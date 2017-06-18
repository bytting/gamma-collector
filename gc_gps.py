# Detector controller for gamma measurements
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

import threading
from gps import *

class GpsThread(threading.Thread):
    """
    Thread class to handle the gps driver
    """
    def __init__(self, event):
        """
        Initialize the gps thread
        """
        threading.Thread.__init__(self)
        self._stopped = event
        self._gpsd = gps(mode = WATCH_ENABLE)
        self._latitude = 0.0
        self._latitude_err = 0.0
        self._longitude = 0.0
        self._longitude_err = 0.0
        self._altitude = 0.0
        self._altitude_err = 0.0
        self._track = 0.0
        self._track_err = 0.0
        self._speed = 0.0
        self._speed_err = 0.0
        self._climb = 0.0
        self._climb_err = 0.0
        self._time = ''

    def run(self):
        """
        Entry point for the gps thread
        """
        # Process any buffered gps signals every 0.5 seconds
        while not self._stopped.wait(0.5):
            # Update our last measurement until buffer is empty
            while self._gpsd.waiting():
                self._gpsd.next()
                if not math.isnan(self._gpsd.fix.latitude):
                    self._latitude = self._gpsd.fix.latitude
                if not math.isnan(self._gpsd.fix.epx):
                    self._latitude_err = self._gpsd.fix.epx
                if not math.isnan(self._gpsd.fix.longitude):
                    self._longitude = self._gpsd.fix.longitude
                if not math.isnan(self._gpsd.fix.epy):
                    self._longitude_err = self._gpsd.fix.epy
                if not math.isnan(self._gpsd.fix.altitude):
                    self._altitude = self._gpsd.fix.altitude
                if not math.isnan(self._gpsd.fix.epv):
                    self._altitude_err = self._gpsd.fix.epv
                if not math.isnan(self._gpsd.fix.track):
                    self._track = self._gpsd.fix.track
                if not math.isnan(self._gpsd.fix.epd):
                    self._track_err = self._gpsd.fix.epd
                if not math.isnan(self._gpsd.fix.speed):
                    self._speed = self._gpsd.fix.speed
                if not math.isnan(self._gpsd.fix.eps):
                    self._speed_err = self._gpsd.fix.eps
                if not math.isnan(self._gpsd.fix.climb):
                    self._climb = self._gpsd.fix.climb
                if not math.isnan(self._gpsd.fix.epc):
                    self._climb_err = self._gpsd.fix.epc
                if self._gpsd.utc != None and self._gpsd.utc != '':
                    self._time = self._gpsd.utc

    @property
    def latitude(self):
        return self._latitude

    @property
    def latitude_err(self):
        return self._latitude_err

    @property
    def longitude(self):
        return self._longitude

    @property
    def longitude_err(self):
        return self._longitude_err

    @property
    def altitude(self):
        return self._altitude

    @property
    def altitude_err(self):
        return self._altitude_err

    @property
    def track(self):
        return self._track

    @property
    def track_err(self):
        return self._track_err

    @property
    def speed(self):
        return self._speed

    @property
    def speed_err(self):
        return self._speed_err

    @property
    def climb(self):
        return self._climb

    @property
    def climb_err(self):
        return self._climb_err

    @property
    def time(self):
        return self._time

    @property
    def position(self):
        return {
            'latitude' : self._latitude, 'latitude_error' : self._latitude_err,
            'longitude' : self._longitude, 'longitude_error' : self._longitude_err,
            'altitude' : self._altitude, 'altitude_error' : self._altitude_err
        }

    @property
    def velocity(self):
        return {
            'track' : self._track, 'track_error' : self._track_err,
            'speed' : self._speed, 'speed_error' : self._speed_err,
            'climb' : self._climb, 'climb_error' : self._climb_err
       }
