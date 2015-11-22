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
import time
from threading import Thread

from obd_capture import OBD_Capture
from obd_sensors import SENSORS
from obd_sensors import *
from pigauge_features import *

#-------------------------------------------------------------------------------

# OBD variable
GAUGE_FILENAME		= "frame_C2.jpg"
LOADING_BG_FILENAME	= "loading_bg.png"

# Global update interval in milliseconds (this triggers the updating of the OBD sensors)
GLOBAL_UPDATE_INTERVAL = 400

#-------------------------------------------------------------------------------

def obd_connect(obdCap):
    obdCap.connect()

class OBDConnection(object):
    """
    Class for OBD connection. Use a thread for connection.
    """
    
    def __init__(self):
        self.obdCap = OBD_Capture()

    def get_capture(self):
        return self.obdCap
    
    # Start a thread to connect to available BT/USB serial port
    def connect(self):
        self.t = Thread(target=obd_connect, args=(self.obdCap,))
        self.t.start()

    def is_connected(self):
        return self.obdCap.is_connected()

    def get_output(self):
        if self.obdCap and self.obdCap.is_connected():
            return self.obdCap.capture_data()
        return ""

    def get_port(self):
        return self.obdCap.is_connected()

    def get_port_name(self):
        if self.obdCap:
            port = self.obdCap.is_connected()
            if port:
                try:
                    return port.port.name
                except:
                    pass
        return None
    
    def get_sensors(self):
        sensors = []
        if self.obdCap:
            sensors = self.obdCap.getSupportedSensorList()
        return sensors

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
        self.sensors = {}  # Indexed by sensor shortname. Note: This is populated with the enabled sensors by OBDFrame before it calls createGaugeGui
        self.port = None
        self.boxes = []
        self.texts = []
        
        # Declare which features should be enabled
        self.features = [TurboTimer(True)]
        
        
    # Create the GUI for the gauges
    def createGaugeGui(self):
        """
        Display the sensors.
        """

        # Destroy previous widgets
        for b in self.boxes: b.Destroy()
        for t in self.texts: t.Destroy()
        self.boxes = []
        self.texts = []

        # Main sizer
        boxSizerMain = wx.BoxSizer(wx.VERTICAL)

        # Grid sizer
        nrows, ncols = 1, 2
        vgap, hgap = 5, 5
        gridSizer = wx.GridSizer(nrows, ncols, vgap, hgap)

        # Create a box for left column (currently selected sensor)
        leftBox = wx.StaticBox(self, wx.ID_ANY)
        self.boxes.append(leftBox)
        leftSizer = wx.StaticBoxSizer(leftBox, wx.VERTICAL)
            
        # Fetch latest sensor values
        sensor = self.sensors.values()[self.currSensorIndex]
        self.port.updateSensor(sensor)
        formatted = sensor.getFormattedValue()
        
        # Create text for sensor value
        tSensorVal = wx.StaticText(parent=self, label=formatted, style=wx.ALIGN_LEFT)
        font1 = wx.Font(26, wx.ROMAN, wx.NORMAL, wx.NORMAL, faceName="Monaco")
        tSensorVal.SetFont(font1)
        tSensorVal.SetForegroundColour('WHITE')
        leftSizer.Add(tSensorVal, 0, wx.ALIGN_LEFT | wx.ALL, 5)
        leftSizer.AddStretchSpacer()
        self.texts.append(tSensorVal)

        # Create Text for sensor name
        tSensorName = wx.StaticText(parent=self, label=sensor.name, style=wx.ALIGN_CENTER)
        tSensorName.SetForegroundColour('WHITE')
        font2 = wx.Font(10, wx.ROMAN, wx.NORMAL, wx.BOLD, faceName="Monaco")
        tSensorName.SetFont(font2)
        leftSizer.Add(tSensorName, 0, wx.ALIGN_CENTER | wx.ALL, 45)
        self.texts.append(tSensorName)
        
        # Add left sizer to grid
        gridSizer.Add(leftSizer, 1, wx.EXPAND | wx.ALL)
        
        # Create box for right column (additional info)
        rightBox = wx.StaticBox(self, wx.ID_ANY)
        self.boxes.append(rightBox)
        rightSizer = wx.StaticBoxSizer(rightBox, wx.VERTICAL)
        
        # Add info text box to right column
        tInfoBox = wx.TextCtrl(self, pos=(5,5), size=(100,220), style=wx.TE_READONLY | wx.TE_MULTILINE)
        tInfoBox.SetBackgroundColour('#21211f')
        tInfoBox.SetForegroundColour(wx.WHITE)
        tInfoBox.SetFont(wx.Font(14, wx.ROMAN, wx.NORMAL, wx.NORMAL, faceName="Monaco"))
        
        rightSizer.Add(tInfoBox, 0, wx.EXPAND | wx.ALL, 5)
        self.texts.append(tInfoBox)
        
        # Add right sizer to grid
        gridSizer.Add(rightSizer, 1, wx.EXPAND | wx.ALL)
        
        # Layout
        boxSizerMain.Add(gridSizer, 1, wx.EXPAND | wx.ALL, 0)
        self.SetSizer(boxSizerMain)
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
            
            if i == self.currSensorIndex:  
                formattedValue = sensor.getFormattedValue()
                
                # Update GUI
                # Index 0 is sensor value, index 1 is sensor name, index 2 is info textbox
                self.texts[0].SetLabel(formattedValue)
                self.texts[1].SetLabel(sensor.name)
                
                # Colour text based on sensor limits
                if sensor.__class__.__name__ == "SensorLimits":
                    # Is sensor value within safe limit?
                    if sensor.value >= sensor.lowerSafeLimit and sensor.value <= sensor.upperSafeLimit:
                        # Within safe limits
                        self.texts[0].SetForegroundColour(wx.Colour(0,255,0))
                    elif sensor.value > sensor.upperSafeLimit:
                        # Above safe limit
                        self.texts[0].SetForegroundColour(wx.Colour(255,0,0))
                    else:
                        # Below safe limit
                        self.texts[0].SetForegroundColour(wx.Colour(255,255,0))
                        
                elif sensor.__class__.__name__ == "CoolantSensor":
                    # Coolant sensor only shows green when oil temp is ready
                    if sensor.bOilTempReady and sensor.value <= sensor.upperSafeLimit:
                        # Oil temp ready and coolant safe
                        self.texts[0].SetForegroundColour(wx.Colour(0,255,0))
                    elif sensor.value > sensor.upperSafeLimit:
                        # Coolant unsafe (too hot)
                        self.texts[0].SetForegroundColour(wx.Colour(255,0,0))
                    elif sensor.bOilTempReady == False and sensor.value >= sensor.lowerSafeLimit and sensor.value <= sensor.upperSafeLimit:
                        # Oil not ready but coolant is safe
                        self.texts[0].SetForegroundColour(wx.Colour(255,153,0))
                    else:
                        # Coolant unsafe(too cold)
                        self.texts[0].SetForegroundColour(wx.Colour(255,255,0))
                else:
                    self.texts[0].SetForegroundColour('WHITE')
            
            i += 1
            
        # Update features, passing in the sensor list and info text box
        self.texts[2].Clear()
        for feature in self.features:
            feature.update(self.sensors, self.texts[2])
            self.texts[2].AppendText("\n")


    def onCtrlC(self, event):
        self.GetParent().Close()

        
    def onLeftClick(self, event):
        """
        Go to the next screen
        """
        self.currSensorIndex += 1
        if self.currSensorIndex >= len(self.sensors):
            self.currSensorIndex = 0
            
        # Update sensors and GUI
        self.obdUpdate(None)
				
                
    def onRightClick(self, event):
        """
        Go to the previous screen
        """
        self.currSensorIndex -= 1
        if self.currSensorIndex < 0:
            self.currSensorIndex = len(self.sensors) - 1
            
        # Update sensors and GUI
        self.obdUpdate(None)
            
            
    def OnPaint(self, event):
        self.Paint(wx.PaintDC(self))

#-------------------------------------------------------------------------------

class OBDLoadingPanel(wx.Panel):
    """
    Main panel for OBD application. 

    Show loading screen. Handle event from mouse/keyboard.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Constructor.
        """
        super(OBDLoadingPanel, self).__init__(*args, **kwargs)

        # Create background image
        image = wx.Image(LOADING_BG_FILENAME)
        width, height = wx.GetDisplaySize()
        image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
        bitmap = wx.BitmapFromImage(image) 
        control = wx.StaticBitmap(self, wx.ID_ANY, bitmap)

        # Connection
        self.obdConn = None

        # Sensors list
        self.sensors = []

        # Port
        self.port = None

    def getConnection(self):
        return self.obdConn

    def showLoadingScreen(self):
        """
        Display the loading screen.
        """
		
        # Setup loading output text box
        self.textCtrl = wx.TextCtrl(self, pos=(10,170), size=(300,60), style=wx.TE_READONLY | wx.TE_MULTILINE)
        self.textCtrl.SetBackgroundColour('#21211f')
        self.textCtrl.SetForegroundColour(wx.WHITE)
        self.textCtrl.SetFont(wx.Font(10, wx.ROMAN, wx.NORMAL, wx.NORMAL, faceName="Monaco"))
		
        self.textCtrl.AppendText(" Opening interface (serial port)\n")
        self.textCtrl.AppendText(" Trying to connect...\n")
        
        self.timer0 = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.connect, self.timer0)
        self.timer0.Start(1000)


    def connect(self, event):
        if self.timer0:
            self.timer0.Stop()

        # Connect to serial port, get ELM version, set CAN mode
        self.obdConn = OBDConnection()
        self.obdConn.connect()
        connected = False
        while not connected:
            connected = self.obdConn.is_connected()
            self.textCtrl.Clear()
            self.textCtrl.AppendText(" Trying to connect ..." + time.asctime())
            time.sleep(1)

        # Connected, get list of available sensors
        self.textCtrl.Clear()
        port_name = self.obdConn.get_port_name()
        if port_name:
            self.textCtrl.AppendText(" Connected on port " + port_name + "\n")
        self.textCtrl.AppendText(" Error? Hold ALT & ESC to view terminal.")
        self.textCtrl.AppendText(str(self.obdConn.get_output()))
        self.sensors = self.obdConn.get_sensors()
        self.port = self.obdConn.get_port()

        # This tells the main frame to check that we have a connection now
        self.GetParent().update(None)


    def getSensors(self):
        return self.sensors
    
    def getPort(self):
        return self.port

    def onCtrlC(self, event):
        self.GetParent().Close()

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
        if self.panelLoading:
            connection = self.panelLoading.getConnection()
            
            # Sensors are actually in the list format Sensors[SensorIndex, SensorObj]
            sensors = self.panelLoading.getSensors()
            
            port = self.panelLoading.getPort()
            self.panelLoading.Destroy()
        self.panelGauges = OBDPanelGauges(self)
        
        if connection:
            self.panelGauges.connection = connection

        if sensors:
            # Get only the enabled sensors and set them in the main gauge GUI
            enabledSensors = []
            for sensor in sensors:
                if sensor[1].enabled == True:
                    self.panelGauges.sensors[sensor[1].shortname] = sensor[1]
        
            self.panelGauges.port = port
            
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.panelGauges, 1, wx.EXPAND)
        self.SetSizer(self.sizer)
        self.panelGauges.createGaugeGui()
        self.panelGauges.SetFocus()
        self.Layout()

    def OnPaint(self, event): 
        self.Paint(wx.PaintDC(self))     

#-------------------------------------------------------------------------------

class OBDApp(wx.App):
    """
    OBD Application.
    """

    def __init__(self, redirect=False, filename=None, useBestVisual=False, clearSigInt=True):
        """
        Constructor.
        """
        wx.App.__init__(self, redirect, filename, useBestVisual, clearSigInt)

    def OnInit(self):
        """
        Initializer.
        """
        # Main frame                                           
        frame = OBDFrame()
        self.SetTopWindow(frame)
        frame.ShowFullScreen(True)
        frame.Show(True)

        return True

    def FilterEvent(self, event):
        if event.GetEventType == wx.KeyEvent:
            pass

#-------------------------------------------------------------------------------

app = OBDApp(False)
app.MainLoop()

#-------------------------------------------------------------------------------

