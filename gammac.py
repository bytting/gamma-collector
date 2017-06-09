#!/usr/bin/python2
#
# Terminal client for detector controller
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

from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol
from twisted.python import log
import sys, argparse, json

import gc_proto as proto

log.startLogging(sys.stdout)

class GammaClient(DatagramProtocol):

	def __init__(self):
	
		parser = argparse.ArgumentParser()
		parser.add_argument("mode", help="Possible values are: config, start, stop, dump")
		parser.add_argument("ip", help="IP address of remote node")
		args = parser.parse_args()
		self.mode = args.mode
		self.ip = args.ip
	
	def startProtocol(self):
			
		self.transport.connect(self.ip, 9999)
        
		if self.mode == 'config':			
			self.transport.write(b'{"command":"detector_config", "arguments":{"detector_type":"osprey", "voltage":775, "coarse_gain":1.0, "fine_gain":1.375, "num_channels":1024, "lld":3, "uld":110}}')
			sys.exit()
		elif self.mode == 'start':			
			self.transport.write(b'{"command":"start_session", "arguments":{"session_name":"Session 1", "livetime":2}}')
			sys.exit()
		elif self.mode == 'stop':			
			self.transport.write(b'{"command":"stop_session", "arguments":{}}')
			sys.exit()
		elif self.mode == 'dump':			
			self.transport.write(b'{"command":"dump_session", "arguments":{}}')
		else:
			log('Invalid options')
			sys.exit()

	def datagramReceived(self, data, addr):	
		
		msg = json.loads(data)
		print("Received %s from %s" % (msg, addr))
	
	def connectionRefused(self):		
	
		print("No server listening")
		sys.exit()

reactor.listenUDP(0, GammaClient())
reactor.run()
