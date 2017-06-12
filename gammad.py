#!/usr/bin/env python2
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
from gc_exceptions import ProtocolError

log.startLogging(sys.stdout)

class SessionState: Ready, Busy = range(2)

class SpectrumState: Ready, Busy = range(2)

class DetectorState: Cold, Warm = range(2)

class Controller(DatagramProtocol):

	def __init__(self):

		self.client_address = None
		self.session_args = None
		self.session_loop = None
		self.session_state = SessionState.Ready
		self.spectrum_state = SpectrumState.Ready
		self.spectrum_index = 0
		self.spectrum_failures = 0
		self.detector_state = DetectorState.Cold

		self.gps_stop = threading.Event() # Event used to notify gps thread
		self.gps = gps.GpsThread(self.gps_stop) # Create the gps thread

		self.plugin = None

	def sendResponse(self, status_command, status_message):

		log.msg("Response: %s: %s" % (status_command, status_message))

		if self.client_address is not None:
			msg = {"command":"%s" % status_command, "message":"%s" % status_message}
			self.transport.write(bytes(json.dumps(msg)), self.client_address)

	def loadPlugin(self, name):

		modname = 'plugin_' + name
		return sys.modules[modname] if modname in sys.modules else importlib.import_module(modname)

	def startProtocol(self):

		self.gps.start()
		log.msg('GPS thread started')

	def stopProtocol(self):

		self.gps_stop.set()
		self.gps.join()
		log.msg('GPS thread stopped')

	def datagramReceived(self, data, addr):

		self.client_address = addr

		try:
			msg = json.loads(data.decode("utf-8"))

			log.msg("Received %s from %s" % (msg, self.client_address)) # FIXME

			if not 'command' in msg:
				raise ProtocolError('error', "Invalid message");

			cmd = msg['command']

			if cmd == 'detector_config':
				if self.session_state == SessionState.Busy:
					raise ProtocolError('detector_config_error', "Detector config failed, session is active")
				if not 'detector_type' in msg:
					raise ProtocolError('detector_config_error', "Detector config failed, detector_type missing")					

				self.plugin = self.loadPlugin(msg['detector_type'])
				self.plugin.initializeDetector(msg)
				self.detector_state = DetectorState.Warm
				#self.sendResponse('detector_config_success', "Detector initialized")
                                msg["command"] = 'detector_config_success'
                                self.transport.write(bytes(json.dumps(msg)), self.client_address)

			elif cmd == 'start_session':
				if self.session_state == SessionState.Busy:
					raise ProtocolError('start_session_error', "Session is already active")

				self.initializeSession(msg)
				self.startSession(msg)
				self.spectrum_index = 0
				self.spectrum_failures = 0
                                msg["command"] = 'start_session_success'
                                self.transport.write(bytes(json.dumps(msg)), self.client_address)

			elif cmd == 'stop_session':
				if self.session_state == SessionState.Ready:
					raise ProtocolError('stop_session_error', "No session is running")

				self.stopSession(msg)
				self.finalizeSession(msg)
				self.sendResponse('stop_session_success', "Session stopped")

			elif cmd == 'dump_session':
				if self.session_state == SessionState.Ready:
					raise ProtocolError('dump_session_error', "No session is running")

				self.sendResponse('dump_session_success', "Registered for dump")

			else: raise Exception("Unknown command: %s" % cmd)

		except ProtocolError as pe:
			self.sendResponse(pe.command, pe.message)

		except Exception as e:
			self.sendResponse('error', str(e))

	def initializeSession(self, msg):

		log.msg("Initializing session " + msg['session_name'])
		# create database etc.

	def finalizeSession(self, msg):

		log.msg("Finalizing session")
		# close database etc.

	def startSession(self, msg):

		self.session_state = SessionState.Busy
		self.session_args = msg
		self.session_loop = task.LoopingCall(self.sessionTick)
		self.session_loop.start(0.05)

	def stopSession(self, msg):

		self.session_loop.stop()
		self.session_state = SessionState.Ready

	def sessionTick(self):

		if self.spectrum_state == SpectrumState.Ready:
			d = threads.deferToThread(self.startSpectrum)
			d.addCallbacks(self.handleSpectrumSuccess, self.handleSpectrumFailure)
			self.spectrum_state = SpectrumState.Busy

	def startSpectrum(self):

		position = self.gps.position
		velocity = self.gps.velocity
		time = self.gps.time

		msg = self.plugin.acquireSpectrum(self.session_args)

		msg.update(position)
		msg.update(velocity)
		msg['time'] = time

		return msg

	def handleSpectrumSuccess(self, msg):

		log.msg("Spectrum %d ready" % self.spectrum_index) # FIXME

		msg['index'] = self.spectrum_index
		self.spectrum_index = self.spectrum_index + 1

		if self.client_address is not None:
			self.transport.write(bytes(json.dumps(msg)), self.client_address)

		self.spectrum_state = SpectrumState.Ready

	def handleSpectrumFailure(self, err):

		self.sendResponse('error', err.getErrorMessage())

		self.spectrum_failures = self.spectrum_failures + 1
		if self.spectrum_failures >= 3:
			stopSession({})
			self.sendResponse('error', "Acquiring spectrum has failed 3 times, stopping session")

		self.spectrum_state = SpectrumState.Ready

reactor.listenUDP(9999, Controller())
reactor.run()
