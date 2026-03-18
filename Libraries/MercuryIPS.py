# Code for MercuryIPS
# Last update on 17Feb26

import pyvisa
import time
    

def IPS_config(address):

    '''
    Set up communication with MercuryIPS and return the corresponding object for further communication.
    
    Input parameter(s):
    address: address of the IPS, change as necessary.
    '''

    rm = pyvisa.ResourceManager()
    IPS = rm.open_resource(address)
    IPS.read_termination = '\n'
    IPS.write_termination = '\n'
    IPS.baud_rate = 9600
    IPS.data_bits = 8
    IPS.parity = pyvisa.constants.Parity.none
    IPS.stop_bits = pyvisa.constants.StopBits.one
    IPS.timeout = 5000

    try:
        while IPS.bytes_in_buffer > 0:
            IPS.read()
    except:
        pass

    print(IPS.query('*IDN?'))
    time.sleep(1)

    return IPS 

def _read_float(inst, cmd, unit='T'):

    '''
    Isolate and convert floats from IPS response. Await testing.

    Input parameters:
    inst: instrument
    cmd: command sent to IPS
    unit: unit of expected quantity
    '''
    resp = inst.query(cmd)
    return float(resp.split(':')[-1].replace(unit, ''))


def IPS_meas_B(inst, disp = True):

    '''
    Measure current B
    '''

    try:
        while inst.bytes_in_buffer > 0:
            inst.read()
    except:
        pass

    B = inst.query('READ:DEV:GRPZ:PSU:SIG:FLD')
    if disp:
        print(B)
    #B = float(inst.query('READ:DEV:GRPZ:PSU:SIG:FLD')[26:-1])

    return float(B[26:-1])


def IPS_to_zero(inst, rate):

    '''
    Zero the field (equivalent to pressing 'To zero' on the psu panel). Avoid using this function if possible.
    '''

    inst.write(f'SET:DEV:GRPZ:PSU:SIG:RFST:{rate/60}')
    inst.write('SET:DEV:GRPZ:PSU:ACTN:RTOZ')
    print("Magnet is set to go zero.")
    
    return

def IPS_hold(inst):

    inst.write('SET:DEV:GRPZ:PSU:ACTN:HOLD')
    time.sleep(1)
    #print('Magnetic field is now {} T.'.format(str(IPS_meas_B(inst))))

    return

def IPS_to_set(inst):

    inst.write('SET:DEV:GRPZ:PSU:ACTN:RTOS')

    return

def IPS_set_rate(inst, target_rate):

    inst.write('SET:DEV:GRPZ:PSU:SIG:RFST:{}'.format(str(target_rate/60)))  

    return

def IPS_set_B(inst,target_rate,target_B,target_rate_slow = 0.2,B_crit = 10):

    '''
    Set magnet to a field. Useful for field initialisation.

    inst: instrument
    target_rate: sweep rate in T/hr
    target_B: field to sweep to in T
    '''

    time.sleep(0.5)
    slow_rate = False

    curr_B = IPS_meas_B(inst)
    t = abs(target_B - curr_B)/(target_rate)
    print(f'It takes about {t} hours to reach {target_B} T.')

    inst.write('SET:DEV:GRPZ:PSU:SIG:RFST:{}'.format(str(target_rate/60))) # IPS takes unit for sweep rate as T/min
    inst.write('SET:DEV:GRPZ:PSU:SIG:FSET:{}'.format(str(target_B)))
    inst.write('SET:DEV:GRPZ:PSU:ACTN:RTOS')

    while True:
        time.sleep(1)
        B = IPS_meas_B(inst, disp = False)
        print(f'B = {B:.5f} T')

        if abs(B) > B_crit and slow_rate == False:
            IPS_hold(inst)
            IPS_set_rate(inst, target_rate = target_rate_slow)
            IPS_to_set(inst)
            slow_rate = True
            print(f'Rate has slown down to {target_rate_slow}.')
        elif abs(B) < B_crit and slow_rate == True:
            IPS_hold(inst)
            IPS_set_rate(inst, target_rate = target_rate)
            IPS_to_set(inst)
            slow_rate = False
            print(f'Rate has increased to {target_rate}.')



        if abs(B - target_B) <= 0.01:
            break

    inst.write('SET:DEV:GRPZ:PSU:ACTN:HOLD')
    print('Magnetic field is now {} T.'.format(str(B)))
    time.sleep(1)

    return


def IPS_sweep_B(inst,target_rate,target_B):

    '''
    Sweep the magnetic field. Useful when doing measurements while sweeping the field.

    inst: instrument
    target_rate: sweep rate in T/hr
    target_B: field to sweep to in T
    '''

    #set_B = float(inst.query('READ:DEV:GRPZ:PSU:SIG:FSET')[27:-1])
    #set_rate = float(inst.query('READ:DEV:GRPZ:PSU:SIG:RFLD')[27:-5])

    time.sleep(0.5)
    curr_B = IPS_meas_B(inst)
    t = abs(target_B - curr_B)/(target_rate)
    print(f'It takes about {t} hours to reach {target_B} T.')

    inst.write('SET:DEV:GRPZ:PSU:SIG:RFST:{}'.format(str(target_rate/60)))
    inst.write('SET:DEV:GRPZ:PSU:SIG:FSET:{}'.format(str(target_B)))
    inst.write('SET:DEV:GRPZ:PSU:ACTN:RTOS')

    time.sleep(1)

    '''
    while not set_B == target_B:
        inst.query('SET:DEV:GRPZ:PSU:SIG:FSET:{}'.format(str(target_B)))
        time.sleep(2)
        set_B = float(inst.query('READ:DEV:GRPZ:PSU:SIG:FSET')[27:-1])

    while not set_rate == target_rate/60:
        inst.query('SET:DEV:GRPZ:PSU:SIG:RFST:{}'.format(str(target_rate/60)))
        time.sleep(2)
        set_rate = float(inst.query('READ:DEV:GRPZ:PSU:SIG:RFLD')[27:-5])

    inst.query('SET:DEV:GRPZ:PSU:ACTN:RTOS')
    inst.query('SET:DEV:GRPZ:PSU:ACTN:HOLD')
    '''

    return
  



def IPS_heater_ON(inst):

    response = (inst.query('SET:DEV:GRPZ:PSU:SIG:SWHT:ON'))

    return response

def IPS_heater_OFF(inst):

    response = inst.query('SET:DEV:GRPZ:PSU:SIG:SWHT:OFF')

    return response

'''
# Code for testing

IPS_address = 'ASRL10::INSTR'
IPS = IPS_config(IPS_address) 

#set_B = (IPS.query('READ:DEV:GRPZ:PSU:SIG:FSET'))
#set_rate = (IPS.query('READ:DEV:GRPZ:PSU:SIG:RFST'))
#cur_B = IPS_meas_B(IPS)
cur_sta = (IPS.query('READ:DEV:GRPZ:PSU:ACTN'))
cur_I = (IPS.query('READ:DEV:GRPZ:PSU:SIG:CURR'))
#set_rate = IPS_set_rate(IPS,target_rate = 0.2)

c = 0
while c < 100:
    print(cur_I)
    print(cur_sta)
    IPS_meas_B(IPS)
    c = c+1
    time.sleep(0.5)


IPS.close()
'''

