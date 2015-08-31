#!/usr/bin/env python
###########################################################################
# obd_sensors.py
#
# Copyright 2004 Donour Sizemore (donour@uchicago.edu)
# Copyright 2009 Secons Ltd. (www.obdtester.com)
#
# This file is part of pyOBD.
#
# pyOBD is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# pyOBD is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyOBD; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
###########################################################################

import time;
import sys;


def hex_to_int(str):
    i = eval("0x" + str, {}, {})
    return i

def maf(code):
    code = hex_to_int(code)
    return code * 0.00132276

def throttle_pos(code):
    code = hex_to_int(code)
    return code * 100.0 / 255.0

def intake_m_pres(code): # in kPa
    code = hex_to_int(code)
    return code / 0.14504
  
def rpm(code):
    code = hex_to_int(code)
    return code / 4

def speedMph(code):
    code = hex_to_int(code)
    return code / 1.609

def percent_scale(code):
    code = hex_to_int(code)
    return code * 100.0 / 255.0

def timing_advance(code):
    code = hex_to_int(code)
    return (code - 128) / 2.0

def sec_to_min(code):
    code = hex_to_int(code)
    return code / 60

def tempCelcius(code):
    code = hex_to_int(code)
    celcius = code - 40
    return celcius

def cpass(code):
    #fixme
    return code

def fuel_trim_percent(code):
    code = hex_to_int(code)
    #return (code - 128.0) * 100.0 / 128
    return (code - 128) * 100 / 128

def dtc_decrypt(code):
    #first byte is byte after PID and without spaces
    num = hex_to_int(code[:2]) #A byte
    res = []

    if num & 0x80: # is mil light on
        mil = 1
    else:
        mil = 0
        
    # bit 0-6 are the number of dtc's. 
    num = num & 0x7f
    
    res.append(num)
    res.append(mil)
    
    numB = hex_to_int(code[2:4]) #B byte
      
    for i in range(0,3):
        res.append(((numB>>i)&0x01)+((numB>>(3+i))&0x02))
    
    numC = hex_to_int(code[4:6]) #C byte
    numD = hex_to_int(code[6:8]) #D byte
       
    for i in range(0,7):
        res.append(((numC>>i)&0x01)+(((numD>>i)&0x01)<<1))
    
    res.append(((numD>>7)&0x01)) #EGR SystemC7  bit of different 
    
    #return res
    return "#"

def hex_to_bitstring(str):
    bitstring = ""
    for i in str:
        # silly type safety, we don't want to eval random stuff
        if type(i) == type(''): 
            v = eval("0x%s" % i)
            if v & 8 :
                bitstring += '1'
            else:
                bitstring += '0'
            if v & 4:
                bitstring += '1'
            else:
                bitstring += '0'
            if v & 2:
                bitstring += '1'
            else:
                bitstring += '0'
            if v & 1:
                bitstring += '1'
            else:
                bitstring += '0'                
    return bitstring

# Sensor class used for data values with units
# bEnabled sets wether the sensor should be shown or not
class Sensor:
    def __init__(self, shortName, sensorName, sensorCommand, valueParserFunc, strUnit, bEnabled):
        self.shortname = shortName
        self.name = sensorName
        self.cmd = sensorCommand
        self.value = 0.0
        self.valueParserFunc = valueParserFunc
        self.unit = strUnit
        self.enabled = bEnabled
        
    # Update the sensor value
    def update(self, newVal):
        self.value = self.valueParserFunc(newVal)
        
    def getFormattedValue(self):
        # Round decimal places
        if type(self.value)==float:
            formatted = str("%.2f"%round(self.value, 3))
        else:
            formatted = str(self.value)
        
        # Add unit text
        formatted = formatted + str(self.unit)
        
        return formatted
        
# Adapter sensor class used for data values with units, but also min/max values and lower and upper safe limits
# The safe lower limit is the lower bound for a safe value (e.g. the lowest standard operating temperature)
# The safe upper limit is the higher bound for a safe value (e.g. the highest standard operating temperature. If it rises above this, there is a problem)
class SensorLimits(Sensor):
    def __init__(self, shortName, sensorName, sensorCmd, valueParserFunc, strUnit, min, max, lowerSafeLimit, upperSafeLimit, bEnabled):
        Sensor.__init__(self, shortName, sensorName, sensorCmd, valueParserFunc, strUnit, bEnabled)
        self.min = min
        self.max = max
        self.lowerSafeLimit = lowerSafeLimit
        self.upperSafeLimit = upperSafeLimit
        
        
# The coolant sensor class is a bespoke class that is used to display when the coolant has been up to operating temperature for
# more than five minutes. This is for cars that don't have access to the oil temperature via OBD2 (like mine). Waiting five minutes
# after the coolant has warmed up generally means the oil should be warmed up too, so we want to display this.
class CoolantSensor(SensorLimits):
    def __init__(self, shortName, sensorName, sensorCmd, valueParserFunc, strUnit, min, max, lowerSafeLimit, upperSafeLimit, bEnabled):
        SensorLimits.__init__(self, shortName, sensorName, sensorCmd, valueParserFunc, strUnit, min, max, lowerSafeLimit, upperSafeLimit, bEnabled)
        self.bReachedOpTemp = False
        self.bOilTempReady = False
        self.timeLastReachedTemp = sys.maxint
        
        # This defines the time to wait in seconds that oil takes to warm up after coolant has (default: 5 mins)
        self.oilTempDelay = 300
        
    def update(self, newVal):
        Sensor.update(newVal)
        
        # Is the sensor up-to-temp yet?
        if self.bReachedOpTemp == False and self.value >= self.lowerSafeLimit:
            self.bReachedOpTemp = True
            
            # Get current time (in seconds)
            self.timeLastReachedTemp = time.time()
        
        # Has the temp dropped? (shouldn't happen, unless the engine is switched off. best to handle it anyway.)
        if self.bReachedOpTemp and self.value < self.lowerSafeLimit:
            # This will essentially reset the oil warm-up timer
            self.bReachedOpTemp = False
            self.bOilTempReady = False
            self.timeLastReachedTemp = sys.maxint
        
        # If the engine has just started up (1 min or less) and the coolant is already up to temp then we can wait a little less time
        #TODO: need a way to get engine running time sensor value here
        # Has the sensor been up-to-temp for more than five minutes?
        if self.bReachedOpTemp and time.time() > (self.timeLastReachedTemp + self.oilTempDelay):
            # Oil temp should be ready now!
            self.bOilTempReady = True
            
    def getFormattedValue(self):
        formatted = Sensor.getFormattedValue()
        
        # Add oil temp indicator
        formatted = formatted + str(" OIL:")
        
        if self.bReachedOpTemp:
            if self.bOilTempReady:
                # Oil is ready
                formatted = formatted + str("OK")
            else:
                # Display countdown
                timeLeft = self.timeLastReachedTemp + self.oilTempDelay - time.time()
                formatted = formatted + str(timeLeft) + str("s")
        else:
            # Wait for coolant temp
            formatted = formatted + str("WAIT")
        
        return formatted


# NOTE: The ordering of this array is important
SENSORS = [
    #       CODE                        NAME                    PID                                         ENABLED
    Sensor("pids",                      "Supported PIDs",       "0100", hex_to_bitstring, "",               True), 
    Sensor("dtc_status",                "S-S DTC Cleared",      "0101", dtc_decrypt, "",                    False),    
    Sensor("dtc_ff",                    "DTC C-F-F",            "0102", cpass, "",                          False),      
    Sensor("fuel_status",               "Fuel System Stat",     "0103", cpass, "",                          False),
    Sensor("load",                      "Calc Load Value",      "01041", percent_scale, "",                 True),    
    CoolantSensor("temp",               "Coolant Temp",         "0105", tempCelcius, "C", 0, 140, 60, 99,   True), # 90C is optimal temp - change back to 88 when not testing!
    Sensor("short_term_fuel_trim_1",    "S-T Fuel Trim",        "0106", fuel_trim_percent, "%",             False),
    Sensor("long_term_fuel_trim_1",     "L-T Fuel Trim",        "0107", fuel_trim_percent, "%",             False),
    Sensor("short_term_fuel_trim_2",    "S-T Fuel Trim",        "0108", fuel_trim_percent, "%",             False),
    Sensor("long_term_fuel_trim_2",     "L-T Fuel Trim",        "0109", fuel_trim_percent, "%",             False),
    Sensor("fuel_pressure",             "FuelRail Pressure",    "010A", cpass, "",                          False),
    Sensor("manifold_pressure",         "Intk Manifold",        "010B", intake_m_pres, "psi",               True),
    SensorLimits("rpm",                 "Engine RPM",           "010C1", rpm, "", 0, 5500, 1000, 4650,      True), # 5k is redline
    SensorLimits("speed",               "Vehicle Speed",        "010D1", speedMph, "MPH", 0, 160, 0, 70,    True),
    Sensor("timing_advance",            "Timing Advance",       "010E", timing_advance, "degrees",          False),
    Sensor("intake_air_temp",           "Intake Air Temp",      "010F", tempCelcius, "C",                   False),
    Sensor("maf",                       "AirFlow Rate(MAF)",    "0110", maf, "lb/min",                      True),
    Sensor("throttle_pos",              "Throttle Position",    "01111", throttle_pos, "%",                 False),
    Sensor("secondary_air_status",      "2nd Air Status",       "0112", cpass, "",                          False),
    Sensor("o2_sensor_positions",       "Loc of O2 sensors",    "0113", cpass, "",                          False),
    Sensor("o211",                      "O2 Sensor: 1 - 1",     "0114", fuel_trim_percent, "%",             False),
    Sensor("o212",                      "O2 Sensor: 1 - 2",     "0115", fuel_trim_percent, "%",             False),
    Sensor("o213",                      "O2 Sensor: 1 - 3",     "0116", fuel_trim_percent, "%",             False),
    Sensor("o214",                      "O2 Sensor: 1 - 4",     "0117", fuel_trim_percent, "%",             False),
    Sensor("o221",                      "O2 Sensor: 2 - 1",     "0118", fuel_trim_percent, "%",             False),
    Sensor("o222",                      "O2 Sensor: 2 - 2",     "0119", fuel_trim_percent, "%",             False),
    Sensor("o223",                      "O2 Sensor: 2 - 3",     "011A", fuel_trim_percent, "%",             False),
    Sensor("o224",                      "O2 Sensor: 2 - 4",     "011B", fuel_trim_percent, "%",             False),
    Sensor("obd_standard",              "OBD Designation",      "011C", cpass, "",                          False),
    Sensor("o2_sensor_position_b",      "Loc of O2 sensor",     "011D", cpass, "",                          False),
    Sensor("aux_input",                 "Aux input status",     "011E", cpass, "",                          False),
    Sensor("engine_time",               "Engine Start MIN",     "011F", sec_to_min, "min",                  True),
    Sensor("engine_mil_time",           "Engine Run MIL",       "014D", sec_to_min, "min",                  False)
    ]
     
    
#___________________________________________________________
