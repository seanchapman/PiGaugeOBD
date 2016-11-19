#!/usr/bin/env python

# The OBD connection thread class, for updating the sensor values.

from obd_capture import OBD_Capture
from threading import Thread

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