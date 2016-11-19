#!/usr/bin/env python

# The PiGaugeOBD app starting point

from obd_gui import *
import wx

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

# Main
app = OBDApp(False)
app.MainLoop()