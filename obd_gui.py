#!/usr/bin/env python
###########################################################################
# obd_gui.py
#
# Created by Paul Bartek (pbartek@cowfishstudios.com)
#
###########################################################################
#-------------------------------------------------------------------------------

import os
import wx

from obd_loading import *
from pigauge_features import *
from obd_sensors import Sensor

#-------------------------------------------------------------------------------

# Gauge texture
GAUGE_FILENAME = "frame_C2.jpg"

# Global update interval in milliseconds (this triggers the updating of the OBD sensors)
GLOBAL_UPDATE_INTERVAL = 400

# True = speedometer style UI
# False = gauge pod style UI
SPEEDOMETER_STYLE = True

# Short names for the sensors displayed in speedo mode
SPEEDO_SENSOR_SHORTNAMES = ['rpm', 'speed', 'temp']

#-------------------------------------------------------------------------------

# Gets and updates the sensor, if the sensors list has been populated, otherwise returns debug sensor
def GetAndUpdateSensor(sensors, index, port):
    if sensors:
        # Fetch latest sensor values
        sensor = sensors.values()[index]
        port.updateSensor(sensor)
        return sensor
    else:
        return Sensor(str(index), str(index), None, None, None, None)

# The same as GetAndUpdateSensor but uses short name rather than index
def GetAndUpdateSensorByName(sensors, shortName, port):
    if sensors:
        # Iterate to find sensor short name
        for sensorShortName, sensor in sensors.iteritems():
            if shortName == sensorShortName:
                port.updateSensor(sensor)
                return sensor
    else:
        return Sensor(shortName, shortName, None, None, None, None)

def CreateSensorNameText(theParent, sensor):
    tSensorName = wx.StaticText(parent=theParent, label=sensor.name, style=wx.ALIGN_CENTER)
    tSensorName.SetForegroundColour('WHITE')
    tSensorName.SetFont(wx.Font(10, wx.ROMAN, wx.NORMAL, wx.BOLD, faceName="Monaco"))
    return tSensorName

def CreateSensorValText(theParent, sensor):
    tSensorVal = wx.StaticText(parent=theParent, label=sensor.getFormattedValue(), style=wx.ALIGN_LEFT)
    tSensorVal.SetFont(wx.Font(22, wx.ROMAN, wx.NORMAL, wx.NORMAL, faceName="Monaco"))
    tSensorVal.SetForegroundColour('WHITE')
    return tSensorVal

def CreateInfoBox(theParent):
    tInfoBox = wx.TextCtrl(theParent, pos=(5, 5), size=(100, 220), style=wx.TE_READONLY | wx.TE_MULTILINE)
    tInfoBox.SetBackgroundColour('#21211f')
    tInfoBox.SetForegroundColour(wx.WHITE)
    tInfoBox.SetFont(wx.Font(14, wx.ROMAN, wx.NORMAL, wx.NORMAL, faceName="Monaco"))
    return tInfoBox

#-------------------------------------------------------------------------------

class OBDPanelGauges(wx.Panel):
    """
    Panel for gauges.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Constructor.
        """
        super(OBDPanelGauges, self).__init__(*args, **kwargs)

        # Background image
        image = wx.Image(GAUGE_FILENAME) 
        width, height = wx.GetDisplaySize() 
        image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
        bitmap = wx.BitmapFromImage(image) 
        control = wx.StaticBitmap(self, wx.ID_ANY, bitmap)

        # Handle events for touchscreen taps on background bitmap
        control.Bind(wx.EVT_LEFT_DOWN, self.onLeftClick)
        control.Bind(wx.EVT_RIGHT_DOWN, self.onRightClick)
        
        # Initialise connection, sensors, port and list variables
        self.connection = None
        self.currSensorIndex = 0

        # Indexed by sensor shortname. Note: This is populated with the enabled sensors by OBDFrame before it calls createGaugeGui
        self.sensors = {}

        self.port = None
        self.boxes = []

        # Indexed by sensor shortname + 'name'/'value'. (ie 'rpmname', 'speedvalue'). Contains wx text elements
        # With the exception of "infobox"
        self.texts = {}
        
        # Declare which features should be enabled
        self.features = [TurboTimer(True)]


    # Creates a instrument cluster style GUI
    def createSpeedoGui(self):
        # Destroy previous widgets
        for b in self.boxes: b.Destroy()
        for t in self.texts: t.Destroy()
        self.boxes = []
        self.texts = {}

        # Main sizer
        nrows, ncols = 2, 2
        vgap, hgap = 5, 5
        gridSizerMain = wx.GridSizer(nrows, ncols, vgap, hgap)

        # Create RPM box
        rpmBox = wx.StaticBox(self, wx.ID_ANY)
        self.boxes.append(rpmBox)
        rpmBoxSizer = wx.StaticBoxSizer(rpmBox, wx.VERTICAL)
        rpmSensor = GetAndUpdateSensorByName(self.sensors, 'rpm', self.port)

        # Create text for sensor value
        tSensorVal = CreateSensorValText(self, rpmSensor)
        rpmBoxSizer.Add(tSensorVal, 0, wx.ALIGN_LEFT | wx.ALL, 1)
        rpmBoxSizer.AddStretchSpacer()
        self.texts[rpmSensor.shortname + 'value'] = tSensorVal

        # Create Text for sensor name
        tSensorName = CreateSensorNameText(self, rpmSensor)
        rpmBoxSizer.Add(tSensorName, 0, wx.ALIGN_CENTER | wx.BOTTOM | wx.ALL, 45)
        self.texts[rpmSensor.shortname + 'name'] = tSensorName

        # Create speed box
        speedBox = wx.StaticBox(self, wx.ID_ANY)
        self.boxes.append(speedBox)
        speedBoxSizer = wx.StaticBoxSizer(speedBox, wx.VERTICAL)
        speedSensor = GetAndUpdateSensorByName(self.sensors, 'speed', self.port)

        # Create text for sensor value
        tSensorVal = CreateSensorValText(self, speedSensor)
        speedBoxSizer.Add(tSensorVal, 0, wx.ALIGN_LEFT | wx.ALL, 1)
        speedBoxSizer.AddStretchSpacer()
        self.texts[speedSensor.shortname + 'value'] = tSensorVal

        # Create Text for sensor name
        tSensorName = CreateSensorNameText(self, speedSensor)
        speedBoxSizer.Add(tSensorName, 0, wx.ALIGN_CENTER | wx.BOTTOM | wx.ALL, 45)
        self.texts[speedSensor.shortname + 'name'] = tSensorName

        # Create coolant temp box
        coolantBox = wx.StaticBox(self, wx.ID_ANY)
        self.boxes.append(coolantBox)
        coolantBoxSizer = wx.StaticBoxSizer(coolantBox, wx.VERTICAL)
        coolantSensor = GetAndUpdateSensorByName(self.sensors, 'temp', self.port)

        # Create text for sensor value
        tSensorVal = CreateSensorValText(self, coolantSensor)
        coolantBoxSizer.Add(tSensorVal, 0, wx.ALIGN_LEFT | wx.ALL, 1)
        coolantBoxSizer.AddStretchSpacer()
        self.texts[coolantSensor.shortname + 'value'] = tSensorVal

        # Create Text for sensor name
        tSensorName = CreateSensorNameText(self, coolantSensor)
        coolantBoxSizer.Add(tSensorName, 0, wx.ALIGN_CENTER | wx.BOTTOM | wx.ALL, 45)
        self.texts[coolantSensor.shortname + 'name'] = tSensorName

        # Add to screen
        gridSizerMain.Add(speedBoxSizer, 1, wx.EXPAND | wx.TOP | wx.LEFT | wx.ALIGN_CENTER)
        gridSizerMain.Add(rpmBoxSizer, 1, wx.EXPAND | wx.TOP | wx.RIGHT | wx.ALIGN_CENTER)
        gridSizerMain.Add(coolantBoxSizer, 1, wx.EXPAND | wx.BOTTOM | wx.RIGHT | wx.ALIGN_CENTER)
        self.SetSizer(gridSizerMain)
        self.Refresh()
        self.Layout()

        # Timer for update
        try:
            self.timer.Start(GLOBAL_UPDATE_INTERVAL)
        except AttributeError:
            # Create timer
            self.timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self.obdUpdate, self.timer)
            self.timer.Start(GLOBAL_UPDATE_INTERVAL)


    # Creates a single gauge pod style GUI
    def createGaugeGui(self):
        # Destroy previous widgets
        for b in self.boxes: b.Destroy()
        for t in self.texts: t.Destroy()
        self.boxes = []
        self.texts = {}

        # Grid layout
        nrows, ncols = 1, 2
        vgap, hgap = 5, 5
        gridSizer = wx.GridSizer(nrows, ncols, vgap, hgap)

        # Create a box for left column (currently selected sensor)
        leftBox = wx.StaticBox(self, wx.ID_ANY)
        self.boxes.append(leftBox)
        leftSizer = wx.StaticBoxSizer(leftBox, wx.VERTICAL)

        sensor = GetAndUpdateSensor(self.sensors, self.currSensorIndex, self.port)
        
        # Create text for sensor value
        tSensorVal = CreateSensorValText(self, sensor)
        leftSizer.Add(tSensorVal, 0, wx.ALIGN_LEFT | wx.ALL, 5)
        leftSizer.AddStretchSpacer()
        self.texts['sensorvalue'] = tSensorVal

        # Create Text for sensor name
        tSensorName = CreateSensorNameText(self, sensor)
        leftSizer.Add(tSensorName, 0, wx.ALIGN_CENTER | wx.ALL, 45)
        self.texts['sensorname'] = tSensorName
        
        # Add left sizer to grid
        gridSizer.Add(leftSizer, 1, wx.EXPAND | wx.ALL)
        
        # Create box for right column (additional info)
        rightBox = wx.StaticBox(self, wx.ID_ANY)
        self.boxes.append(rightBox)
        rightSizer = wx.StaticBoxSizer(rightBox, wx.VERTICAL)
        
        # Add info text box to right column
        tInfoBox = CreateInfoBox(self)
        rightSizer.Add(tInfoBox, 0, wx.EXPAND | wx.ALL, 5)
        self.texts['infobox'] = tInfoBox
        
        # Add right sizer to grid
        gridSizer.Add(rightSizer, 1, wx.EXPAND | wx.ALL)
        
        # Layout
        self.SetSizer(gridSizer)
        self.Refresh()
        self.Layout() 

        # Timer for update
        try:
            self.timer.Start(GLOBAL_UPDATE_INTERVAL)
        except AttributeError:
            # Create timer
            self.timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self.obdUpdate, self.timer)
            self.timer.Start(GLOBAL_UPDATE_INTERVAL)


    # Update gets fresh data from the sensors and updates features
    def obdUpdate(self, event):
        i = 0
        for shortname, sensor in self.sensors.iteritems():
            self.port.updateSensor(sensor)

            if SPEEDOMETER_STYLE:
                # Update all displayed sensors
                if shortname in SPEEDO_SENSOR_SHORTNAMES:
                    # This is a currently displayed sensor
                    formattedValue = sensor.getFormattedValue()
                    self.texts[shortname + 'value'].SetLabel(formattedValue)
                    
                    # Update UI elements for special sensors (coolant etc.)
                    if sensor.__class__.__name__ != "Sensor":
                        sensor.updateUi(self.texts[shortname+'value'])
                    else:
                        self.texts[shortname+'value'].SetForegroundColour('WHITE')
            else:
                # Update current sensor index only
                if i == self.currSensorIndex:
                    # Update GUI
                    formattedValue = sensor.getFormattedValue()
                    self.texts['sensorvalue'].SetLabel(formattedValue)
                    self.texts['sensorname'].SetLabel(sensor.name)

                # Update UI elements for special sensors (coolant etc.)
                if sensor.__class__.__name__ != "Sensor":
                    sensor.updateUi(self.texts['sensorvalue'])
                else:
                    self.texts['sensorvalue'].SetForegroundColour('WHITE')
            i += 1

        if SPEEDOMETER_STYLE == False:
            # Update features, passing in the sensor list and info text box
            self.texts['infobox'].Clear()
            for feature in self.features:
                feature.update(self.sensors, self.texts['infobox'])
                self.texts['infobox'].AppendText("\n")


    def onCtrlC(self, event):
        self.GetParent().Close()

        
    def onLeftClick(self, event):
        if SPEEDOMETER_STYLE == False:
            self.currSensorIndex += 1
            if self.currSensorIndex >= len(self.sensors):
                self.currSensorIndex = 0
                
            # Update sensors and GUI
            self.obdUpdate(None)
				
                
    def onRightClick(self, event):
        if SPEEDOMETER_STYLE == False:
            self.currSensorIndex -= 1
            if self.currSensorIndex < 0:
                self.currSensorIndex = len(self.sensors) - 1
                
            # Update sensors and GUI
            self.obdUpdate(None)
            
            
    def OnPaint(self, event):
        self.Paint(wx.PaintDC(self))

#-------------------------------------------------------------------------------

class OBDFrame(wx.Frame):
    """
    OBD frame.
    """

    def __init__(self):
        """
        Constructor.
        """
        wx.Frame.__init__(self, None, wx.ID_ANY, "OBD-Pi")

        self.panelLoading = OBDLoadingPanel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.panelLoading, 1, wx.EXPAND)
        self.SetSizer(self.sizer)

        self.panelLoading.showLoadingScreen()
        self.panelLoading.SetFocus()

        
    def update(self, event):
        if self.panelLoading and OBDLoadingPanel.DEBUG_MODE == False:
            connection = self.panelLoading.getConnection()

            # Sensors are actually in the list format Sensors[SensorIndex, SensorObj]
            sensors = self.panelLoading.getSensors()

            port = self.panelLoading.getPort()
        else:
            connection = None
            sensors = None
            port = None

        self.panelLoading.Destroy()
        self.panelGauges = OBDPanelGauges(self)
        
        if connection:
            self.panelGauges.connection = connection

        if sensors:
            # Get only the enabled sensors and set them in the main gauge GUI
            for sensor in sensors:
                if sensor[1].enabled:
                    self.panelGauges.sensors[sensor[1].shortname] = sensor[1]
        
            self.panelGauges.port = port
            
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.panelGauges, 1, wx.EXPAND)
        self.SetSizer(self.sizer)
        if SPEEDOMETER_STYLE:
            self.panelGauges.createSpeedoGui()
        else:
            self.panelGauges.createGaugeGui()

        self.panelGauges.SetFocus()
        self.Layout()

    def OnPaint(self, event): 
        self.Paint(wx.PaintDC(self))     
