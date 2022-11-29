from kivy.uix.boxlayout import BoxLayout
from popups import ModbusPopup, ScanPopup, DataGraphPopup, HistGraphPopup
from pyModbusTCP.client import ModbusClient
from kivy.core.window import Window
from threading import Thread
from time import sleep
from datetime import datetime
import random
from timeseriesgraph import TimeSeriesGraph
from bdhandler import BDHandler
from kivy_garden.graph import LinePlot
from kivy.clock import Clock

class MainWidget(BoxLayout):
    """
    Widget principal da aplicação
    """
    _updateThread = None
    _updateWidgets = True
    _tags={}
    _max_points = 20
    Window.size = (800, 600)
    
    def __init__(self, **kwargs):
        """
        Construtor do widget principal
        """
        #sempre utilizar construtor da classe base para evitar posteriores problemas
        super().__init__()
        self._scan_time = kwargs.get('scan_time')
        self._serverIP = kwargs.get('server_ip')
        self._serverPort = kwargs.get('server_port')
        self._modbusPopup = ModbusPopup(self._serverIP, self._serverPort)
        self._scanPopup = ScanPopup(self._scan_time)
        self._modbusClient = ModbusClient(host=self._serverIP, port=self._serverPort)
        # dicionário que possui medições atuais ("measure")
        self._meas = {}             
        self._meas['timestamp'] = None
        self._meas['values'] = {}
        self._maxt = 0

        
        for key,value in kwargs.get('modbus_inf').items():
            if key == 'nivel':
                #rgb com opacidade
                plot_color = (0, 0, 1, 1) 
            else :
                plot_color = (random.random(), random.random(), random.random(), 1)
            self._tags[key] = {'addr' : value[0],'mult' : value[1],'tipo' : value[2],'unit' : value[3],'color' : plot_color}
        self._graph = DataGraphPopup(self._max_points, self._tags['nivel']['color'])
        self._hgraph = HistGraphPopup(tags=self._tags)
        self._db = BDHandler(kwargs.get('db_path'), self._tags)
    
    def startDataRead (self, ip, port):
        """
        Metodo utilizado para a configuração do IP e porta do servidor MODBUS e inicializar uma thread para a leitura dos dados e atualização da interface gráfica
        """
        self._serverIP = ip
        self._serverPort = port
        self._modbusClient.host = self._serverIP
        self._modbusClient.port = self._serverPort
        try:
            #configura o cursor como espera enquanto estiver tentando realizar conexão
            Window.set_system_cursor("wait") 
            self._modbusClient.open()
            #se acessar normalmente, voltamos o cursor padrão
            Window.set_system_cursor("arrow") 
            if self._modbusClient.is_open():
                self._updateThread = Thread(target=self.updater)
                self._updateThread.start()
                #atualiza a imagem com status de conexão
                self.ids.img_con.source = 'imgs/conectado.png' 
                #fecha janela do modbusPopup
                self._modbusPopup.dismiss() 
            else :
                self._modbusPopup.setinfo("Falha na conexão com o servidor")
        except Exception as e:
            print ("Erro: a", e.args)
        
    def updater(self):
        """
        Método que invoca as rotinas de leitura dos dados, atualização da interface e inserção dos dados no Banco de dados
        """
        try :
            #com estes procedimentos não alteramos o funcionamento da thread principal; não perdemos responsividade; não deixamos de atualizar de atualizar a interface gráfica
            while self._updateWidgets:
                #leitura dos dados MODBUS
                self.readData() 
                #atualiza a interface
                self.updateGUI() 
                #insere os dados no BD
                self._db.insertData(self._meas) 
                #converte [ms] em [s]
                sleep(self._scan_time/1000) 
        except Exception as e:
            self._modbusClient.close()
            print ("Erro: b", e.args)
    
    def readData (self):
        """
        Metodo para a leitura dos dados por meio do protocolo MODBUS
        """
        #horário corrente do SO
        self._meas['timestamp'] = datetime.now() 
        for key,value in self._tags.items():
            if(value['tipo']==0):
                self._meas['values'][key] = self._modbusClient.read_coils(value['addr'], 1)[0]
            elif(value['tipo']==1):
                self._meas['values'][key] = self._modbusClient.read_holding_registers(value['addr'], 1)[0]/value['mult']
            elif(value['tipo']==2):
                self._meas['values'][key] = self._modbusClient.read_input_registers(value['addr'], 1)[0]/value['mult']
            elif(value['tipo']==3):
                self._meas['values'][key] = self.ids['freq_des_in'].text
        

    def updateGUI(self):
        """
        Metodo para atualiza~ao da interface grafica a partir dos dados lidos
        """
        self.ids['volume'].text = str(self._meas['values']['nivel']) + ' L'
        
        #Atualização dos labels informativos
        for key, value in self._tags.items():
            if(key != 'solenoide' and key != 'estado_mot' and key != 'auto_control' and key != 'nivel' and key != 'nivel_h' and key != 'nivel_l'):
                if(self._tags[key]['tipo'] == 0):
                    self.ids[key].text = str(self._meas['values'][key])
                else:
                    self.ids[key].text = str(self._meas['values'][key]) + ' ' + str(self._tags[key]['unit'])            
        
        #Atualização do nível do tanque; alteramos apenas o label com base em uma regra de três
        self.ids.lb_tanque.size = (self.ids.lb_tanque.size[0], self._meas['values']['nivel']/1000*self.ids.tanque.size[1])

        #Atualização do gráfico
        self._graph.ids.graph.updateGraph((self._meas['timestamp'], self._meas['values']['nivel']), 0)

        #Garante execução pela thread primária o mais rápido possível
        Clock.schedule_once(self._startValvula)
        Clock.schedule_once(self._startMotor)
        Clock.schedule_once(self._startControleMotor)
        Clock.schedule_once(self._startSensor)

    def stopRefresh(self):
        """
        Método auxiliar para interromper a atualização do método updater após fechamento da GUI
        """
        self._updateWidgets = False

    def getDataDB(self,**kwargs):
        """
        Método que coleta as informações da interface fornecidas pelo usuário e requisita a busca no BD
        """
        try:
            init_t = self.parseDTString(self._hgraph.ids.txt_init_time.text)
            final_t = self.parseDTString(self._hgraph.ids.txt_final_time.text)
            cols=[]
            self._maxt = 0
            
            #navegar dentro de todos os widgets filhos do boxlayout sensores
            for sensor in self._hgraph.ids.sensores.children: 
                if sensor.ids.checkbox.active:
                    if(sensor.id == 'vz_entrada'):
                        if(20 >= self._maxt):
                            self._maxt = 20
                    elif (sensor.id == 'temp_estator'):
                        if(60 >= self._maxt):
                            self._maxt = 60
                    elif (sensor.id == 'freq_mot'):
                        if(60 >= self._maxt):
                            self._maxt = 100
                    elif (sensor.id =='tensao'):
                        if(300 >= self._maxt):
                            self._maxt = 300
                    elif (sensor.id == 'rotacao'):
                        if(2000 >= self._maxt):
                            self._maxt = 2000
                    elif (sensor.id == 'pot_entrada'):
                        if(2000 >= self._maxt):
                            self._maxt = 2000
                    elif (sensor.id == 'corrente'):
                        if(50 >= self._maxt):
                            self._maxt = 50

                    cols.append(sensor.id)
            
            if init_t is None or final_t is None or len(cols)==0:
                return
            
            
            cols.append('timestamp')
            
            dados = self._db.selectData(cols, init_t, final_t)

            if dados is None or len (dados['timestamp']) == 0:
                return
            
            #limpa ambiente do gráfico para plotar somente o desejado
            self._hgraph.ids.graph.clearPlots() 

            for key,value in dados.items():
                if key == 'timestamp':
                    continue
                p = LinePlot(line_width = 1.5, color = self._tags[key]['color'])
                p.points = [(x, value[x]) for x in range (0, len (value))]
                #adicionamos todas as linhas desejadas pelo usuário
                self._hgraph.ids.graph.add_plot(p) 
            #len(...) é o número de medidas
            self._hgraph.ids.graph.xmax = len(dados[cols[0]]) 
            self._hgraph.ids.graph.ymax = self._maxt
            self._hgraph.ids.graph.y_ticks_major = self._maxt/10
            #atualiza as legendas do eixo x de forma a mostrar o timestamp e não o número das amostras
            self._hgraph.ids.graph.update_x_labels([datetime.strptime(x, "%Y-%m-%d %H:%M:%S.%f") for x in dados ['timestamp']]) 
        except Exception as e :
            print ( "Erro: c", e.args)

    def parseDTString(self, datetime_str) :
        """
        Método que converte a string inserida pelo usuário para o formato utilizado na busca dos dados no BD
        """
        try :
            d = datetime.strptime(datetime_str, '%d/%m/%Y %H:%M:%S')
            return d.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e :
            print ( "Erro: d", e.args)

    def _alteraValvula(self):
        """
        Método que altera o estado da válvula solenóide
        """
        if(self._meas['values']['solenoide'] == 1):
            self._meas['values']['solenoide'] = 0
            self._modbusClient.write_single_coil(self._tags['solenoide']['addr'], self._meas['values']['solenoide'])
        else:
            self._meas['values']['solenoide'] = 1
            self._modbusClient.write_single_coil(self._tags['solenoide']['addr'], self._meas['values']['solenoide'])
        self._startValvula
    
    def _startValvula(self,dt):
        """
        Método que faz a atualização gráfica do estado da válvula solenoide
        """
        if(self._meas['values']['solenoide'] == 0):
            self.ids.solenoide_bt.background_normal = 'imgs/valve_off.png'
            self.ids.solenoide_bt.background_down = 'imgs/valve_off.png'
        else:
            self.ids.solenoide_bt.background_normal = 'imgs/valve_on.png'
            self.ids.solenoide_bt.background_down = 'imgs/valve_on.png'
    
    def _alteraMotor(self):
        """
        Método que altera estado do motor
        """
        if(self._meas['values']['estado_mot'] == 1):
            self._meas['values']['estado_mot'] = 0
            self._modbusClient.write_single_coil(self._tags['estado_mot']['addr'], self._meas['values']['estado_mot'])
        else:
            self._meas['values']['estado_mot'] = 1
            self._modbusClient.write_single_coil(self._tags['estado_mot']['addr'], self._meas['values']['estado_mot'])
        self._startMotor

    def _startMotor(self,dt):
        """
        Método que faz atualização gráfica dos botão de ON/OFF e do estado do motor 
        """
        if(self._meas['values']['estado_mot'] == 0):
            self.ids.estado_motor.source = 'imgs/motor_off.png'
            self.ids.motor_bt.background_normal = 'imgs/bt_off.png'
            self.ids.motor_bt.background_down = 'imgs/bt_off.png'
        else:
            self.ids.estado_motor.source = 'imgs/motor_on.png'
            self.ids.motor_bt.background_normal = 'imgs/bt_on.png'
            self.ids.motor_bt.background_down = 'imgs/bt_on.png'
        
    def _alteraControleMotor(self):
        """
        Método que altera o estado de auto controle do motor
        """
        if(self._meas['values']['auto_control'] == 1):
            self._meas['values']['auto_control'] = 0
            self._modbusClient.write_single_coil(self._tags['auto_control']['addr'], self._meas['values']['auto_control'])
        else:
            self._meas['values']['auto_control'] = 1
            self._modbusClient.write_single_coil(self._tags['auto_control']['addr'], self._meas['values']['auto_control'])
        self._startControleMotor

    def _startControleMotor(self,dt):
        """
        Método que faz atualização gráfica do botão AUTO CTRL
        """
        if(self._meas['values']['auto_control'] == 0):
            self.ids.motor_automatico_bt.background_normal = 'imgs/bt_off.png'
            self.ids.motor_automatico_bt.background_down = 'imgs/bt_off.png'
        else:
            self.ids.motor_automatico_bt.background_normal = 'imgs/bt_on.png'
            self.ids.motor_automatico_bt.background_down = 'imgs/bt_on.png'
    
    def _alteraFreq(self):
        """
        Método que altera a frequência do motor
        """
        if self.ids.freq_des_in.text:
            if int(self.ids.freq_des_in.text) <= 60 and int(self.ids.freq_des_in.text) > 0:
                self._meas['values']['freq_des'] = int(self.ids.freq_des_in.text)
                self._modbusClient.write_single_register(self._tags['freq_des']['addr'], self._meas['values']['freq_des'])
    
    def _alteraTempoPartida(self):
        """
        Método que altera o tempo de partida do motor
        """
        if self.ids.t_partida.text:
            if int(self.ids.t_partida.text) > 0:
                self._meas['values']['t_part'] = int(self.ids.t_partida.text)*self._tags['t_part']['mult']
                self._modbusClient.write_single_register(self._tags['t_part']['addr'], self._meas['values']['t_part'])

    def _startSensor(self,dt):
        """
        Método que faz atualização gráfica dos sensores de nível do tanque 
        """
        if self._meas['values']['nivel_l'] == 0:
            self.ids.sensor_baixo.source = 'imgs/sensor_off_d.png'
            self.ids.sensor_alto.source = 'imgs/sensor_off_e.png'
        elif self._meas['values']['nivel_l'] == 1 and self._meas['values']['nivel_h'] == 0:
            self.ids.sensor_baixo.source = 'imgs/sensor_on_d.png'
            self.ids.sensor_alto.source = 'imgs/sensor_off_e.png'
        elif self._meas['values']['nivel_h'] == 1:
            self.ids.sensor_baixo.source = 'imgs/sensor_on_d.png'
            self.ids.sensor_alto.source = 'imgs/sensor_on_e.png'
