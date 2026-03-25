# Code for SR7265 Signal Recovery Lock-in Amplifier.


import pyvisa
import time
import numpy as np

# list of available lockin sensitivity
SENS = [
    2e-9, 5e-9, 1e-8, 2e-8, 5e-8,
    1e-7, 2e-7, 5e-7,
    1e-6, 2e-6, 5e-6,
    1e-5, 2e-5, 5e-5,
    1e-4, 2e-4, 5e-4,
    1e-3, 2e-3, 5e-3,
    1e-2, 2e-2, 5e-2,
    1e-1, 2e-1, 5e-1,
    1.0
]

def SR7265_config(address):

    '''
    Initialise communication to SR7265.

    Args:
        address: address of the SR7265

    Return:
        The SR7265 object for future communication. 
    '''

    rm = pyvisa.ResourceManager()
    SR7265 = rm.open_resource(address)
    SR7265.read_termination = '\r\n'
    SR7265.write_termination = '\r\n'
    print(SR7265.query('ID'))

    return SR7265

def SR7265_manualrange(inst):

    '''
    Built-in autorange function of the SR7265 lockin is pretty bad. 
    Manually set the range wherever possible.
    '''
    # defining range
    low = 0.3
    high = 0.8

    mag = float(inst.query('MAG.'))
    curr_sens = float(inst.query('SEN.'))    # current sensitivity

    ratio = mag / curr_sens

    # already good → no change
    if low <= ratio <= high:
        return curr_sens, curr_sens, False 

    # choose best range (target ~ 0.6 full scale)
    target = abs(mag) / 0.6
    
    tc = float(inst.query('TC.'))

    for i, s in enumerate(SENS):
        if s >= target:
            if s != curr_sens: # only change sensitivity when necessary
                inst.write(f"SEN {i+1}")   # instrument is 1-based
                return curr_sens, SENS[i], True
            else:
                return curr_sens, curr_sens, False

    inst.write(f"SEN {len(SENS)}")
    return curr_sens, SENS[len(SENS)-1], True

def SR7265_meas_X(inst):

    X = inst.query('X.') # with . it's in floating point mode and return quantities in volts.
    return float(X)

def SR7265_meas_Y(inst):

    Y = inst.query('Y.') # with . it's in floating point mode and return quantities in volts.
    return float(Y)

def SR7265_meas_Mag(inst):

    mag = inst.query('MAG.') # with . it's in floating point mode and return quantities in volts.
    return float(mag)

def SR7265_meas_Phase(inst):

    phase = inst.query('PHA.') # with . it's in floating point mode and return quantities in degrees.
    return float(phase)

def SR7265_meas_sens(inst):

    return float(inst.query('SEN.')) # with . it returns sensitivity in volts and in indices without .

def SR7265_autorange(inst):

    '''
    Built-in autorange function of the SR7265. Not recommended.
    '''
    curr_sens = SR7265_meas_sens(inst)
    curr_mag = SR7265_meas_Mag(inst)
    if curr_mag < 0.3 * curr_sens or curr_mag > 0.9 * 3 * curr_sens:
        inst.write('AS')
    time.sleep(10)

    return 

def SR7265_set_osc(inst,v_target):

    '''
    Setting the oscillation amplitude of the output signal. Signal amplitude is ramped to setpoint at 0.1V/s. 
    '''

    curr_osc = float(inst.query('OA.'))
    step = 0.1 # volt
    num = round(abs(v_target - curr_osc)/step)
    v_set = np.linspace(curr_osc,v_target,num)
    for v in v_set:
        inst.write('OA. {}'.format(str(v)))
        time.sleep(1)

    return 

def SR7265_meas_TC(inst):

    '''
    Return the time constant of the lockin. 
    Useful for waiting time after adjusting sensitivity.
    '''

    tc = float(inst.query('TC.'))

    return tc


# Code for testing
'''
lockin1_address = 'GPIB0::12::INSTR'
lockin2_address = 'GPIB0::11::INSTR'
lockin1 = SR7265_config(lockin1_address) # Measure Vxx
lockin2 = SR7265_config(lockin2_address) # Measure Vxy

print(SR7265_meas_X(lockin1))
#SR7265_set_osc(lockin1, 0.2)
print(SR7265_meas_X(lockin1))

lockin1.close()
lockin2.close()
'''
