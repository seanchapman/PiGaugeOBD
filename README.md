PiGaugeOBD
=====

<pre>Displays extra colour-coded gauges, such as coolant temperature.
Act as a manual turbo timer.
Estimate target RPMs for rev-matching whilst down-shifting.
View interesting statistics.

What is the purpose of this project?
I started this as my car did not have a coolant temperature or oil temperature gauge as standard, and found that I could achieve this myself by accessing the OBD-II port.
From there, I realised I could add additional functionality, such as estimating what RPMs I should be at before I down-shift, collecting statistics such as total time driven
and manually timing the turbo before switching the engine off.

What is a "manual turbo timer"?
It is a function that counts down when you are parked up, to let you know when enough time has passed to cool the turbo down before switching off the engine.

What is "rev-matching"?
Rev-matching is used when switching gears. When switching up, the RPM will drop, when switching down, the RPM will increase. If your RPM doesn't match the expected new RPM when you release the clutch
after switching gears, the engine will jolt the clutch either faster or slower, to match the new RPM. So the Pi can tell you what the estimated RPMs are if you downshift or upshift, which allows you 
to accurately match them with the accelerator, giving you a smoother driving experience.


Forked from Pbartek/pyobd-pi-TFT
The original author gave me a great start at the code, showing basic text gauges on a Raspberry Pi TFT display, but I wanted to add more functionality, hence the reason for this fork.
I have refactored a large majority of the original code to add additional features such as analogue gauges, colour coding safe limits and more.
The original repository is available at https://github.com/Pbartek/pyobd-pi-TFT


Hardware Required:
1. Raspberry Pi
2. Adafruit PiTFT Touchscreen Display
3. 2A Car Supply / Switch or Micro USB Car Charger
4. ELM327 USB Cable (or Bluetooth adapter, but this is not recommended - see below)
5. UPS Pico (optional - to prevent SD card corruption when the Pi suddenly loses power)
5. Car Mount Holder (optional)
6. Keyboard (optional)

What is OBD-II?
OBD stands for On-Board Diagnostics, and this standard connector has been mandated in the US since 1996. Now you can think of OBD-II as an on-board computer system that is responsible for monitoring your vehicle’s engine, transmission, and emissions control components. 

Vehicles that comply with the OBD-II standards will have a data connector within about 2 feet of the steering wheel. The OBD connector is officially called a SAE J1962 Diagnostic Connector, but is also known by DLC, OBD Port, or OBD connector. It has positions for 16 pins.

The program will connect through the OBD-II interface, display the gauges available dependent on the particular vehicle and display realtime engine data on Adafruit's PiTFT touchscreen display in an interactive GUI.

Software Installation
In order to add support for the 2.8" TFT and touchscreen, we'll need to install a new Linux Kernel. Head over to Adafruit and follow their Software Installation, then come on back! You will also want to install the UPS Pico software if you are using that.

It is preferrable to disable automatic screen dimming, to minimise distractions whilst driving! You may also want to have the Python script execute as soon as the Pi is switched on.

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

Next, download the software direct from GitHub.
(https://github.com/seanchapman/PiGaugeOBD.git)

Or using the command:
#  cd ~
#  git clone https://github.com/seanchapman/PiGaugeOBD.git

Vehicle Installation
The vehicle installation is quite simple.

1. Insert the USB ELM327 cable into the Raspberry Pi along with the SD card. 

2a. Connect your UPS Pico to the Raspberry Pi.

2b. Connect your PiTFT display to the Raspberry Pi (or on top of the UPS Pico).

3. Insert the other end of the ELM327 cable into your OBD-II port. (the SAE J196216 (OBD Port) connector)

4. Finally, turn your key to the ON position, to power the Pi.

5. Enter your login credentials and run:
#  startx

6. Open up Terminal and run:
#  cd PiGaugeOBD
#  sudo su
#  python obd_gui.py

Tap the display to cycle through the gauges!

To exit the program just press Control and C or Alt and Esc.
Enjoy and drive safe!</pre>
