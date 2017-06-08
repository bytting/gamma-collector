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
		self.last_lat = 0
		self.last_epx = 0
		self.last_lon = 0
		self.last_epy = 0
		self.last_alt = 0
		self.last_epv = 0
		self.last_speed = 0
		self.last_eps = 0
		self.last_time = ''

	def run(self):
		"""
		Description:
			Entry point for the gps thread
		"""		

		# Process any buffered gps signals every .3 seconds
		while not self._stopped.wait(0.3):

			# Update our last measurement until buffer is empty
			while self.gpsd.waiting():
				self.gpsd.next()
				if not math.isnan(self.gpsd.fix.latitude):
					self.last_lat = self.gpsd.fix.latitude
				if not math.isnan(self.gpsd.fix.epx):
					self.last_epx = self.gpsd.fix.epx
				if not math.isnan(self.gpsd.fix.longitude):
					self.last_lon = self.gpsd.fix.longitude
				if not math.isnan(self.gpsd.fix.epy):
					self.last_epy = self.gpsd.fix.epy
				if not math.isnan(self.gpsd.fix.altitude):
					self.last_alt = self.gpsd.fix.altitude
				if not math.isnan(self.gpsd.fix.epv):
					self.last_epv = self.gpsd.fix.epv
				if not math.isnan(self.gpsd.fix.speed):
					self.last_speed = self.gpsd.fix.speed
				if not math.isnan(self.gpsd.fix.eps):
					self.last_eps = self.gpsd.fix.eps
				if self.gpsd.utc != None and self.gpsd.utc != '':
					self.last_time = self.gpsd.utc

	@property
	def latitude(self):
		return self.last_lat

	@property
	def epx(self):
		return self.last_epx

	@property
	def longitude(self):
		return self.last_lon

	@property
	def epy(self):
		return self.last_epy

	@property
	def altitude(self):
		return self.last_alt

	@property
	def epv(self):
		return self.last_epv

	@property
	def speed(self):
		return self.last_speed

	@property
	def eps(self):
		return self.last_eps

	@property
	def time(self):
		return self.last_time
