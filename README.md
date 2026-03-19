# Cryostat Transport Control

## Description
Developed as part of PhD research to automate cryostat transport measurements.

Includes instrument control, data acquisition, and automation logic.

## Overview
This repo contains Python code for controlling and automating transport measurements in cryostats using PYVISA.

## Features
- Instrument communication
- Voltage/current measurement
- Temperature measurement/control
- Magnetic field measurement/control with quench prevention
- DAQ control
- Live data visualisation

## Requirements
- Python 3.x
- pyvisa
- socket
- nidaqmx

## Setup
1. Install dependencies:
   pip install -r requirements.txt
2. Pick libraries from the Libraries folder as needed (i.e. instruments involved).
3. Pick a template main script from the Scripts folder.
4. Put the script and libraries in the same folder.
5. Modify the main script as needed and update instrument addresses

## Usage
python template_main.py

## Notes
This project requires a VISA backend (e.g. NI-MAX) installed on the system.

