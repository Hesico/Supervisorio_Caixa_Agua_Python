from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy_garden.graph import LinePlot
from kivy.uix.boxlayout import BoxLayout

class ModbusPopup(Popup):
    """
    Popup para cofiguração do protocolo MODBUS
    """
    _info_lb = None
    def __init__(self, server_ip, server_port, **kwargs):
        """
        Construtor da classe ModbusPopup
        """
        super().__init__(**kwargs)
        self.ids.txt_ip.text = str(server_ip)
        self.ids.txt_porta.text = str(server_port)

    
    def setinfo(self, message):
        #informa ao usuário uma menssagem de status do programa
        self._info_lb = Label(text=message) 
        #adiciona mensagem do Label no "layout"
        self.ids.layout.add_widget(self._info_lb) 

    def clearinfo (self) :
        if self._info_lb is not None :
            #remove mensagem
            self.ids.layout.remove_widget(self._info_lb) 

class ScanPopup(Popup):
    """
    Popup para configuração do tempo de varredura
    """
    def __init__(self, scantime, **kwargs):
        """
        Construtor da classe ScanPopup
        """
        #sempre utilizar construtor da classe base para evitar posteriores problemas
        super().__init__(**kwargs)
        self.ids.txt_st.text = str(scantime)

class DataGraphPopup(Popup):
    def __init__(self, xmax, plot_color, **kwargs):
        super().__init__(**kwargs)
        #define a linha do gráfico
        self.plot = LinePlot(line_width = 1.5, color = plot_color) 
        #adiciona a linha ao gráfico definido em dataGraphPopus
        self.ids.graph.add_plot(self.plot) 
        #número máximo de amostras no eixo x
        self.ids.graph.xmax = xmax 

class LabeledCheckBoxDataGraph(BoxLayout):
    pass

class HistGraphPopup (Popup):
    def __init__(self,**kwargs):
        super().__init__()
        for key, value in kwargs.get('tags').items():
            if(key != 't_part'  and key != 'freq_des' and key != 'solenoide' and key != 'estado_mot' and key != 'auto_control' and key != 'nivel' and key != 'nivel_h' and key != 'nivel_l'):  
                cb = LabeledCheckBoxHistGraph()
                if(key == 'vz_entrada'):
                    cb.ids.label.text = 'Vazão'
                elif (key == 'temp_estator'):
                    cb.ids.label.text = 'Temperatura'
                elif (key == 'freq_mot'):
                    cb.ids.label.text = 'Frequência'
                elif (key =='tensao'):
                    cb.ids.label.text = 'Tensão'
                elif (key == 'rotacao'):
                    cb.ids.label.text = 'Rotação'
                elif (key == 'pot_entrada'):
                    cb.ids.label.text = 'Potência'
                elif (key == 'corrente'):
                    cb.ids.label.text = 'Corrente'
                cb.ids.label.color = value['color']
                cb.id = key
                #incluímos no boxlayout de sensores
                self.ids.sensores.add_widget(cb)

class LabeledCheckBoxHistGraph(BoxLayout):
    pass