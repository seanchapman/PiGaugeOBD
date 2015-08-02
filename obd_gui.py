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
        control.Bind(wx.EVT_LEFT_DOWN, self.onLeft)
        control.Bind(wx.EVT_RIGHT_DOWN, self.onRight)
        
        # Initialise connection, sensors, port and list variables
        self.connection = None
        self.istart = 0
        self.sensors = []
        self.port = None
        self.boxes = []
        self.texts = []


    def setConnection(self, connection):
        self.connection = connection
    
    def setSensors(self, sensors):
        self.sensors = sensors
        
    def setPort(self, port):
        self.port = port

    def getSensorsToDisplay(self, istart):
        """
        Get at most 1 sensor to be displayed on screen.
        """
        sensors_display = []
        if istart<len(self.sensors):
            iend = istart + 1
            sensors_display = self.sensors[istart:iend]
        return sensors_display

    def ShowSensors(self):
        """
        Display the sensors.
        """
        
        sensors = self.getSensorsToDisplay(self.istart)

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

        # Create a box for each sensor
        for index, sensor in sensors:
            
            self.port.updateSensor(index)
            (name, value, unit) = self.port.getSensorTuple(index)

            box = wx.StaticBox(self, wx.ID_ANY)
            self.boxes.append(box)
            boxSizer = wx.StaticBoxSizer(box, wx.VERTICAL)
                
            formatted = self.port.getSensorFormatted(index)
            t1 = wx.StaticText(parent=self, label=formatted, style=wx.ALIGN_CENTER)
            t1.SetForegroundColour('WHITE')
            font1 = wx.Font(30, wx.ROMAN, wx.NORMAL, wx.NORMAL, faceName="Monaco")
            t1.SetFont(font1)
            boxSizer.Add(t1, 0, wx.ALIGN_CENTER | wx.ALL, 70)
            boxSizer.AddStretchSpacer()
            self.texts.append(t1)

            # Text for sensor name
            t2 = wx.StaticText(parent=self, label=name, style=wx.ALIGN_CENTER)
            t2.SetForegroundColour('WHITE')
            font2 = wx.Font(10, wx.ROMAN, wx.NORMAL, wx.BOLD, faceName="Monaco")
            t2.SetFont(font2)
            boxSizer.Add(t2, 0, wx.ALIGN_CENTER | wx.ALL, 45)
            self.texts.append(t2)
            gridSizer.Add(boxSizer, 1, wx.EXPAND | wx.ALL)

        # Add invisible boxes if necessary
        nsensors = len(sensors)
        for i in range(1-nsensors):
            box = wx.StaticBox(self)
            boxSizer = wx.StaticBoxSizer(box, wx.VERTICAL)
            self.boxes.append(box)
            box.Show(False)
            gridSizer.Add(boxSizer, 1, wx.EXPAND | wx.ALL)
           
        # Layout
        boxSizerMain.Add(gridSizer, 1, wx.EXPAND | wx.ALL, 0)
        self.SetSizer(boxSizerMain)
        self.Refresh()
        self.Layout() 

        # Timer for update
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.refresh, self.timer)
        self.timer.Start(500)


    # Update gets fresh data from the sensors
    def refresh(self, event):
        sensors = self.getSensorsToDisplay(self.istart)   
        
        itext = 0
        for index, sensor in sensors:

            self.port.updateSensor(index)
            formattedValue = self.port.getSensorFormatted(index)

            if itext<len(self.texts):
                self.texts[itext*2].SetLabel(formattedValue)
            
            itext += 1


    def onCtrlC(self, event):
        self.GetParent().Close()

    def onLeft(self, event):
        """
        Get data from previous sensor in the list.
        """
        istart = self.istart + 1
        if istart<len(self.sensors):
            self.istart = istart
            self.ShowSensors()
        else: 
			istart = self.istart - 31 
			self.istart = istart 
			self.ShowSensors() 
				
    def onRight(self, event):
        """
        Get data from next sensor in the list.
        """
        istart = self.istart + 1
        if istart<len(self.sensors):
            self.istart = istart
            self.ShowSensors()
        else: 
			istart = self.istart - 31
			self.istart = istart
			self.ShowSensors()
            
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
            sensors = self.panelLoading.getSensors()
            port = self.panelLoading.getPort()
            self.panelLoading.Destroy()
        self.panelGauges = OBDPanelGauges(self)
        
        if connection:
            self.panelGauges.setConnection(connection)

        if sensors:
            self.panelGauges.setSensors(sensors)
            self.panelGauges.setPort(port)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.panelGauges, 1, wx.EXPAND)
        self.SetSizer(self.sizer)
        self.panelGauges.ShowSensors()
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

