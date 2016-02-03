from multiprocessing import Process
from proto import *
from gps import *
import logging, math

class GpsProc(Process):

    def __init__(self, fd):
        Process.__init__(self)
        self.fd = fd
        self.gpsd = gps(mode=WATCH_ENABLE)
        self.last_lat = 0
        self.last_lon = 0
        self.last_alt = 0
        self._running = False

    def run(self):
        self._running = True
        logging.info('gpsd: starting service')

        while self._running:
            while self.gpsd.waiting():
                self.gpsd.next()
                if not math.isnan(self.gpsd.fix.latitude):
                    self.last_lat = self.gpsd.fix.latitude
                if not math.isnan(self.gpsd.fix.longitude):
                    self.last_lon = self.gpsd.fix.longitude
                if not math.isnan(self.gpsd.fix.altitude):
                    self.last_alt = self.gpsd.fix.altitude

            while self.fd.poll():
                self.dispatch(self.fd.recv())

        logging.info('gpsd: terminating')

    def dispatch(self, msg):
        if msg.command == 'get_fix':
            msg.command = 'get_fix_ok'
            msg.arguments["latitude"] = self.last_lat
            msg.arguments["longitude"] = self.last_lon
            msg.arguments["altitude"] = self.last_alt
            self.fd.send(msg)
        elif msg.command == 'close':
            self._running = False

    def is_running(self):
        return self._running
