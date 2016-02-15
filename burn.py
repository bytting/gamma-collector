#!/usr/bin/env python2
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

from __future__ import print_function
from proto import *
from spec_proc import SpecProc
from net_proc import NetProc
from multiprocessing import Pipe
from datetime import datetime
from helpers import *
import time, sys, os, select, logging

class Burn():

    def __init__(self):
        self.running = False
        self.session_dir = ''

        fds_pass, self.fds = Pipe()
        fdn_pass, self.fdn = Pipe()

        setblocking(self.fds, 0)
        setblocking(self.fdn, 0)

        self.s = SpecProc(fds_pass)
        self.n = NetProc(fdn_pass)

        self.s.start()
        self.n.start()

        fds_pass.close()
        fdn_pass.close()

    def run(self):
        self.running = True

        logging.info('main: warming up services')
        time.sleep(5)

        inputs = [self.fdn, self.fds]

        while self.running:
            readable, _, _ = select.select(inputs, [], [])
            for s in readable:
                msg = s.recv()
                if s is self.fdn:
                    self.dispatch_net_msg(msg)
                elif s is self.fds:
                    self.dispatch_spec_msg(msg)

    def dispatch_net_msg(self, msg):
        if not msg:
            return
        if msg.command == 'ping':
            msg.command = 'ping_ok'
            self.fdn.send(msg)
        elif msg.command == 'close':
            self.fds.send(msg)
            msg.command = 'close_ok'
            self.fdn.send(msg)
            self.running = False
        elif msg.command == 'new_session' or msg.command == 'stop_session' or msg.command == 'set_gain':
            self.fds.send(msg)
        else:
            logging.warning('controller: unknown command: ' + msg.command)

    def dispatch_spec_msg(self, msg):
        self.fdn.send(msg)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.fds.close()
        self.fdn.close()

        self.s.join()
        self.n.join()

        logging.info('main: terminating')

if __name__ == '__main__':
    #try:
    #logpath = os.path.expanduser("/var/log/")
    #now = datetime.now()
    #logfile = logpath + 'burn-' + now.strftime("%Y%m%d_%H%M%S") + '.log'
    #logging.basicConfig(filename=logfile, level=logging.DEBUG)
    logging.basicConfig(filename='burn.log', level=logging.DEBUG)
    with Burn() as burn:
        burn.run()
    #except Exception as e:
    #logging.error('main: exception: ' + str(e))
