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
lockin1_address = 'placeholder'
IPS_address = 'placeholder'
Host = 'placeholder'
Port = 'placeholder'
Channel = 'placeholder'

# Initialise communication with the instruments
lockin1 = SR7265_config(lockin1_address) # Measure Vxx
IPS = IPS_config(IPS_address)
lakeshore = LakeShore(Host, Port, Channel)
lakeshore.test()
lakeshore.close()

# Defining the sensitivity of pre-amp
Sens1 = 1e-6 # assuming current pre-amp has a sensitivity of 1uA/V

# Setting up paths to data folder
date_str = datetime.datetime.now().strftime("%d%m%y")
time_str = datetime.datetime.now().strftime("%H%M%S")
script_dir = os.path.dirname(os.path.abspath(__file__)) # Path to the folder where your main.py lives
data_folder = os.path.join(script_dir, date_str) # Path to your manually created 'data' folder
os.makedirs(data_folder, exist_ok=True) # Make sure data folder exists

# Setting sweep parameters
Vsg_start_down = -1.2
Vsg_end_down = -2
Vsg_start_up = Vsg_end_down
Vsg_end_up = Vsg_start_down
Vsg_rate_down = 15 # V/hr
Vsg_rate_up = 15 # V/hr
Vsg_chan = 650
points_down = int(round(abs(Vsg_end_down - Vsg_start_down)/(Vsg_rate_down/3600)) + 1)
points_up = int(round(abs(Vsg_end_up - Vsg_start_up)/(Vsg_rate_up/3600)) + 1)
Vsg_down = np.linspace(Vsg_start_down, Vsg_end_down, points_down)
Vsg_up = np.linspace(Vsg_start_up, Vsg_end_up, points_up)
print('Vsg_down array is:',Vsg_down)
print('Vsg_up array is:',Vsg_up)

Vtg_start = -1.825
Vtg_end = -2.025
Vtg_step = -0.025
Vtg = np.arange(Vtg_start,Vtg_end + Vtg_step,Vtg_step)
Vtg_chan = 652
print('Vtg array is',Vtg)

Vdc_start = 0
Vdc_end = 0
Vdc_step = -0.1
Vdc = np.arange(Vdc_start,Vdc_end + Vdc_step,Vdc_step)
Vdc_chan = 653
print('Vdc array is',Vdc)

B_start = 0
B_end = 2
B_step = 0.05
B = np.arange(B_start,B_end + B_step,B_step)
B_rate = 1
print('B array is',B)

Vsg_map = {
    "up": Vsg_up,
    "down": Vsg_down,
}

# Initialise and zero all DAQ channels being used
DAQsweep(Vsg_chan, start = -1.475, end = 0, rate = 100)
DAQsweep(Vtg_chan, start = -1.825, end = 0, rate = 100)
IPS_set_B(IPS,target_rate = B_rate, target_B = 0)
#DAQset(Vsg_chan,0)
#DAQset(Vtg_chan,0)
#DAQset(Vdc_chan,0)

# Program paused for users to build their circuits
answer = input("Continue? [Y/N]: ")

if answer.strip().upper() != "Y":
    print("Stopping script.")
    IPS.close()
    lockin1.close()
    raise SystemExit

print("Continuing...")

#DAQsweep(Vsg_chan, start = 0, end = Vsg_start_down, rate = 100)
#DAQsweep(Vtg_chan, start = 0, end = Vtg_start, rate = 100)
#DAQsweep(Vdc_chan, start = 0, end = Vdc_start, rate = 100)

def Vsg_sweep(sweep):
        
    '''
    Measuring current through the device while sweeping the split gate voltage. Plot the graph and save the data.

    Args:
        sweep: upsweep or downsweep; type:string
    '''

    txt_filename = f"Vsg_sweep_{date_str}_{time_str}_{sweep}_{vtg:.3f}V_{vdc:.1f}mV_{b:.3f}T_{counter}.txt"
    txt_path = os.path.join(data_folder, txt_filename)

    # New line per vtg 
    if sweep == 'up':
        line1, = ax1.plot([], [], 'r-')
    if sweep == 'down':
        line1, = ax1.plot([], [], 'b-')

    # Initialise data to be recorded
    Vsg_data = []
    Ixx_data = [] 
    Temp_data = []  
    Phase1_data = []

    for vsg in Vsg_map[sweep]:

        DAQset(channel = Vsg_chan, voltage = vsg)
        '''
        if len(Vsg_data) % 20 == 0:
            curr_sens_1, target_sens_1, mr1 = SR7265_manualrange(lockin1)
            if mr1 == True:
                time.sleep(10 * SR7265_meas_TC(lockin1))
                print(f'Current lockin_1 sensitivity was {curr_sens_1} and is now set to {target_sens_1}.')
        '''
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

        line1.set_data(Vsg_data,Ixx_data)
        ax1.relim()
        ax1.autoscale_view()  # auto-adjust axes  
        fig1.canvas.draw()
        fig1.canvas.flush_events()       

        plt.pause(0.1)  # short pause to allow GUI event loop to run
        time.sleep(1)
        plt.show(block=False)

        with open(txt_path, mode='w') as file:

            file.write(f"# Measurement taken on {date_str} at {time_str}\n")
            file.write(f"# Columns: Vsg (V), Ixx (uA), Phase1 (degree), Temperature (K) \n")
            file.write(f"{'Vsg (V)':>15} {'Ixx (uA)':>15} {'Phase1 (degree)':>15} {'Temperature (K)':>15}\n")

            # Data rows
            for i in range(len(Vsg_data)):
                file.write(f"{Vsg_data[i]:15.6f} {Ixx_data[i]:15.8f} {Phase1_data[i]:15.6f} {Temp_data[i]:15.6f}\n")

    return vsg

counter = 1

plt.ion()  # turn on interactive mode

# Plot 1 : Ixx over Vsg
fig1, ax1 = plt.subplots()
ax1.set_xlabel("Vsg (V)")
ax1.set_ylabel("Ixx (uA)")
ax1.set_title('Ixx vs Vsg')

while counter <= 1: 

    for b in B:
        
        print('B is set to: ',b,'T')
        IPS_set_B(IPS,target_rate = B_rate, target_B = b) # ramp to starting field
        time.sleep(10)

        for vtg in Vtg:
            
            print('Vtg is set to: ',vtg,'V')
            DAQset(Vtg_chan, vtg)
            time.sleep(10)

            for vdc in Vdc:

                png_filename_1 = f"Vsg_sweep_Ixx_{date_str}_{time_str}_{b:.3f}T_{vtg:.3f}Vtg_{vdc:.1f}Vdc_{counter}.png"
                save_path_1 = os.path.join(data_folder, png_filename_1)

                print('Vdc is set to: ',vdc,'V')
                DAQset(Vdc_chan, vdc)
                #time.sleep(10)

                vsg_final = Vsg_sweep(sweep = 'down')
                vsg_final = Vsg_sweep(sweep = 'up')

            DAQsweep(Vdc_chan, start = vdc, end = Vdc_start, rate = 100)

        DAQsweep(Vtg_chan, start = vtg, end = Vtg_start, rate = 100)

    IPS_set_B(IPS,target_rate = 1,target_B = B_start)

    counter = counter + 1

# Save the figure
fig1.savefig(save_path_1, dpi=300)
plt.ioff()

IPS_set_B(IPS,target_rate = 1,target_B = 0) 
DAQsweep(Vdc_chan, start = Vdc_start, end = 0, rate = 100)
DAQsweep(Vtg_chan, start = Vtg_start, end = 0, rate = 100)
DAQsweep(Vsg_chan, start = vsg_final, end = 0, rate = 100)
IPS.close()
lockin1.close()
