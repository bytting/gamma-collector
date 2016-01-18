#!/usr/bin/env python2

from __future__ import print_function
from multiprocessing import Pipe
from proto import *
from gps_proc import GpsProc
from spec_proc import SpecProc
from net_proc import NetProc
from datetime import datetime
import time, sys, os, fcntl, select, atexit, logging

class Burn():

    def __init__(self):

        #fdg_pass, self.fdg = Pipe()
        #fds_pass, self.fds = Pipe()
        fdn_pass, self.fdn = Pipe()

        #flags = fcntl.fcntl(self.fdg, fcntl.F_GETFL)
        #fcntl.fcntl(self.fdg, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        #flags = fcntl.fcntl(self.fds, fcntl.F_GETFL)
        #fcntl.fcntl(self.fds, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        flags = fcntl.fcntl(self.fdn, fcntl.F_GETFL)
        fcntl.fcntl(self.fdn, fcntl.F_SETFL, flags | os.O_NONBLOCK)

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

        #logging.info('main: warming up services')
        #time.sleep(4)

        running = True
        while running:
            readable, _, exceptional = select.select([self.fdn], [], [self.fdn])
            for s in readable:
                data = s.recv()
                if data:
                    s.send(data.upper())
                    if data.startswith('close'):
                        s.send('closing')
                        running = False

    @atexit.register
    def terminate(self):
        logging.info('main: terminating')

        #self.fdg.close()
        #self.fds.close()
        self.fdn.close()

        #self.g.join()
        #self.s.join()
        self.n.join()

if __name__ == '__main__':
    #try:
    #logpath = os.path.expanduser("/var/log/")
    #now = datetime.now()
    #logfile = logpath + 'burn-' + now.strftime("%Y%m%d_%H%M%S") + '.log'
    #logging.basicConfig(filename=logfile, level=logging.DEBUG)
    logging.basicConfig(filename='burn.log', level=logging.DEBUG)
    Burn().run()
    #except Exception as e:
    #logging.error('main: exception: ' + str(e))
