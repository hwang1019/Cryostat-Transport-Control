# This code is for measurements involving sweeping/stepping voltage output from NI DAQ 
# Preferbaly for split gate devices

import numpy as np
import time
import matplotlib.pyplot as plt
import os
import datetime
from SR7265 import * 
from DAQ import * 
from MercuryIPS import *
from LakeShore import LakeShore

# Replace placeholders with actual instrument address
lockin1_address = 'lockin1_address'
IPS_address = 'IPS_address'
Host = 'ITC_host'
Port = 00000
Channel = 0

# Initialise communication with the instruments
lockin1 = SR7265_config(lockin1_address) # Measure Vxx
IPS = IPS_config(IPS_address)
lakeshore = LakeShore(Host, Port, Channel)
lakeshore.test()
lakeshore.close()

# Defining the sensitivity of pre-amp
Sens1 = 1e-6 # when current pre-amp has a sensitivity of 1uA/V

# Setting up paths to data folder
date_str = datetime.datetime.now().strftime("%d%m%y")
time_str = datetime.datetime.now().strftime("%H%M%S")
script_dir = os.path.dirname(os.path.abspath(__file__)) # Path to the folder where your main.py lives
data_folder = os.path.join(script_dir, date_str) # Path to your manually created 'data' folder
os.makedirs(data_folder, exist_ok=True) # Make sure data folder exists
fig_path_1 = os.path.join(data_folder, f"Vsg_sweep_Ixx_{date_str}_{time_str}.png")

# Setting sweep parameters
repeats = 1 # number of repeats
Vsg_start_down = -1.2
Vsg_end_down = -1.9
Vsg_start_up = Vsg_end_down
Vsg_end_up = Vsg_start_down
Vsg_rate_down = 20 # V/hr
Vsg_rate_up = 20 # V/hr
Vsg_chan = 650
points_down = int(round(abs(Vsg_end_down - Vsg_start_down)/(Vsg_rate_down/3600)) + 1)
points_up = int(round(abs(Vsg_end_up - Vsg_start_up)/(Vsg_rate_up/3600)) + 1)
Vsg_down = np.linspace(Vsg_start_down, Vsg_end_down, points_down)
Vsg_up = np.linspace(Vsg_start_up, Vsg_end_up, points_up)


Vtg_start = -2
Vtg_end = -2.025
Vtg_step = -0.025
Vtg = Vtg_start + np.arange(int(round((Vtg_end - Vtg_start) / Vtg_step)) + 1) * Vtg_step
Vtg_chan = 652
print('Vtg array is',Vtg)

Vdc_start = 0
Vdc_end = 3
Vdc_step = 0.025
Vdc = Vdc_start + np.arange(int(round((Vdc_end - Vdc_start) / Vdc_step)) + 1) * Vdc_step
Vdc_chan = 653
print('Vdc array is',Vdc)

B_start = 0
B_end = 0
B_step = 0.05
B = B_start + np.arange(int(round((B_end - B_start) / B_step)) + 1) * B_step
B_rate = 1
print('B array is',B)

Vsg_map = {
    "up": Vsg_up,
    "down": Vsg_down,
}

# Initialise and zero all DAQ channels being used
#DAQsweep(Vsg_chan, start = -1.02, end = 0, rate = 100)
#DAQsweep(Vtg_chan, start = 0, end = 0, rate = 100)
#DAQsweep(Vdc_chan, start = 1.375, end = 0, rate = 100)
IPS_set_B(IPS,target_rate = B_rate, target_B = 0)
DAQset(Vsg_chan,0)
DAQset(Vtg_chan,0)
DAQset(Vdc_chan,0)

# Program paused for users to build their circuits
t = (abs(Vsg_start_down - Vsg_end_down)/Vsg_rate_down + abs(Vsg_start_up - Vsg_end_up)/Vsg_rate_up) * len(Vtg) * len(Vdc) * len(B)
t_sweep = abs((np.max(Vtg) - np.min(Vtg)))/100 + abs((np.max(B)) - np.min(B))/1
print(f'This measurement takes about {(t + t_sweep):.3f} hours.')
answer = input("Continue? [Y/N]: ")

if answer.strip().upper() != "Y":
    print("Stopping script.")
    IPS.close()
    lockin1.close()
    raise SystemExit

print("Continuing...")

DAQsweep(Vsg_chan, start = 0, end = Vsg_start_down, rate = 100)
DAQsweep(Vtg_chan, start = 0, end = Vtg_start, rate = 100)
DAQsweep(Vdc_chan, start = 0, end = Vdc_start, rate = 100)
IPS_set_B(IPS,target_rate = B_rate, target_B = B_start)
time.sleep(10)

def Vsg_sweep(sweep, ar = False):
        
    '''
    Measuring current through the device while sweeping the split gate voltage. 
    Plot the graph and save the data.

    Args:
        sweep: upsweep or downsweep; type:string
        ar: turn autorange on or off; type: Boolean
    '''

    global vsg

    txt_filename = f"Vsg_sweep_{date_str}_{time_str}_{sweep}_Vtg={vtg:.3f}V_Vdc={vdc:.3f}V_B={b:.3f}T_{counter}.txt"
    txt_path = os.path.join(data_folder, txt_filename)

    # New line per vtg
    if sweep == 'up':
        line1, = ax1.plot([], [], 'o', c='r', markersize=3, ls='')
    if sweep == 'down':
        line1, = ax1.plot([], [], 'o', c='b', markersize=3, ls='')

    # Initialise data to be recorded
    Vsg_data = []
    Ixx_data = [] 
    Temp_data = []  
    Phase1_data = []

    for vsg in Vsg_map[sweep]:

        DAQset(channel = Vsg_chan, voltage = vsg)
    
        if ar:
            if len(Vsg_data) % 20 == 0:
                curr_sens_1, target_sens_1, mr1 = SR7265_manualrange(lockin1)
                if mr1 == True:
                    time.sleep(10 * SR7265_meas_TC(lockin1))
                    print(f'Current lockin_1 sensitivity was {curr_sens_1} and is now set to {target_sens_1}.')
        
        Ixx_meas = SR7265_meas_X(lockin1) * Sens1
        Phase1_meas = SR7265_meas_Phase(lockin1)
        Vsg_meas = vsg

        lakeshore = LakeShore(Host, Port, Channel)
        T_samp_meas = lakeshore.read_thermometer()
        lakeshore.close()

        Ixx_data.append(Ixx_meas * 1e+6)
        Phase1_data.append(Phase1_meas)
        Temp_data.append(T_samp_meas)
        Vsg_data.append(Vsg_meas)

        line1.set_data(Vsg_data, Ixx_data)
        ax1.relim()
        ax1.autoscale_view()  # auto-adjust axes  
        fig1.canvas.draw()
        fig1.canvas.flush_events()       

        plt.pause(1)  # process GUI events + delay; handles Ctrl+C properly on Windows

        with open(txt_path, mode='w') as file:

            file.write(f"# Measurement taken on {date_str} at {time_str}\n")
            file.write(f"# Columns: Vsg (V), Ixx (uA), Phase1 (degree), Temperature (K) \n")
            file.write(f"{'Vsg (V)':>15} {'Ixx (uA)':>15} {'Phase1 (degree)':>15} {'Temperature (K)':>15}\n")

            # Data rows
            for i in range(len(Vsg_data)):
                file.write(f"{Vsg_data[i]:15.6f} {Ixx_data[i]:15.8f} {Phase1_data[i]:15.6f} {Temp_data[i]:15.6f}\n")

    fig1.canvas.draw()
    fig1.savefig(fig_path_1, dpi=300)
    print(f"Figure saved: {fig_path_1}")
    return vsg

counter = 1
vsg = None

plt.ion()  # turn on interactive mode

# Plot 1 : Ixx over Vsg
fig1, ax1 = plt.subplots()
ax1.set_xlabel("Vsg (V)")
ax1.set_ylabel("Ixx (uA)")
ax1.set_title('Ixx vs Vsg')

try:
    while counter <= repeats:

        for b in B:

            print('B is set to: ',b,'T')
            IPS_set_B(IPS,target_rate = B_rate, target_B = b) # ramp to desired field
            if len(B) > 1:
                print('Stabilising B...')
                time.sleep(10)

            for vtg in Vtg:

                print('Vtg is set to: ',vtg,'V')
                DAQset(Vtg_chan, vtg)
                if len(Vtg) > 1:
                    print('Stabilising Vtg...')
                    time.sleep(10)

                for vdc in Vdc:

                    print('Vdc is set to: ',vdc,'V')
                    DAQset(Vdc_chan, vdc)
                    if len(Vdc) > 1:
                        print('Stabilising Vdc...')
                        time.sleep(10)

                    vsg_final = Vsg_sweep(sweep = 'down')
                    vsg_final = Vsg_sweep(sweep = 'up')

                DAQsweep(Vdc_chan, start = vdc, end = Vdc_start, rate = 100)

            DAQsweep(Vtg_chan, start = vtg, end = Vtg_start, rate = 100)

        IPS_set_B(IPS,target_rate = B_rate,target_B = B_start)

        counter = counter + 1

except KeyboardInterrupt:
    print(f"\nInterrupted at Vsg={vsg:.3f}V, Vtg={vtg:.3f}V, Vdc={vdc:.3f}V, B={b:.3f}T, repeat={counter}")
    answer = input("Zero all outputs? [Y/N]: ")
    if answer.strip().upper() == "Y":
        plt.ioff()
        fig1.savefig(fig_path_1, dpi=300)
        print(f"Figure saved: {fig_path_1}")
        IPS_set_B(IPS, target_rate=1, target_B=0)
        DAQsweep(Vdc_chan, start=vdc, end=0, rate=100)
        DAQsweep(Vtg_chan, start=vtg, end=0, rate=100)
        DAQsweep(Vsg_chan, start=vsg, end=0, rate=100)
    IPS.close()
    lockin1.close()
    raise SystemExit 

plt.ioff()
IPS_set_B(IPS,target_rate = 1,target_B = 0)
DAQsweep(Vdc_chan, start = Vdc_start, end = 0, rate = 100)
DAQsweep(Vtg_chan, start = Vtg_start, end = 0, rate = 100)
DAQsweep(Vsg_chan, start = vsg_final, end = 0, rate = 100)
IPS.close()
lockin1.close()
