PiGaugeOBD
=====

<pre>Displays extra gauges such as coolant temperature.
Act as a manual turbo timer.
Estimate target RPMs for rev-matching whilst down-shifting.
View interesting statistics.

What is the purpose of this project?
I started this as I was annoyed that my car did not have a coolant temperature or oil temperature gauge, and found that I could achieve this via the OBD2 port.
From there, I realised I could add additional functionality, such as estimating what RPMs I should be at before I down-shift, collecting statistics such as total time driven
and manually timing the turbo before switching the engine off.

What is a "manual turbo timer"?


What is "rev-matching"?


Hardware Required:
1. Raspberry Pi
2. Adafruit PiTFT Touchscreen Display
3. 2A Car Supply / Switch or Micro USB Car Charger
4. ELM327 USB Cable (or Bluetooth adapter, but this is not recommended - see below)
5. Car Mount Holder (*optional)
6. Keyboard (*optional)

What is OBD2?
OBD stands for On-Board Diagnostics, and this standard connector has been mandated in the US since 1996. Now you can think of OBD-II as an on-board computer system that is responsible for monitoring your vehicle’s engine, transmission, and emissions control components. 

Vehicles that comply with the OBD-II standards will have a data connector within about 2 feet of the steering wheel. The OBD connector is officially called a SAE J1962 Diagnostic Connector, but is also known by DLC, OBD Port, or OBD connector. It has positions for 16 pins.

OBD-PiTFT and pyOBD?
pyOBD is an open source OBD-II compliant scantool software written entirely in Python. It is designed to interface with low-cost ELM 32x OBD-II diagnostic interfaces such as ELM-USB. It will basically allow you to talk to your car's ECU, display fault codes, display measured values, read status tests, etc.

I took a fork of pyOBD’s software from their GitHub repository, https://github.com/peterh/pyobd, and used this as the basis for my program.

The program will connect through the OBD-II interface, display the gauges available dependent on the particular vehicle and display realtime engine data on Adafruit's PiTFT touchscreen display in an interactive GUI.

Software Installation
In order to add support for the 2.8" TFT and touchscreen, we'll need to install a new Linux Kernel. Head over to Adafruit and follow their Software Installation, then come on back!

We'll be doing this from a console cable connection, but you can just as easily do it from the direct HDMI/TV console or by SSH'ing in. Whatever gets you to a shell will work!

Note: For the following command line instructions, do not type the '#', that is only to indicate that it is a command to enter. 

Before proceeding, run:
#  sudo apt-get update
#  sudo apt-get upgrade
#  sudo apt-get autoremove

Install these components using the command:
#  sudo apt-get install python-serial
#  sudo apt-get install python-wxgtk2.8 python-wxtools wx2.8-i18n libwxgtk2.8-dev
#  sudo apt-get install git-core

Next, download the OBD-Pi Software direct from GitHub.
(https://github.com/Pbartek/pyobd-pi-TFT.git)

Or using the command:
#  cd ~
#  git clone https://github.com/Pbartek/pyobd-pi-TFT.git

Vehicle Installation
The vehicle installation is quite simple.

1. Insert the USB Bluetooth dongle into the Raspberry Pi along with the SD card.

2. Connect your PiTFT display to the Raspberry Pi.

3. Insert the OBD-II Bluetooth adapter into the SAE J196216 (OBD Port) connector.

4. Install your 2A Car Supply / Switch or Micro USB Car Charger.

5. Finally, turn your key to the ON position.

6. Enter your login credentials and run:
#  startx

7. Launch BlueZ, the Bluetooth stack for Linux. Pair + Trust your ELM327 Bluetooth Adapter and Connect To: SPP Dev. You should see the Notification "Serial port connected to /dev/rfcomm0"

Note: Click the Bluetooth icon, bottom right (Desktop) to configure your device. Right click on your Bluetooth device to bring up Connect To: SPP Dev.

8. Open up Terminal and run:
#  cd pyobd-pi-TFT
#  sudo su
#  python obd_gui.py

Note: Run, # python obd_gui_square.py to use the rounded rectangle gauge.

Tap the display to cycle through the gauges!

To exit the program just press Control and C or Alt and Esc.
Enjoy and drive safe!</pre>
