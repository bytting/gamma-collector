from multiprocessing import Process
from helpers import *
from proto import *
from socket import error as socket_error
import struct, json, socket, select, sys, os, logging, errno

HOST = ''
PORT = 7000

class NetProc(Process):

    def __init__(self, fd):
        """
        Initialization of the net process
        """
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
        """
        Entry point for the net process
        """
        logging.info('network: starting service')
        self._running = True
        # Prepare sockets and file descriptors
        inputs = [self.fd, self.sock]

        # Start select event loop
        while(self._running):
            readable, _, _ = select.select(inputs, [], [])

            # Handle reads
            for s in readable:

                if s is self.sock:
                    # Incoming connection on listening socket
                    # We only allow one connection at a time (TODO)
                    self.conn, self.addr = s.accept()
                    self.conn.setblocking(0)
                    inputs.append(self.conn)
                    self.buffer = ''
                    logging.info('connection received')

                elif s is self.fd:
                    # Incoming message from main controller
                    msg = s.recv()
                    data = json.dumps(msg.__dict__)
                    netstring = struct.pack("!I", len(data)) + data
                    totlen, currlen = len(netstring), 0
                    while True:
                        l = self.conn.send(netstring[currlen:])
                        if l == 0:
                            self.extinguish_conn(inputs)
                            break
                        currlen += l
                        if currlen >= totlen:
                            break

                    if msg.command == 'close_ok':
                        self._running = False

                else:
                    # Incoming data from existing connection
                    try:
                        data = s.recv(1024)
                    except socket_error as e:
                        if e.errno != errno.ECONNRESET:
                            raise
                        self.extinguish_conn(inputs)
                        continue
                    if not data or data == '':
                        self.extinguish_conn(inputs)
                        continue
                    else:
                        self.buffer += data
                        self.dispatch_msg()

        if self.conn is not None:
            self.conn.close()
        if self.sock is not None:
            self.sock.close()
        logging.info('network: terminating')

    def extinguish_conn(self, inputs):
        # Connection was lost abruptly, remove it from select descriptors and close
        inputs.remove(self.conn)
        self.conn.close()
        logging.info('network: connection lost')

    def dispatch_msg(self):
        # Convert received data to messages and pass them on to main controller
        while True:
            if len(self.buffer) < 4:
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
        # Return wether the net process is still running
        return self._running
