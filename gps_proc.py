# Controller for a Canberra Osprey gamma detector
# Copyright (C) 2016  Norwegain Radiation Protection Authority
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Authors: Dag Robole,

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

        self.fd.close()
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
