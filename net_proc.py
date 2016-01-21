from multiprocessing import Process
from proto import *
import json, socket, select, sys, os, fcntl, logging

HOST = ''
PORT = 7000

class NetProc(Process):

    def __init__(self, fd):
        Process.__init__(self)
        self.fd = fd
        flags = fcntl.fcntl(self.fd, fcntl.F_GETFL)
        fcntl.fcntl(self.fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        self._running = False
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
        self._running = True
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
                    msg = s.recv()
                    data = json.dumps(msg.__dict__)
                    logging.info('network sending: ' + data)
                    self.conn.send(data + '\n')
                    if msg.command.startswith('closing'):
                        self._running = False
                else:
                    data = s.recv(1024)
                    if not data:
                        inputs.remove(s)
                        s.close()
                        s = None
                    else:
                        logging.info('received: ' + data)
                        jmsg = json.loads(data)
                        msg = Request(**jmsg)
                        self.fd.send(msg)

        if self.conn is not None:
            self.conn.close()
        if self.sock is not None:
            self.sock.close()
        logging.info('network: terminating')

    def is_running(self):
        return self._running
