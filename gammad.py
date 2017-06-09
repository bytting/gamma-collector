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

import sys, json, threading, importlib

from twisted.internet import reactor, threads, defer, task
from twisted.internet.protocol import DatagramProtocol
from twisted.python import log

import gc_gps as gps

log.startLogging(sys.stdout)

class SessionState: Ready, Busy = range(2)

class SpectrumState: Ready, Busy = range(2)
	
class DetectorState: Cold, Warm = range(2)
	
class Controller(DatagramProtocol):

	def __init__(self):
		
		self.addr = None		
		self.session_args = None
		self.session_loop = None
		self.session_state = SessionState.Ready
		self.spectrum_state = SpectrumState.Ready
		self.detector_state = DetectorState.Cold
		
		self.gps_stop = threading.Event() # Event used to notify gps thread
		self.gps = gps.GpsThread(self.gps_stop) # Create the gps thread
		
		self.plugin = None

	def sendResponse(self, state, message):
		
		resp = '{"command":"%s", arguments:{"message":"%s"}' % (state, message)
		self.transport.write(bytes(resp), self.addr)

	def loadPlugin(self, name):
				
		module_name = "plugin_" + name
		return sys.modules[module_name] if module_name in sys.modules else importlib.import_module(module_name)
		
	def startProtocol(self):		
		
		self.gps.start()
		log.msg('GPS thread started')
	
	def stopProtocol(self):
		
		self.gps_stop.set()
		self.gps.join()
		log.msg('GPS thread stopped')        
		
	def datagramReceived(self, data, addr):
		
		log.msg("Received %s from %s" % (data, addr))
		self.addr = addr

		try:					
			p = json.loads(data)
			cmd, args = p["command"], p["arguments"]		
			
			if cmd == 'detector_config':
				self.plugin = self.loadPlugin(args["detector_type"])
				self.plugin.initializeDetector(args)
				self.detector_state = DetectorState.Warm
				self.sendResponse("success", "Detector initialized")

			elif cmd == 'start_session':
				self.initializeSession(args)
				self.startSession(args)
				self.sendResponse("success", "Session started")

			elif cmd == 'stop_session':
				self.stopSession(args)
				self.finalizeSession(args)
				self.sendResponse("success", "Session stopped")

			elif cmd == 'dump_session':
				self.sendResponse("success", "Registered for dump")

			else:
				raise Exception("Unknown command: " % cmd)

		except Exception as e:
			log.msg(str(e))
			self.sendResponse("error", str(e))

	def initializeSession(self, args):
				
		log.msg("Initializing session " + args["session_name"])
		# create database etc.
		
	def finalizeSession(self, args):
		
		log.msg("Finalizing session " + args["session_name"])
		# close database etc.
		
	def startSession(self, args):
		
		if self.session_state == SessionState.Ready:
			self.session_state = SessionState.Busy
			self.session_args = args
			self.session_loop = task.LoopingCall(self.sessionTick)
			self.session_loop.start(0.05)	

	def sessionTick(self):
		
		if self.spectrum_state == SpectrumState.Ready:
			d = threads.deferToThread(self.startSpectrum)
			d.addCallbacks(self.handleSpectrumSuccess, self.handleSpectrumFailure)
			self.spectrum_state = SpectrumState.Busy
			
	def stopSession(self, args):
		
		self.session_loop.stop()
		self.session_state = SessionState.Ready

	def startSpectrum(self):
		
		position = self.gps.position
		velocity = self.gps.velocity
		time = self.gps.time
		
		msg = self.plugin.acquireSpectrum(self.session_args)
		
		msg.arguments.update(position)
		msg.arguments.update(velocity)
		msg.arguments["time"] = time

		return msg

	def handleSpectrumSuccess(self, msg):
		
		self.transport.write(bytes(msg), self.addr)
		self.spectrum_state = SpectrumState.Ready

	def handleSpectrumFailure(self, err):
		
		self.sendResponse("error", err.getErrorMessage())
		self.spectrum_state = SpectrumState.Ready

reactor.listenUDP(9999, Controller())
reactor.run()

