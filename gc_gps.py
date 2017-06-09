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
		Description:
			Initialize the gps thread
		"""
		threading.Thread.__init__(self)
		self._stopped = event
		self.gpsd = gps(mode=WATCH_ENABLE)
		self.clatitude = 0
		self.clatitude_err = 0
		self.clongitude = 0
		self.clongitude_err = 0
		self.caltitude = 0
		self.caltitude_err = 0
		self.ctrack = 0
		self.ctrack_err = 0
		self.cspeed = 0
		self.cspeed_err = 0
		self.cclimb = 0
		self.cclimb_err = 0
		self.ctime = ''

	def run(self):
		"""
		Description:
			Entry point for the gps thread
		"""		

		# Process any buffered gps signals every .3 seconds
		while not self._stopped.wait(0.5):

			# Update our last measurement until buffer is empty
			while self.gpsd.waiting():
				self.gpsd.next()
				if not math.isnan(self.gpsd.fix.latitude):
					self.clatitude = self.gpsd.fix.latitude
				if not math.isnan(self.gpsd.fix.epx):
					self.clatitude_err = self.gpsd.fix.epx
				if not math.isnan(self.gpsd.fix.longitude):
					self.clongitude = self.gpsd.fix.longitude
				if not math.isnan(self.gpsd.fix.epy):
					self.clongitude_err = self.gpsd.fix.epy
				if not math.isnan(self.gpsd.fix.altitude):
					self.caltitude = self.gpsd.fix.altitude
				if not math.isnan(self.gpsd.fix.epv):
					self.caltitude_err = self.gpsd.fix.epv
				if not math.isnan(self.gpsd.fix.track):
					self.ctrack = self.gpsd.fix.track
				if not math.isnan(self.gpsd.fix.epd):
					self.ctrack_err = self.gpsd.fix.epd
				if not math.isnan(self.gpsd.fix.speed):
					self.cspeed = self.gpsd.fix.speed
				if not math.isnan(self.gpsd.fix.eps):
					self.cspeed_err = self.gpsd.fix.eps
				if not math.isnan(self.gpsd.fix.climb):
					self.cclimb = self.gpsd.fix.climb
				if not math.isnan(self.gpsd.fix.epc):
					self.cclimb_err = self.gpsd.fix.epc
				if self.gpsd.utc != None and self.gpsd.utc != '':
					self.ctime = self.gpsd.utc

	@property
	def latitude(self):
		return self.clatitude

	@property
	def latitude_err(self):
		return self.clatitude_err

	@property
	def longitude(self):
		return self.longitude

	@property
	def longitude_err(self):
		return self.clongitude_err

	@property
	def altitude(self):
		return self.caltitude

	@property
	def altitude_err(self):
		return self.caltitude_err

	@property
	def track(self):
		return self.ctrack

	@property
	def track_err(self):
		return self.ctrack_err

	@property
	def speed(self):
		return self.cspeed

	@property
	def speed_err(self):
		return self.cspeed_err

	@property
	def climb(self):
		return self.cclimb

	@property
	def climb_err(self):
		return self.cclimb_err

	@property
	def time(self):
		return self.ctime

	@property
	def position(self):
		return { "latitude" : self.clatitude, "latitude_error" : self.clatitude_err, 
				"longitude" : self.clongitude, "longitude_error" : self.clongitude_err, 
				"altitude" : self.caltitude, "altitude_error" : self.caltitude_err }

	@property
	def velocity(self):
		return { "track" : self.ctrack, "track_error" : self.ctrack_err, 
				"speed" : self.cspeed, "speed_error" : self.cspeed_err, 
				"climb" : self.cclimb, "climb_error" : self.cclimb_err }
