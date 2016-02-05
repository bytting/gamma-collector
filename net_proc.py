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

from multiprocessing import Process
from helpers import *
from proto import *
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
        self.conn, self.addr = None, None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(0)
        self.buffer = ''
        try:
            self.sock.bind((HOST, PORT))
        except socket.error as e:
            logging.error('network: bind failed: ' + os.strerror(e.errno))

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

            for s in readable: # Handle reads

                if s is self.sock: # Incoming connection on listening socket
                    # We only allow one connection at a time (TODO)
                    self.conn, self.addr = s.accept()
                    self.conn.setblocking(0)
                    inputs.append(self.conn)
                    self.buffer = ''
                    logging.info('network: connection received from ' + self.addr[0])

                elif s is self.fd: # Incoming message from main controller
                    msg = s.recv()
                    data = json.dumps(msg.__dict__) # Convert object to json
                    netstring = struct.pack("!I", len(data)) + data # Serialize json
                    totlen, currlen = len(netstring), 0
                    while True:
                        # Send complete packet
                        l = self.conn.send(netstring[currlen:])
                        if l == 0:
                            inputs.remove(self.conn)
                            self.conn.close()
                            logging.info('network: connection broken from ' + self.addr[0])
                            break
                        currlen += l
                        if currlen >= totlen:
                            break
                    if msg.command == 'close_ok': # main controller is closing
                        self._running = False

                else: # Incoming data from existing connection
                    try:
                        data = s.recv(1024)
                    except socket.error as e:
                        if e.errno == errno.ECONNRESET:
                            inputs.remove(s)
                            s.close()
                        logging.error('network: ' + self.addr[0] + ': ' + os.strerror(e.errno))
                        continue
                    if not data or data == '':
                        inputs.remove(s)
                        s.close()
                        logging.error('network: connection lost')
                        continue
                    else:
                        # Data successfully received, store in buffer
                        self.buffer += data
                        self.dispatch_msg()

        # Close active connections
        if self.conn is not None:
            self.conn.close()
        if self.sock is not None:
            self.sock.close()

        logging.info('network: terminating')

    def dispatch_msg(self):
        """
        Convert received data to messages and pass them on to main controller
        """
        while True:
            if len(self.buffer) < 4:
                return
            # Extract message length
            msglen = struct.unpack("!I", self.buffer[0:4])[0]
            if len(self.buffer) < msglen+4:
                logging.info('network: buffer not ready')
                return
            # Extract rest of message and convert to object
            jmsg = json.loads(self.buffer[4:4+msglen])
            msg = Message(**jmsg)
            # Pass message to main controller
            self.fd.send(msg)
            # Update buffer
            self.buffer = self.buffer[4+msglen:]

    def is_running(self):
        """
        Return wether the net process is still running
        """
        return self._running
