from multiprocessing import Process
from proto import *
import logging

class SpecProc(Process):
    def __init__(self, fd):
        Process.__init__(self)
        self.fd = fd
        self.running = False

    def run(self):
        logging.info('spec: staring service')
        self.running = True
        while(self.running):
            if self.fd.poll():
                self.dispatch(self.fd.recv())
        logging.info('spec: service exiting')

    def dispatch(self, cmd):
        if cmd.name == set_gain:
            # set gain
            self.fd.send(Command(set_gain_ok))
        elif cmd.name == ping:
            self.fd.send(Command(pong))
        elif cmd.name == close:
            # exit proc
            self.fd.send(Command(close_ok))
            self.running = False
        else:
            logging.warning('spec: unknown command')
            self.fd.send(Command(unknown))

