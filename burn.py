#!/usr/bin/env python2
# Daemon controlling a Canberra Osprey gamma detector and a Globalsat G-Star IV GPS device.
# Copyright (C) 2016  Dag Robole
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

import time
import os
import sys
import socket

from twisted.internet import reactor
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver

from gps_controller import GpsController
from spectrum_controller import SpectrumController

class NetController(LineReceiver):

    def __init__(self, spectrumController, gpsController):
        self.sc = spectrumController
        self.gc = gpsController

    def lineReceived(self, line):
        if line == 'start':
            self.sendLine('server: running session')

            self.sc.stabilize_probe(700, 1, 1)
            self.sc.create_session(2, 0, 8)
            self.sc.run_session()
            #cmd = json.load(line)

            self.sendLine('server: session done')

    def connectionMade(self):
        print 'connection made'
        self.gc.start()

    def connectionLost(self, reason):
        print 'connection lost', reason
        self.gc.stopController()

class NetFactory(Factory):

    def __init__(self, spectrumController, gpsController):
        self.sc = spectrumController
        self.gc = gpsController

    def buildProtocol(self, addr):
        return NetController(self.sc, self.gc)

def main():

    if not os.geteuid() == 0:
        sys.exit('Script must be run as root')

    if len(sys.argv) < 2:
        sys.exit("Missing arguments")

    iface = sys.argv[-1]

    try:
        socket.gethostbyaddr("10.0.1.10")
        print "IP 10.0.1.10 already alive"
    except socket.herror:
        ret = os.system("ip addr add 10.0.1.10/24 broadcast 10.0.1.255 dev " + iface)
        if ret != 0:
            sys.exit("Unable to set ip address for detector")
        else:
            print "Interface " + iface + " configured successfully"

    sc = SpectrumController()
    gc = GpsController()

    LineReceiver.MAX_LENGTH = 1024*1024
    reactor.listenTCP(7000, NetFactory(sc, gc))
    reactor.run()

if __name__ == '__main__':
    main()
