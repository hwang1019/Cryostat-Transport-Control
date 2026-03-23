# Class for communicating with LakeShore 370 AC Resistance Bridge
# Many thanks to Dr Johnathan Gough for his contributions.

import socket 
    
class LakeShore: 
    def __init__(self, HOST, PORT, CHANNEL):
        
        """Connect to an lakshore 370 AC bridge and test connection

        Args:
            ip address(str)
            port(float)
            Channel (int)
        """
        self._lakeshore = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._lakeshore.connect((HOST, PORT))
        self.control = CHANNEL
        
    def test(self, BUFF = 50000) :
        
        """test connection to lakshore 370 AC bridge 

        """
        
        CMD = '*IDN?'
        self._lakeshore.send(("{}".format(CMD) + "\n").encode())
        
        msg = self._lakeshore.recv(BUFF)
        
        msg = str(msg)
        msg = msg[2:len(msg)-3]
        print(msg)
        
        
    def read_thermometer(self, BUFF = 50000):
        
        """
        Read current temperature on channel in Kelvin 

        """     
        c = self.control
        CMD = f'READ:DEV:T{c}:TEMP:SIG:TEMP'
        self._lakeshore.send(("{}".format(CMD) + "\n").encode())
        msg = self._lakeshore.recv(BUFF)
        
        msg = str(msg)
        T = float(msg[msg.find('G:TEMP:') + len('G:TEMP:') : msg.find('K\n') - len('K\n') - 1])
        
        return T
            

    def read_heater_range(self, BUFF = 50000):
        
        """
        Read heater range (current supplied to heater) in Amp

        """     
        c = self.control
        CMD = f'READ:DEV:T{c}:TEMP:LOOP:RANGE'
        self._lakeshore.send(("{}".format(CMD) + "\n").encode())
        msg = self._lakeshore.recv(BUFF)
        
        msg = str(msg)
        I = float(msg[msg.find('RANGE:') + len('RANGE:') : msg.find('mA\n') - len('mA\n') - 1])
        
        return I


    def read_heater_setpoint(self, BUFF = 50000):
        
        """
        Read temperature setpoint on channel in Kelvin 

        """     
        c = self.control
        CMD = f'READ:DEV:T{c}:TEMP:LOOP:TSET'
        self._lakeshore.send(("{}".format(CMD) + "\n").encode())
        msg = self._lakeshore.recv(BUFF)
        
        msg = str(msg)
        T = float(msg[msg.find('TSET:') + len('TSET:') : msg.find('K\n') - len('K\n') - 1])
        
        return T
        
    def set_heater_setpoint(self,T, BUFF = 50000):
        
        """
        Set heater set point
        Args:
            T: Temperature set point (unit: K)

        """     
        c = self.control
        CMD = f'SET:DEV:T{c}:TEMP:LOOP:TSET:{T}'
        self._lakeshore.send(("{}".format(CMD) + "\n").encode())
        msg = self._lakeshore.recv(BUFF)
        
        msg = str(msg)

        
        return msg

    def set_heater_range(self,I, BUFF = 50000):
        
        """
        Set heater range (current supplied to the heater)
        Args:
            I: Heater current (unit: mA)  

        """     
        c = self.control
        CMD = f'SET:DEV:T{c}:TEMP:LOOP:RANGE:{I}'
        self._lakeshore.send(("{}".format(CMD) + "\n").encode())
        msg = self._lakeshore.recv(BUFF)
        
        msg = str(msg)

        
        return msg

    def close(self) :
            
        """close connection to lakshore 370 AC bridge 

        """
        self._lakeshore.close() 
            
        

      
'''
# Code for testing

import matplotlib.pyplot as plt
import time
import datetime

def time_now():
    now = datetime.datetime.now()
    t_str_hour = str(now)[11:13]
    t_str_min = str(now)[14:16]
    t_str_sec = str(now)[17:22]
    return ((60*60*float(t_str_hour))+(60*float(t_str_min))+(float(t_str_sec)))/(60*60)

lakeshore = LakeShore(Host, Port, Channel)
lakeshore.test()
lakeshore.close()
IPS = LakeShore(Host, Port, Cha_IPS)
IPS.test()
IPS.close()

c = 0
while True:
    
    lakeshore = LakeShore(Host, Port, Channel)
    T = lakeshore.read_thermometer()
    lakeshore.close()

    IPSTemp = LakeShore(Host, Port, Cha_IPS)
    T_IPS = IPSTemp.read_thermometer()
    IPSTemp.close()

    t = time_now()
    
    plt.scatter(t, T)
    plt.scatter(t, T_IPS)
    plt.pause(0.01)
    
    time.sleep(1)
    c = c + 1

    if c > 10:
        break
  
lakeshore.close()
IPSTemp.close()
'''