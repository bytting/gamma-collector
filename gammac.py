#!/usr/bin/python2
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

def signal_handler(signal, frame):

    global exit_dump
    exit_dump = True

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('mode', help = "Possible values are: config, start, stop, dump")
    parser.add_argument('ip', help = "IP address of remote node")
    args = parser.parse_args()

    skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (args.ip, 9999)

    try:
        if args.mode == 'config':
            msg = {
                "command": "detector_config",
                "detector_type": "osprey",
                "voltage": 775,
                "coarse_gain": 1.0,
                "fine_gain": 1.375,
                "num_channels": 1024,
                "lld": 3,
                "uld": 110
            }
            sent = skt.sendto(bytes(json.dumps(msg)), server_address)
            sys.exit()

        elif args.mode == 'start':
            msg = { "command": "start_session", "session_name": "Session 1", "livetime": 2 }
            sent = skt.sendto(bytes(json.dumps(msg)), server_address)
            sys.exit()

        elif args.mode == 'stop':
            msg = { "command": "stop_session" }
            sent = skt.sendto(bytes(json.dumps(msg)), server_address)
            sys.exit()

        elif args.mode == 'dump':
            msg = { "command": "dump_session" }
            sent = skt.sendto(bytes(json.dumps(msg)), server_address)

        else:
            print("Invalid options")
            sys.exit()

        while not exit_dump:
            try:
                data, server = skt.recvfrom(8192)
                print("received %s" % json.loads(data.decode("utf-8")))

            except KeyboardInterrupt:
                global exit_dump
                exit_dump = True

    finally:
        skt.close()

if __name__ == "__main__":
    main()

