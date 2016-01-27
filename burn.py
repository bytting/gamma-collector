#!/usr/bin/env python2

from __future__ import print_function
from proto import *
from gps_proc import GpsProc
from spec_proc import SpecProc
from net_proc import NetProc
from multiprocessing import Pipe
from datetime import datetime
from utils import *
import time, sys, os, select, logging

class Burn():

    def __init__(self):
        self.running = False

        #fdg_pass, self.fdg = Pipe()
        #fds_pass, self.fds = Pipe()
        fdn_pass, self.fdn = Pipe()

        #setblocking(self.fdg, 0)
        #setblocking(self.fds, 0)
        setblocking(self.fdn, 0)

        #self.g = GpsProc(fdg_pass)
        #self.s = SpecProc(fds_pass)
        self.n = NetProc(fdn_pass)

        #self.g.start()
        #self.s.start()
        self.n.start()

        #fdg_pass.close()
        #fds_pass.close()
        fdn_pass.close()

    def run(self):
        self.running = True

        #logging.info('main: warming up services')
        #time.sleep(4)

        while self.running:
            readable, _, exceptional = select.select([self.fdn], [], [self.fdn])
            for s in readable:
                msg = s.recv()
                if s is self.fdn:
                    self.dispatch_net_msg(msg)

    def dispatch_net_msg(self, msg):
        if not msg:
            return
        if msg.command.startswith('ping'):
            msg.command = 'pong'
            self.fdn.send(msg)
        if msg.command.startswith('close'):
            msg.command = 'closing'
            self.fdn.send(msg)
            self.running = False
        if msg.command.startswith('new_session'):
            msg.command = 'session_info'
            self.fdn.send(msg)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        #self.fdg.close()
        #self.fds.close()
        self.fdn.close()

        #self.g.join()
        #self.s.join()
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
