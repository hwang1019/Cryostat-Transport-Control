# Code for assigning voltage to NI DAQ channels
# Channels range from 650 to 657
# Code for reading voltage output does not work for some reason...

import nidaqmx
import time
import numpy as np

def DAQset(channel, voltage):
    '''
    Setting voltage output from a DAQ channel.

    Args:
        channel: DAQ channel
        voltage: voltage output (unit: V)
    '''

    if channel < 654:
        dev = 'cDAQ1Mod1'
        cha = str(channel - 650)
    else:
        dev = 'cDAQ1Mod2'
        cha = str(channel - 654)

    with nidaqmx.Task() as task:
        task.ao_channels.add_ao_voltage_chan(f"{dev}/ao{cha}")
        task.write(-voltage) # -voltage because the output is opposite to the set value

    return

def DAQsweep(channel, start, end, rate):
    '''
    Voltage output is ramped to setpoint.

    Args:
        channel: DAQ channel
        start: start voltage
        end: end voltage
        rate: voltage ramp rate (unit: V/hr)
    '''

    points = int(round(abs(end - start)/(rate/3600)) + 1)
    volt = np.linspace(start, end, points)
    for v in volt:
        DAQset(channel, v)
        time.sleep(1)
    
    print(f'Voltage output at {channel} is now {end} V.')


# Code for testing
'''
DAQset(650,0)
DAQsweep(channel=650,start=1,end=0,rate=300)
'''