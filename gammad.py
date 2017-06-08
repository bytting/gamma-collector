#!/usr/bin/python2
#
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

from __future__ import print_function

import sys, json, threading

from twisted.internet import reactor, threads, defer, task
from twisted.internet.protocol import DatagramProtocol
from twisted.python import log

import gc_gps as gps, gc_proto as proto

log.startLogging(sys.stdout)

class State:
	
	Ready, Busy = range(2)

class Controller(DatagramProtocol):

	def __init__(self):
		
		self.addr = None		
		self.sessionArgs = None
		self.sessionLoop = None
		self.sessionState = State.Ready
		self.spectrumState = State.Ready
		
		self.gpsStop = threading.Event() # Event used to notify gps thread
		self.gpsClient = gps.GpsThread(self.gpsStop) # Create the gps thread
		
		self.plugin = self.loadPlugin("osprey")
		log.msg('Osprey plugin loaded')

	def loadPlugin(self, name):
		
		return __import__("plugin_%s" % name)
		
	def startProtocol(self):		
		
		self.gpsClient.start() # Start the gps
		log.msg('GPS client started')
	
	def stopProtocol(self):
		
		self.gpsStop.set()
		self.gpsClient.join()
		log.msg('GPS client stopped')        
		
	def datagramReceived(self, data, addr):
				
		log.msg("Received %s from %s" % (data, addr))

		self.addr = addr
		p = json.loads(data)
		cmd, args = p["command"], p["arguments"]		
		
		if cmd == 'detector_config':
			ret, err = self.plugin.initializeDetector(args)
			if ret == False:
				log.msg('Detector configuration failed: ' + err)
			else:
				log.msg('Detector configured')

		elif cmd == 'start_session':
			self.initializeSession(args)
			self.startSession(args)
			log.msg('Session started')

		elif cmd == 'stop_session':
			self.stopSession(args)
			self.finalizeSession(args)
			log.msg('Session stopped')

		elif cmd == 'dump_session':
			pass

		else:
			log.msg("Unknown command " % cmd)

	def initializeSession(self, args):
				
		log.msg("Initializing session " + args["session_name"])
		# create database etc.
		
	def finalizeSession(self, args):
		
		log.msg("Finalizing session " + args["session_name"])
		# close database etc.
		
	def startSession(self, args):
		
		if self.sessionState == State.Ready:
			self.sessionState = State.Busy
			self.sessionArgs = args
			self.sessionLoop = task.LoopingCall(self.sessionTick)
			self.sessionLoop.start(0.05)	

	def sessionTick(self):
		
		if self.spectrumState == State.Ready:
			d = threads.deferToThread(self.startSpectrum)
			d.addCallback(self.handleSpectrum)
			self.spectrumState = State.Busy
			
	def stopSession(self, args):
		
		self.sessionLoop.stop()
		self.sessionState = State.Ready

	def startSpectrum(self):
		
		log.msg('Starting spectrum...')
		lat = self.gpsClient.latitude
		lon = self.gpsClient.longitude
		alt = self.gpsClient.altitude		
		
		msg = self.plugin.acquireSpectrum(self.sessionArgs)

		if msg["command"] != "error":		
			msg.arguments["latitude"] = lat
			msg.arguments["longitude"] = lon
			msg.arguments["altitude"] = alt
		
		return msg

	def handleSpectrum(self, msg):
		
		if msg["command"] == "error":
			log.msg('Spectrum error: ' + msg.arguments["message"])
		
		self.transport.write(bytes(msg), self.addr)
		self.spectrumState = State.Ready

reactor.listenUDP(9999, Controller())
reactor.run()

