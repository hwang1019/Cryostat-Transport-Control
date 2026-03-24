# Code for MercuryIPS
# Leave sufficient time with e.g. time.sleep(1) between successive queries, especially when the magnet psu is connected to the pc via serial (e.g. RS-232) communication 
# and over long cables

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
    Measure current magnetic field and return it.

    Args:
        inst: object corresponds to the magnet
        disp: print the magnetic field or not (print by default)
    '''
    # Make sure the computer always 'reads' something in the IPS buffer
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
    Args:
        inst: object cprresponds to the magnet
        rate: sweep rate of the magnetic field (unit: T/h)
    '''

    inst.write(f'SET:DEV:GRPZ:PSU:SIG:RFST:{rate/60}') # divide by 60 is very important since IPS accepts sweep rate in T/min
    inst.write('SET:DEV:GRPZ:PSU:ACTN:RTOZ')
    print("Magnet is set to go zero.")
    
    return

def IPS_hold(inst):

    '''
    Put the magnet on hold. This is equivalent to pressing the 'hold' button on the psu panel.
    '''

    inst.write('SET:DEV:GRPZ:PSU:ACTN:HOLD')
    time.sleep(1) # Essential if doing multiple queries and especially if the magnet is connected over long cable via serial communication.
    #print('Magnetic field is now {} T.'.format(str(IPS_meas_B(inst))))

    return

def IPS_to_set(inst):

    '''
    Ask the magnet to go to the setpoint. This is equivalent to pressing the 'to set' button on the psu panel.
    '''

    inst.write('SET:DEV:GRPZ:PSU:ACTN:RTOS')

    return

def IPS_set_rate(inst, target_rate):

    '''
    Set the sweep rate for magnetic field.

    Args:
        inst: object corresponding to the magnet
        target_rate: field sweep rate in T/hr
    '''

    inst.write('SET:DEV:GRPZ:PSU:SIG:RFST:{}'.format(str(target_rate/60)))  

    return

def IPS_set_B(inst,target_rate,target_B,target_rate_slow = 0.2,B_crit = 10):

    '''
    Set magnet to a field. Useful for field initialisation.
    Note this function does not come with quench-prevention mechanism.

    inst: instrument
    target_rate: sweep rate in T/hr
    target_B: field to sweep to in T
    target_rate_slow: the slower sweep rate when field goes beyond a critical value
    B_crit: Critical field value beyond which the sweep rate slows down to provent magnet quench
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

        # Slow down sweep rate when field goes beyond the critical field value
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

    # Following code is for making sure the field setpoint and sweep rate are set correctly. 
    # They are commented out because successive queries via RS-232 can cause reading errors.
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

    '''
    Turn on the switch heater remotely. It is recommended to do it locally.
    '''

    response = (inst.query('SET:DEV:GRPZ:PSU:SIG:SWHT:ON'))
    print('Switch heater is turned ON. Stabilising ...')

    time.sleep(5 * 60) # wait 5 minutes for heater to stabilise
    print('Switch heater is turned on and stabilised.')

    return response

def IPS_heater_OFF(inst):

    response = inst.query('SET:DEV:GRPZ:PSU:SIG:SWHT:OFF')
    print('Switch heater is turned OFF.')

    return response


# The following code is for quick testing. Remember to comment them out before running the main.py
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

