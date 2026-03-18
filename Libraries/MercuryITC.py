# Code for Mercury ITC

UID_VTI = 'placeholder' 
UID_sample = 'placeholder' # use sample temp sensor & heater where possible

import pyvisa
import time

def ITC_configure(address):
    '''
    Connect to ITC and create ITC instance.
    '''

    rm = pyvisa.ResourceManager()
    ITC_adddress = address
    ITC = rm.open_resource(ITC_adddress)
    ITC.read_termination = '\n'
    ITC.write_termination = '\n'
    print(ITC.query('*IDN?'))

    return ITC 


def ITC_read_temp(inst,UID):
    '''
    Read ITC temperature
    '''
    temp = inst.query('READ:DEV:{}:TEMP:SIG:TEMP'.format(UID))[30:-1]

    return float(temp)

def ITC_set_temp(inst,UID,t_set):
    '''
    Set ITC temperature.
    '''
    inst.query('SET:DEV:{}:TEMP:LOOP:TSET:{}'.format(UID,str(t_set)))

    return

def ITC_read_set_temp(inst,UID):

    t_set = inst.query('READ:DEV:{}:TEMP:LOOP:TSET'.format(UID))[31:-1]
               
    return float(t_set)
