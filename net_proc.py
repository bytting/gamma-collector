from multiprocessing import Process
from proto import *
import socket
import select
import sys
import os
import fcntl
import logging

HOST = ''
PORT = 7000

class NetProc(Process):

    def __init__(self, fd):

        Process.__init__(self)
        self.fd = fd
        flags = fcntl.fcntl(self.fd, fcntl.F_GETFL)
        fcntl.fcntl(self.fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        self._running = True
        self.conn = None
        self.addr = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(0)
        try:
            self.sock.bind((HOST, PORT))
        except socket.error as err:
            logging.error('network: bind failed')

        self.sock.listen(5)
        logging.info('network: server listening')

    def run(self):

        logging.info('network: starting service')
        inputs = [self.fd, self.sock]

        while(self._running):

            readable, _, _ = select.select(inputs, [], [])

            for s in readable:
                if s is self.sock:
                    self.conn, self.addr = s.accept()
                    self.conn.setblocking(0)
                    inputs.append(self.conn)
                    logging.info('connection received')
                elif s is self.fd:
                    data = s.recv()
                    self.conn.send(data)
                    if data.startswith('closing'):
                        self._running = False
                else:
                    data = s.recv(1024)
                    self.fd.send(data)

                #inputs.remove(s)
                #s.close()
                #del msgq[s]
                #s = None

        if self.conn is not None:
            self.conn.close()
        self.sock.close()
        logging.info('network: service exiting')

    def is_running(self):
        return self._running
