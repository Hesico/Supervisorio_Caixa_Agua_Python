from pyModbusTCP.server import DataBank, ModbusServer
from Tanque import Tanque
from time import sleep
from random import randrange
class CLP():
    """
    class CLP - Server - ModBus TCP

    attribute: tick : CLP cycle time


    """

    __tick = 0.1

    def __init__(self,host,port):
        """
        class constructor
        param: host: server IP address
        param: port : server port

        """
        self.__server = ModbusServer(host=host, port=port, no_block=True)
        self.__db = DataBank()
        self.__tank = Tanque(self.__tick)
        
        self.__db.set_words(799,(self.__tank.motor.getOpFrequencia()/10,))  
        self.__db.set_words(798,(self.__tank.motor.getTStart()*10,))       
        self.__db.set_bits(811,(self.__tank.getSolenoide(),))

    def Connection(self):
        """
        starts server
        listen client

        """
        self.__server.start()
        print('Simulador Online... Ctrl+C para parar')
        while True:
            try:
                self.DoService()
                sleep(self.__tick)
            except Exception as e:
                print("Error: ",e.args)
    
    def DoService(self):
        """
        serve client
        simulate tank
        set tank/motor parmas thru registers
        random noise added when reading data 

        """
        motorState = self.__db.get_bits(800)[0]
        drainState = self.__db.get_bits(801)[0]
        ac = self.__db.get_bits(1000)[0]
        frequency = self.__db.get_words(799)[0]
        t_partida = self.__db.get_words(798)[0]/10
        
        self.__tank.TankSimulation(frequency, t_partida,motorState,drainState)

        self.__db.set_words(801, (self.__tank.motor.getTensao()+ randrange(-3,4),))
        self.__db.set_words(802, (self.__tank.motor.getTorque(),))
        self.__db.set_words(800,(max(self.__tank.motor.getOpFrequencia()+ randrange(-3,4),0),))
        self.__db.set_words(803, (max(self.__tank.motor.getRotacao() + randrange(-3,4),0),))
        self.__db.set_words(804,(max(self.__tank.motor.getInPower()+ randrange(-3,4),0),))
        self.__db.set_words(805, (max(self.__tank.motor.getCorrente() + 10*randrange(-2,2),0),))
        self.__db.set_words(806,(max(self.__tank.motor.getTemperature()+ randrange(-2,3),0),))
        self.__db.set_words(807,(max(self.__tank.getVazao()+ 10*randrange(-1,1),0),))
        self.__db.set_words(808,(max(self.__tank.getNivel()+ 10*randrange(-3,4),0),))       
        self.__db.set_bits(811,(self.__tank.getSolenoide(),))
        high_l = self.__tank.getHighLevel()
        low_level = self.__tank.getLowLevel()
        self.__db.set_bits(809,(high_l,))
        self.__db.set_bits(810,(low_level,))
        if high_l:
            self.__db.set_bits(800,(False,))
        if ac and not low_level:
            self.__db.set_bits(800,(True,))
        self.__db.set_bits(811,(self.__tank.getSolenoide(),))        