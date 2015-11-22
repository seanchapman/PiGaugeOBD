#!/usr/bin/env python
# This file defines features used by PiGaugeOBD, such as turbo timer and rev matcher.

import time;
import sys;

# Feature class is the base class which is used to run feature logic in a loop.
# bEnabled sets wether the feature should be enabled or not
class Feature:
    def __init__(self, bEnabled):
        self.enabled = bEnabled
        
    # Update the feature, passing in the sensor list and info textbox for the feature to read and write to
    def update(self, sensorList, tInfoBox):
        pass

# The manual turbo timer feature lets you know when it is safe to switch off your engine.
class TurboTimer(Feature):
    def __init__(self, bEnabled):
        Feature.__init__(self, bEnabled)
        
        # The time the engine started idling (in seconds)
        self.timeStartedIdling = sys.maxint
        
        self.currentlyIdling = False
        
        self.cooldownPeriod = 120 # seconds
        self.idleRpm = 1000
        
    def update(self, sensorList, tInfoBox):
        # Get current RPM
        rpm = sensorList["rpm"].value
    
        # Detect engine entering idle
        if self.currentlyIdling == False and rpm < self.idleRpm:
            self.timeStartedIdling = time.time()
            self.currentlyIdling = True
            
        # Detect engine leaving idle
        if self.currentlyIdling and rpm > self.idleRpm:
            self.timeStartedIdling = sys.maxint
            self.currentlyIdling = False
            
        # Start countdown after 60 seconds of idle
        if self.currentlyIdling:
            idlingTime = time.time() - self.timeStartedIdling
            if idlingTime > 60:
                if idlingTime > self.cooldownPeriod:
                    tInfoBox.AppendText("TurboTimer: SAFE.\n")
                else:
                    timeLeft = int(self.cooldownPeriod - idlingTime)
                    tInfoBox.AppendText("TurboTimer: " + str(timeLeft) + "s\n")
