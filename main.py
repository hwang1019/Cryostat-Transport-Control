# B sweep example program
# Last update on 19Feb26

#import pyvisa
#import numpy as np
import time
import matplotlib.pyplot as plt
import os
import datetime
from MercuryITC import *
from MercuryIPS import *
from SR7265 import * 
from LakeShore import LakeShore

# Replace placeholders with actual instrument address
IPS_address = 'ASRLXX::INSTR'
lockin1_address = 'GPIB0::XX::INSTR'
lockin2_address = 'GPIB0::XX::INSTR'
Host = 'place holder'
Port = 'place holder'
Channel = 'place holder' 
Cha_IPS = 'place holder' # for reading magnet temperature

lockin1 = SR7265_config(lockin1_address) # Measure Vxx
lockin2 = SR7265_config(lockin2_address) # Measure Vxy
IPS = IPS_config(IPS_address)
lakeshore = LakeShore(Host, Port, Channel)
lakeshore.test()
lakeshore.close()
IPS_temp = LakeShore(Host, Port, Cha_IPS)
IPS_temp.test()
IPS_temp.close()

IPS_hold(IPS)
time.sleep(10)

'''
#Use during emergency
IPS_to_zero(IPS,1)
time.sleep(10)
IPS.close()
'''

# Defining the gain of pre-amp
Gain1 = 100
Gain2 = 100

# Setting up paths to data folder
date_str = datetime.datetime.now().strftime("%d%m%y")
time_str = datetime.datetime.now().strftime("%H%M%S")
script_dir = os.path.dirname(os.path.abspath(__file__)) # Path to the folder where your main.py lives
data_folder = os.path.join(script_dir, date_str) # Path to your manually created 'data' folder
os.makedirs(data_folder, exist_ok=True) # Make sure data folder exists

# Setting sweep parameters
B_start_down = 0
B_end_down = -11.5
B_start_up = -11.5
B_end_up = 0
B_rate = 1 # T/hr
B_rate_slow = 0.2 #T/hr
Mag_T_crit = 4 #K
B_sample = 0.002 # Field between consecutive measurement. Unit: Tesla
t_wait = 3600/(B_rate/B_sample) # Time between consecutive measurement. Unit: second
t_wait_slow = 3600/(B_rate_slow/B_sample)
overheat = False

B_start_map = {
    "up": B_start_up,
    "down": B_start_down,
}

B_end_map = {
    "up": B_end_up,
    "down": B_end_down,
}

counter = 1
while counter <=1:
    # 1st sweep
    sweep = 'down'
    margin = 0.01

    txt_filename = f"B_sweep_{date_str}_{time_str}_{sweep}_{counter}.txt"
    txt_path = os.path.join(data_folder, txt_filename)
    png_filename_1 = f"B_sweep_Vxx_{date_str}_{time_str}_{sweep}_{counter}.png"
    save_path_1 = os.path.join(data_folder, png_filename_1)
    png_filename_2 = f"B_sweep_Vxy_{date_str}_{time_str}_{sweep}_{counter}.png"
    save_path_2 = os.path.join(data_folder, png_filename_2)

    IPS_set_B(IPS,target_rate = B_rate, target_B = B_start_map[sweep]) # ramp to starting field
    time.sleep(10)

    plt.ion()  # turn on interactive mode

    # Plot 1 : Vxx over B
    fig1, ax1 = plt.subplots()
    line1, = ax1.plot([], [], 'ro',label = 'Vxx')   
    ax1.set_xlabel("B (T)")
    ax1.set_ylabel("Vxx (V)")
    ax1.set_title('Vxx vs B')
    #ax1.set_xlim(B_low, B_high)

    # Plot 2 : Vxy over B
    fig2, ax2 = plt.subplots()
    line2, = ax2.plot([], [], 'bo',label = 'Vxy')   
    ax2.set_xlabel("B (T)")
    ax2.set_ylabel("Vxy (V)")
    ax2.set_title('Vxy vs B')
    #ax1.set_xlim(B_low, B_high)
        
    # Initialise data to be recorded
    B_data = []
    Vxx_data = [] 
    Vxy_data = []
    Temp_data = []
    Mag_T_data = []   
    Phase1_data = []
    Phase2_data = []

    # Measurements
    target_B = B_end_map[sweep]
    IPS_sweep_B(IPS,target_rate = B_rate,target_B = target_B) # sweep to end field
    rate_slow = False
    t = t_wait
    while True:

        B_meas = IPS_meas_B(IPS)

        if abs(B_meas) > 10 and rate_slow == False:
            IPS_hold(IPS)
            IPS_set_rate(IPS, target_rate = B_rate_slow)
            IPS_to_set(IPS)
            t = t_wait_slow
            rate_slow = True
        elif abs(B_meas) < 10 and rate_slow == True:
            IPS_hold(IPS)
            IPS_set_rate(IPS, target_rate = B_rate)
            IPS_to_set(IPS)
            t = t_wait
            rate_slow = False

        if abs(B_meas - target_B) <= margin:
            break

        IPSTemp = LakeShore(Host, Port, Cha_IPS)
        Mag_T_meas = IPSTemp.read_thermometer()
        IPSTemp.close()    

        if Mag_T_meas >= Mag_T_crit:
            IPS_hold(IPS)
            time.sleep(20*60) # wait for 20 min and see if magnet temperature stabilises
            IPSTemp = LakeShore(Host, Port, Cha_IPS)
            Mag_T_meas = IPSTemp.read_thermometer()
            IPSTemp.close() 
            if Mag_T_meas >= Mag_T_crit:
                overheat = True
            else:
                overheat = False


        if len(B_data) % 3 == 0:
            curr_sens_1, target_sens_1, mr1 = SR7265_manualrange(lockin1)
            if mr1 == True:
                IPS_hold(IPS)
                print(f'Current lockin_1 sensitivity was {curr_sens_1} and is now set to {target_sens_1}.')

            curr_sens_2, target_sens_2, mr2 = SR7265_manualrange(lockin2)
            if mr2 == True:
                IPS_hold(IPS)
                print(f'Current lockin_2 sensitivity was {curr_sens_2} and is now set to {target_sens_2}.')

        Vxx_meas = SR7265_meas_X(lockin1)/Gain1
        Vxy_meas = SR7265_meas_X(lockin2)/Gain2 
        Phase1_meas = SR7265_meas_Phase(lockin1)
        Phase2_meas = SR7265_meas_Phase(lockin2)

        lakeshore = LakeShore(Host, Port, Channel)
        T_samp_meas = lakeshore.read_thermometer()
        lakeshore.close()
        #Temp_meas = ITC_read_temp(ITC,UID = UID_VTI)

        if mr1 == True or mr2 == True and overheat == False:
            IPS_to_set(IPS)

        B_data.append(B_meas)
        Vxx_data.append(Vxx_meas)
        Vxy_data.append(Vxy_meas)
        Phase1_data.append(Phase1_meas)
        Phase2_data.append(Phase2_meas)
        Temp_data.append(T_samp_meas)
        Mag_T_data.append(Mag_T_meas)

        line1.set_data(B_data,Vxx_data)
        ax1.relim()
        ax1.autoscale_view()  # auto-adjust axes  
        fig1.canvas.draw()
        fig1.canvas.flush_events()   

        line2.set_data(B_data,Vxy_data)
        ax2.relim()
        ax2.autoscale_view()  # auto-adjust axes  
        fig2.canvas.draw()
        fig2.canvas.flush_events()      

        plt.pause(0.1)  # short pause to allow GUI event loop to run
        time.sleep(t) 


        # Save the figure
        fig1.savefig(save_path_1, dpi=300)
        fig2.savefig(save_path_2, dpi=300)

        plt.show(block=False)

        with open(txt_path, mode='w') as file:

            file.write(f"# Measurement taken on {date_str} at {time_str}\n")
            file.write(f"# Columns: B (T), Vxx (V), Vxy (V), Phase (degree), Temperature (K) \n")
            file.write(f"{'B (T)':>15} {'Vxx (V)':>15} {'Vxy (V)':>15} {'Phase1 (degree)':>15} {'Phase2 (degree)':>15} {'Temperature (K)':>15} {'MagnetTemp (K)':>15}\n")

            # Data rows
            for i in range(len(B_data)):
                file.write(f"{B_data[i]:15.6f} {Vxx_data[i]:15.6f} {Vxy_data[i]:15.6f} {Phase1_data[i]:15.6f} {Phase2_data[i]:15.6f} {Temp_data[i]:15.6f} {Mag_T_data[i]:15.6f}\n")


        if overheat == True:
            IPS_to_zero(IPS, 0.1)
            print('Magnet overheating. Going back to zero now.')
            break
        

    plt.ioff()
    IPS_hold(IPS)

    if overheat == True:
        IPS_to_zero(IPS,0.1)
        print('Magnet overheating, going back to zero now.')
        break

    # 2nd sweep
    sweep = 'up'

    txt_filename = f"B_sweep_{date_str}_{time_str}_{sweep}_{counter}.txt"
    txt_path = os.path.join(data_folder, txt_filename)
    png_filename_1 = f"B_sweep_Vxx_{date_str}_{time_str}_{sweep}_{counter}.png"
    save_path_1 = os.path.join(data_folder, png_filename_1)
    png_filename_2 = f"B_sweep_Vxy_{date_str}_{time_str}_{sweep}_{counter}.png"
    save_path_2 = os.path.join(data_folder, png_filename_2)

    IPS_set_B(IPS,target_rate = B_rate_slow, target_B = B_start_map[sweep]) # ramp to starting field

    plt.ion()  # turn on interactive mode

    # Plot 1 : Vxx over B
    fig1, ax1 = plt.subplots()
    line1, = ax1.plot([], [], 'ro',label = 'Vxx')   
    ax1.set_xlabel("B (T)")
    ax1.set_ylabel("Vxx (V)")
    ax1.set_title('Vxx vs B')

    # Plot 2 : Vxy over B
    fig2, ax2 = plt.subplots()
    line2, = ax2.plot([], [], 'bo',label = 'Vxy')   
    ax2.set_xlabel("B (T)")
    ax2.set_ylabel("Vxy (V)")
    ax2.set_title('Vxy vs B')

    # Initialise data to be recorded
    B_data = []
    Vxx_data = []
    Vxy_data = []
    Temp_data = []
    Mag_T_data = []
    Phase1_data = []
    Phase2_data = []

    # Measurements
    target_B = B_end_map[sweep]
    IPS_sweep_B(IPS,target_rate = B_rate,target_B = B_end_map[sweep])
    rate_slow = False
    t = t_wait
    while True:

        B_meas = IPS_meas_B(IPS)

        if abs(B_meas) > 10 and rate_slow == False:
            IPS_hold(IPS)
            IPS_set_rate(IPS, target_rate = B_rate_slow)
            IPS_to_set(IPS)
            t = t_wait_slow
            rate_slow = True
        elif abs(B_meas) < 10 and rate_slow == True:
            IPS_hold(IPS)
            IPS_set_rate(IPS, target_rate = B_rate)
            IPS_to_set(IPS)
            t = t_wait
            rate_slow = False

        if abs(B_meas - target_B) <= margin:
            break

        IPSTemp = LakeShore(Host, Port, Cha_IPS)
        Mag_T_meas = IPSTemp.read_thermometer()
        IPSTemp.close() 

        if Mag_T_meas >= Mag_T_crit:
            IPS_hold(IPS)
            time.sleep(20*60) # wait for 20 min and see if magnet temperature stabilises
            IPSTemp = LakeShore(Host, Port, Cha_IPS)
            Mag_T_meas = IPSTemp.read_thermometer()
            IPSTemp.close() 
            if Mag_T_meas >= Mag_T_crit:
                overheat = True
            else:
                overheat = False


        if len(B_data) % 3 == 0:
            curr_sens_1, target_sens_1, mr1 = SR7265_manualrange(lockin1)
            if mr1 == True:
                IPS_hold(IPS)
                print(f'Current lockin_1 sensitivity is {curr_sens_1} and will be set to {target_sens_1}.')
                time.sleep(10)

            curr_sens_2, target_sens_2, mr2 = SR7265_manualrange(lockin2)
            if mr2 == True:
                IPS_hold(IPS)
                print(f'Current lockin_2 sensitivity is {curr_sens_2} and will be set to {target_sens_2}.')
                time.sleep(10)

        Vxx_meas = SR7265_meas_X(lockin1)/Gain1
        Vxy_meas = SR7265_meas_X(lockin2)/Gain2 
        Phase1_meas = SR7265_meas_Phase(lockin1)
        Phase2_meas = SR7265_meas_Phase(lockin2)
        lakeshore = LakeShore(Host, Port, Channel)
        T_samp_meas = lakeshore.read_thermometer()
        lakeshore.close()
        #Temp_meas = ITC_read_temp(ITC,UID = UID_VTI)

        if mr1 == True or mr2 == True and overheat == False:
            IPS_to_set(IPS)

        B_data.append(B_meas)
        Vxx_data.append(Vxx_meas)
        Vxy_data.append(Vxy_meas)
        Phase1_data.append(Phase1_meas)
        Phase2_data.append(Phase2_meas)
        Temp_data.append(T_samp_meas)
        Mag_T_data.append(Mag_T_meas)

        line1.set_data(B_data,Vxx_data)
        ax1.relim()
        ax1.autoscale_view()  # auto-adjust axes  
        fig1.canvas.draw()
        fig1.canvas.flush_events()   

        line2.set_data(B_data,Vxy_data)
        ax2.relim()
        ax2.autoscale_view()  # auto-adjust axes  
        fig2.canvas.draw()
        fig2.canvas.flush_events()      

        plt.pause(0.1)  # short pause to allow GUI event loop to run
        time.sleep(t) 

        # Save the figure
        fig1.savefig(save_path_1, dpi=300)
        fig2.savefig(save_path_2, dpi=300)

        plt.show(block=False)

        with open(txt_path, mode='w') as file:
            # Optional metadata
            file.write(f"# Measurement taken on {date_str} at {time_str}\n")
            file.write(f"# Columns: B (T), Vxx (V), Vxy (V), Phase (degree), Temperature (K) \n")
            file.write(f"{'B (T)':>15} {'Vxx (V)':>15} {'Vxy (V)':>15} {'Phase1 (degree)':>15} {'Phase2 (degree)':>15} {'Temperature (K)':>15} {'MagnetTemp (K)':>15}\n")

            # Data rows
            for i in range(len(B_data)):
                file.write(f"{B_data[i]:15.6f} {Vxx_data[i]:15.6f} {Vxy_data[i]:15.6f} {Phase1_data[i]:15.6f} {Phase2_data[i]:15.6f} {Temp_data[i]:15.6f} {Mag_T_data[i]:15.6f}\n")

        if overheat == True:
            IPS_to_zero(IPS, 0.1)
            print('Magnet overheating. Going back to zero now.')
            break

    plt.ioff()
    IPS_hold(IPS)

    if overheat == True:
        IPS_to_zero(IPS,0.1)
        print('Magnet overheating, going back to zero now.')
        break

    counter = counter + 1 


IPS_set_B(IPS,target_rate = 1,target_B = 0) # zero the magnet at the end

IPS.close()
lockin1.close()
lockin2.close()
#lakeshore.close()
IPS_temp.close()
