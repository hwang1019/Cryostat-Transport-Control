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
lockin1_address = 'ph'
IPS_address = 'ph'
Host = 'ph'
Port = 'ph'
Channel = 'ph'

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
Vsg_start_down = 0
Vsg_end_down = -3
Vsg_start_up = -3
Vsg_end_up = 0
Vsg_rate_down = 100 # V/hr
Vsg_rate_up = 100 # V/hr
Vsg_chan = 650
points_down = int(round(abs(Vsg_end_down - Vsg_start_down)/(Vsg_rate_down/3600)) + 1)
points_up = int(round(abs(Vsg_end_up - Vsg_start_up)/(Vsg_rate_up/3600)) + 1)
Vsg_down = np.linspace(Vsg_start_down, Vsg_end_down, points_down)
Vsg_up = np.linspace(Vsg_start_up, Vsg_end_up, points_up)

Vtg_start = 0
Vtg_end = -3
Vtg_step = -0.1
Vtg = np.arange(Vtg_start,Vtg_end + Vtg_step,Vtg_step)
Vtg_chan = 651

B_start = 0
B_end = 0
B_step = 0.1
B = np.arange(B_start,B_end + B_step,B_step)
B_rate = 1

Vsg_map = {
    "up": Vsg_up,
    "down": Vsg_down,
}

# Initialise and zero all DAQ channels being used
DAQset(Vsg_chan,0)
DAQset(Vtg_chan,0)

# Program paused for users to build their circuits
answer = input("Continue? [Y/N]: ")

if answer.strip().upper() != "Y":
    print("Stopping script.")
    IPS.close()
    lockin1.close()
    raise SystemExit

print("Continuing...")

counter = 1
while counter <=1:
    
    for b in B:

        IPS_set_B(IPS,target_rate = B_rate, target_B = b) # ramp to starting field
        time.sleep(10)

        png_filename_1 = f"Vg_sweep_Vxx_{date_str}_{time_str}_{b}T_{counter}.png"
        save_path_1 = os.path.join(data_folder, png_filename_1)

        plt.ion()  # turn on interactive mode

        # Plot 1 : Ixx over Vsg
        fig1, ax1 = plt.subplots()
        ax1.set_xlabel("Vsg (V)")
        ax1.set_ylabel("Ixx (A)")
        ax1.set_title('Ixx vs Vsg')
        
        # Measurements
        for vtg in Vtg:

            # 1st sweep
            sweep = 'down'

            DAQset(channel = Vtg_chan, voltage = vtg) 

            txt_filename = f"Vsg_sweep_{date_str}_{time_str}_{sweep}_{vtg}V_{b}T_{counter}.txt"
            txt_path = os.path.join(data_folder, txt_filename)

            # New line per vtg 
            line1, = ax1.plot([], [], 'ro')

            # Initialise data to be recorded
            Vsg_data = []
            Ixx_data = [] 
            Temp_data = []  
            Phase1_data = []

            for vsg in Vsg_map[sweep]:

                DAQset(channel = Vsg_chan, voltage = vsg)

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

                Ixx_data.append(Ixx_meas)
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
                    file.write(f"# Columns: Vsg (V), Ixx (A), Phase1 (degree), Temperature (K) \n")
                    file.write(f"{'Vsg (V)':>15} {'Ixx (A)':>15} {'Phase1 (degree)':>15} {'Temperature (K)':>15}\n")

                    # Data rows
                    for i in range(len(Vsg_data)):
                        file.write(f"{Vsg_data[i]:15.6f} {Ixx_data[i]:15.6f} {Phase1_data[i]:15.6f} {Temp_data[i]:15.6f}\n")

            # Save the figure
            fig1.savefig(save_path_1, dpi=300)


            # 2nd sweep
            sweep = 'up'

            txt_filename = f"Vsg_sweep_{date_str}_{time_str}_{sweep}_{vtg}V_{b}T_{counter}.txt"
            txt_path = os.path.join(data_folder, txt_filename)

            # New line per vtg (label lets you add a legend)
            line1, = ax1.plot([], [], 'bo')

            # Initialise data to be recorded
            Vsg_data = []
            Ixx_data = [] 
            Temp_data = []  
            Phase1_data = []

            for vsg in Vsg_map[sweep]:

                DAQset(channel = Vsg_chan, voltage = vsg)

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

                Ixx_data.append(Ixx_meas)
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
                    file.write(f"# Columns: Vsg (V), Ixx (A), Phase1 (degree), Temperature (K) \n")
                    file.write(f"{'Vsg (V)':>15} {'Ixx (A)':>15} {'Phase1 (degree)':>15} {'Temperature (K)':>15}\n")

                    # Data rows
                    for i in range(len(Vsg_data)):
                        file.write(f"{Vsg_data[i]:15.6f} {Ixx_data[i]:15.6f} {Phase1_data[i]:15.6f} {Temp_data[i]:15.6f}\n")

            # Save the figure
            fig1.savefig(save_path_1, dpi=300)

        plt.ioff()
        IPS_hold(IPS)
        DAQsweep(Vsg_chan, start = np.max(Vsg_map[sweep]), end = 0, rate = 100)
        DAQsweep(Vtg_chan, start = np.max(Vtg), end = 0, rate = 100)

    counter = counter + 1 


IPS_set_B(IPS,target_rate = 1,target_B = 0) # zero the magnet at the end

IPS.close()
lockin1.close()
