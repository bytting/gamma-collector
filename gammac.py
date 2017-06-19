#!/usr/bin/env python2
#
# Terminal client for gamma measurements
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

import sys, signal, socket, argparse, json

exit_dump = False

def signalHandler(signal, frame):

    global exit_dump
    exit_dump = True

def handleOneResponse(skt, timeout, bufsiz):

    skt.settimeout(timeout)

    try:
        data, server = skt.recvfrom(bufsiz)
        print("received %s" % json.loads(data.decode("utf-8")))

    except socket.timeout:
        print("Timeout waiting for response")

    except socket.error as err:
        print("Interrupted")

def handleResponses(skt, bufsiz):

    global exit_dump

    while not exit_dump:
        try:
            data, server = skt.recvfrom(bufsiz)
            print("received %s" % json.loads(data.decode("utf-8")))

        except socket.error as err:
            pass

def main():

    signal.signal(signal.SIGINT, signalHandler)

    parser = argparse.ArgumentParser()
    parser.add_argument('mode', help = "Possible values are: config, start, stop, dump")
    parser.add_argument('--ip', default = '127.0.0.1:9999', help = "IP address and port of remote peer. Default 127.0.0.1:9999")
    parser.add_argument('--timeout', type = int, default = 5, help = "Receive timeout for responses in seconds. Default 5")
    parser.add_argument('--buffersize', type = int, default = 8192, help = "Size of response buffer in bytes. Default 8192")
    args = parser.parse_args()

    ip, sep, port = args.ip.partition(':')
    port = 9999 if not port else int(port)
    address = (ip, port)

    skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        if args.mode == 'config':
            msg = {
                'command': "detector_config",
                'detector_type': "osprey",
                'voltage': 775,
                'coarse_gain': 1.0,
                'fine_gain': 1.375,
                'num_channels': 1024,
                'lld': 3,
                'uld': 110
            }
            nbytes = skt.sendto(bytes(json.dumps(msg)), address)
            handleOneResponse(skt, 30, args.buffersize)

        elif args.mode == 'start':
            msg = { 'command': "start_session", 'session_name': "Session 1", 'livetime': 2 }
            nbytes = skt.sendto(bytes(json.dumps(msg)), address)
            handleOneResponse(skt, args.timeout, args.buffersize)

        elif args.mode == 'stop':
            msg = { 'command': "stop_session" }
            nbytes = skt.sendto(bytes(json.dumps(msg)), address)
            handleOneResponse(skt, args.timeout, args.buffersize)

        elif args.mode == 'dump':
            msg = { 'command': "dump_session" }
            nbytes = skt.sendto(bytes(json.dumps(msg)), address)
            handleResponses(skt, args.buffersize)

        elif args.mode == 'status':
            msg = { 'command': "get_status" }
            nbytes = skt.sendto(bytes(json.dumps(msg)), address)
            handleOneResponse(skt, args.timeout, args.buffersize)

        else:
            print("Invalid options")

    finally:
        skt.close()

if __name__ == "__main__":
    main()

