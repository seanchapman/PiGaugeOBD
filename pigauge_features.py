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
# The base cooldown is 2 minutes, with a minute added for every hour driven, up to a maximum of 5 minutes.
class TurboTimer(Feature):
    def __init__(self, bEnabled):
        Feature.__init__(self, bEnabled)
        
        # The time the engine started idling (in seconds)
        self.timeStartedIdling = sys.maxint
        
        self.currentlyIdling = False
        self.idleRpm = 1000
        
        # All in seconds
        self.minCooldown = 90
        self.maxCooldown = 300
        self.cooldownIncrement = 80 # How much to increment the cooldown by per run time multiple
        
        # Engine running time multiple to increase cooldown (in minutes)
        self.runTimeMultiple = 60
        
    # Calculates the optimal cooldown time in seconds
    def calcCooldown(self, sensorList):
        # Get engine run time
        runTime = sensorList["engine_time"].value
        hoursRan = runTime / self.runTimeMultiple
        percentCurrentHour = float(runTime % self.runTimeMultiple) / self.runTimeMultiple
        
        # Calculate
        cooldown = self.minCooldown + (self.cooldownIncrement * hoursRan) + (self.cooldownIncrement * percentCurrentHour)
        if cooldown > self.maxCooldown:
            cooldown = self.maxCooldown
        
        return cooldown
    
    def update(self, sensorList, tInfoBox):
        # Get current RPM
        rpm = sensorList["rpm"].value
        cooldown = self.calcCooldown(sensorList)
    
        # Detect engine entering idle
        if self.currentlyIdling == False and rpm < self.idleRpm:
            self.timeStartedIdling = time.time()
            self.currentlyIdling = True
            
        # Detect engine leaving idle
        if self.currentlyIdling and rpm > self.idleRpm:
            self.timeStartedIdling = sys.maxint
            self.currentlyIdling = False
            
        # Start countdown after 30 seconds of idle
        if self.currentlyIdling:
            idlingTime = time.time() - self.timeStartedIdling
            if idlingTime > 30:
                if idlingTime > cooldown:
                    tInfoBox.AppendText("TurboTimer: SAFE.\n")
                else:
                    timeLeft = int(cooldown - idlingTime)
                    tInfoBox.AppendText("TurboTimer: " + str(timeLeft) + "s\n")
