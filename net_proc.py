from multiprocessing import Process
from utils import *
from proto import *
import struct, json, socket, select, sys, os, logging

HOST = ''
PORT = 7000

class NetProc(Process):

    def __init__(self, fd):
        Process.__init__(self)
        self.fd = fd
        setblocking(self.fd, 0)
        self._running = False
        self.conn = None
        self.addr = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(0)
        self.buffer = ''
        try:
            self.sock.bind((HOST, PORT))
        except socket.error as err:
            logging.error('network: bind failed')

        self.sock.listen(5)
        logging.info('network: service listening')

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
                    netstring = struct.pack("!I", len(data))
                    netstring += data
                    self.conn.send(netstring)
                    if msg.command == 'close_ok':
                        self._running = False
                else:
                    data = s.recv(1024)
                    if not data:
                        inputs.remove(s)
                        s.close()
                        s = None
                    else:
                        self.buffer += data
                        self.dispatch_msg()

        if self.conn is not None:
            self.conn.close()
        if self.sock is not None:
            self.sock.close()
        logging.info('network: terminating')

    def dispatch_msg(self):
        while True:
            if len(self.buffer) < 4:
                logging.info('network: buffer < 4')
                return
            msglen = struct.unpack("!I", self.buffer[0:4])[0]
            if len(self.buffer) < msglen+4:
                logging.info('network: buffer not ready')
                return
            jmsg = json.loads(self.buffer[4:4+msglen])
            msg = Message(**jmsg)
            logging.info('network: dispatching command: ' + msg.command)
            self.fd.send(msg)
            self.buffer = self.buffer[4+msglen:]

    def is_running(self):
        return self._running
