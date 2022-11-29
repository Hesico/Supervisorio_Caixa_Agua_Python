from Motor import Motor
import math

class Tanque:
    """
    class tank

    """
    def __init__(self, tick,iState=False,maxLevel=1000,lowLevel=100,highLevel=950):
        """
        class constructor
        dictionary to initialize motor params

        """
        self.__tick = tick
        self.__level = 0.0
        self.__solenoide = iState
        self.__maxLevel = maxLevel
        self.__lowLevel = lowLevel
        self.__highLevel = highLevel
        self.__motorDic = {"state":False,"tensao":220,"eff":0.8,"polo":4,"costheta":0.8,"horsepower":3,"slipNom":0.05,\
            "load":0.5,"frequencia" : 60,"opFrequencia" : 60, "TempAmbiente" : 24, "tal": 100, "tstart":3}
        self.motor = Motor(**self.__motorDic)

    """
    return data to registers
    """
    def getVazao(self):
        return int(self.__vin*100)
    def getNivel(self):
        return int(self.__level*10)   
    def getLowLevel(self):
        return self.__level >= self.__lowLevel
    def getHighLevel(self):
        return self.__level >= self.__highLevel
    def getSolenoide(self):
        return self.__solenoide

    def getTick(self):
        return self.__tick

    def CalculaVazao(self):
            self.__vin = 10*(self.motor.getRotacao()/(self.motor.getWsincrona()))

    def setSolenoide(self, state):
        self.__solenoide = state

        if self.__vin == 0 and self.__level == 0:
            self.__solenoide = False

    def CalculaNivel(self):
        vout = 10*self.__level/self.__maxLevel

        if not self.__solenoide:
            vout = 0

        self.__level += (self.__vin - vout)*self.__tick    


    def TankSimulation(self, frequencia, t_partida,motorState, drainState):

        """
        set motor/tank params upon user frequency and valve state input 
        """
        self.motor.setTStart(t_partida)
        freq = self.motor.partida(motorState, frequencia, self.__tick)
        self.motor.TorqueNom()
        self.motor.setOpFrequencia(freq)
        self.motor.wSincronaOperacao()
        self.motor.TorqueVazio()
        self.motor.Torque()
        self.motor.Rotacao()
        self.motor.OutPower()
        self.motor.InPower()
        self.motor.CalculaCorrente()
        self.motor.Temperature(self.__tick)

        self.CalculaVazao()
        self.setSolenoide(drainState)
        self.CalculaNivel()
        self.getHighLevel()
        self.getLowLevel()        