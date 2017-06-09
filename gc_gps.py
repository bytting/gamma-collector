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
		self.lat = 0
		self.lat_err = 0
		self.lon = 0
		self.lon_err = 0
		self.alt = 0
		self.alt_err = 0
		self.track = 0
		self.track_err = 0
		self.speed = 0
		self.speed_err = 0
		self.climb = 0
		self.climb_err = 0
		self.time = ''

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
					self.lat = self.gpsd.fix.latitude
				if not math.isnan(self.gpsd.fix.epx):
					self.lat_err = self.gpsd.fix.epx
				if not math.isnan(self.gpsd.fix.longitude):
					self.lon = self.gpsd.fix.longitude
				if not math.isnan(self.gpsd.fix.epy):
					self.lon_err = self.gpsd.fix.epy
				if not math.isnan(self.gpsd.fix.altitude):
					self.alt = self.gpsd.fix.altitude
				if not math.isnan(self.gpsd.fix.epv):
					self.alt_err = self.gpsd.fix.epv
				if not math.isnan(self.gpsd.fix.track):
					self.track = self.gpsd.fix.track
				if not math.isnan(self.gpsd.fix.epd):
					self.track_err = self.gpsd.fix.epd
				if not math.isnan(self.gpsd.fix.speed):
					self.speed = self.gpsd.fix.speed
				if not math.isnan(self.gpsd.fix.eps):
					self.speed_err = self.gpsd.fix.eps
				if not math.isnan(self.gpsd.fix.climb):
					self.climb = self.gpsd.fix.climb
				if not math.isnan(self.gpsd.fix.epc):
					self.climb_err = self.gpsd.fix.epc
				if self.gpsd.utc != None and self.gpsd.utc != '':
					self.time = self.gpsd.utc

	@property
	def lat(self):
		return self.lat

	@property
	def lat_err(self):
		return self.epx

	@property
	def lon(self):
		return self.lon

	@property
	def lon_err(self):
		return self.epy

	@property
	def alt(self):
		return self.alt

	@property
	def alt_err(self):
		return self.alt_err

	@property
	def track(self):
		return self.track

	@property
	def track_err(self):
		return self.track_err

	@property
	def speed(self):
		return self.speed

	@property
	def speed_err(self):
		return self.speed_err

	@property
	def climb(self):
		return self.climb

	@property
	def climb_err(self):
		return self.climb_err

	@property
	def time(self):
		return self.last_time

	@property
	def position(self):
		return { "latitude" : self.lat, "latitude_error" : self.lat_err, 
				"longitude" : self.lon, "longitude_error" : self.lon_err, 
				"altitude" : self.alt, "altitude_error" : self.alt_err }

	@property
	def velocity(self):
		return { "track" : self.track, "track_error" : self.track_err, 
				"speed" : self.speed, "speed_error" : self.speed_err, 
				"climb" : self.climb, "climb_error" : self.climb_err }
