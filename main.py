from kivy.app import App
from mainwidget import MainWidget
from kivy.lang.builder import Builder


class MainApp(App):
    """
    Aplicativo básico kivy
    """
    def build (self):
        """
        Metodo que gera o aplicativo com no widget principal
        """    
        self._widget = MainWidget(scan_time = 1000, server_ip = '127.0.0.1', server_port = 502,
        modbus_inf = {
        't_part'        : [798,  10  ,  1,   's'],
        'freq_des'      : [799,  1,     3,  'Hz'],
        'estado_mot'    : [800,  None,  0,  None],
        'freq_mot'      : [800,  10,    2,  'Hz'],
        'tensao'        : [801,  1,     2,   'V'],
        'solenoide'     : [801,  None,  0,  None],
        'rotacao'       : [803,  1,     2, 'RPM'],
        'pot_entrada'   : [804,  10,    2,   'W'],
        'corrente'      : [805,  100,   2,'A (RMS)'],
        'temp_estator'  : [806,  10,    2,  '°C'],
        'vz_entrada'    : [807,  100,   2, 'L/s'],
        'nivel'         : [808,  10,    2,   'L'],
        'nivel_h'       : [809,  None,  0,  None],
        'nivel_l'       : [810,  None,  0,  None],
        'auto_control'  : [1000, None,  0,  None]
        },
        db_path="db\\scada.db"
        )
        return self._widget
    
    def on_stop(self):
        """
        Método executado quando a aplicação é fechada
        """
        self._widget.stopRefresh()
            
    
if __name__=='__main__':

   #faz ajustes para devida exibição de caracteres especiais especificando codificação de leitura
   Builder.load_string(open("mainwidget.kv", encoding='utf-8').read(), rulesonly=True)
   Builder.load_string(open("popups.kv", encoding='utf-8').read(), rulesonly=True)
   MainApp().run()