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

#-------------------------------------------------------------------------------

# OBD variable
GAUGE_FILENAME		= "frame_C1.jpg"
LOADING_BG_FILENAME	= "loading_bg.png"

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
        self.sensors = []  # Note: This is populated with the enabled sensors by OBDFrame before it calls createGaugeGui
        self.port = None
        self.boxes = []
        self.texts = []
        
        
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
        nrows, ncols = 1, 1
        vgap, hgap = 50, 50
        gridSizer = wx.GridSizer(nrows, ncols, vgap, hgap)

        # Create a box for currently selected sensor
        box = wx.StaticBox(self, wx.ID_ANY)
        self.boxes.append(box)
        boxSizer = wx.StaticBoxSizer(box, wx.VERTICAL)
            
        # Fetch latest sensor values
        sensor = self.sensors[self.currSensorIndex]
        self.port.updateSensor(sensor)
        formatted = sensor.getFormattedValue()
        
        # Create text for sensor value
        t1 = wx.StaticText(parent=self, label=formatted, style=wx.ALIGN_CENTER)
        font1 = wx.Font(30, wx.ROMAN, wx.NORMAL, wx.NORMAL, faceName="Monaco")
        t1.SetFont(font1)
        t1.SetForegroundColour('WHITE')
        boxSizer.Add(t1, 0, wx.ALIGN_CENTER | wx.ALL, 70)
        boxSizer.AddStretchSpacer()
        self.texts.append(t1)

        # Create Text for sensor name
        t2 = wx.StaticText(parent=self, label=sensor.name, style=wx.ALIGN_CENTER)
        t2.SetForegroundColour('WHITE')
        font2 = wx.Font(10, wx.ROMAN, wx.NORMAL, wx.BOLD, faceName="Monaco")
        t2.SetFont(font2)
        boxSizer.Add(t2, 0, wx.ALIGN_CENTER | wx.ALL, 45)
        self.texts.append(t2)
        gridSizer.Add(boxSizer, 1, wx.EXPAND | wx.ALL)
           
        # Layout
        boxSizerMain.Add(gridSizer, 1, wx.EXPAND | wx.ALL, 0)
        self.SetSizer(boxSizerMain)
        self.Refresh()
        self.Layout() 

        # Timer for update
        try:
            self.timer.Start(500)
        except AttributeError:
            # Create timer
            self.timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self.obdUpdate, self.timer)
            self.timer.Start(500)


    # Update gets fresh data from the sensors
    def obdUpdate(self, event):
        i = 0
        for sensor in self.sensors:
            self.port.updateSensor(sensor)
            
            if i == self.currSensorIndex:  
                formattedValue = sensor.getFormattedValue()
                
                # Update GUI
                # Index 0 is sensor value, index 1 is sensor name
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
                    enabledSensors.append(sensor[1])
        
            self.panelGauges.sensors = enabledSensors
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

