#!/usr/bin/env python

# Contains the loading screen code

import wx
import time
from obd_connection import *

# Loading screen background texture
LOADING_BG_FILENAME	= "loading_bg.png"

class OBDLoadingPanel(wx.Panel):
    # True = skips connecting to the OBD port and just displays the GUI
    DEBUG_MODE = True

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
        self.textCtrl = wx.TextCtrl(self, pos=(10, 170), size=(300, 60), style=wx.TE_READONLY | wx.TE_MULTILINE)
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

        if self.DEBUG_MODE == False:
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
