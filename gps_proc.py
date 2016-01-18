from multiprocessing import Process
from proto import *
from gps import *
import logging

class GpsProc(Process):

    def __init__(self, fd):
        Process.__init__(self)
        self.fd = fd
        self.gpsd = gps(mode=WATCH_ENABLE)
        self._running = True

    def run(self):
        logging.info('gpsd: starting service')
        while self._running:
            while self.gpsd.waiting():
                self.gpsd.next()
            while self.fd.poll():
                self.dispatch(self.fd.recv())
        logging.info('gpsd: service exiting')

    def dispatch(self, cmd):
        if cmd.name == get_fix:
            args = [self.gpsd.fix.latitude, self.gpsd.fix.longitude, self.gpsd.fix.altitude]
            self.fd.send(Command(fix, args))
        elif cmd.name == ping:
            self.fd.send(Command(pong))
        elif cmd.name == close:
            self.fd.send(Command(close))
            self._running = False
        else:
            logging.warning('gpsd: unknown command: ' + cmd.name)
            self.fd.send(Command(unknown))

    def is_running(self):
        return self._running
