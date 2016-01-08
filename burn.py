#!/usr/bin/python2

import time
import os
import sys
import socket
from gps_controller import GpsController
from spectrum_controller import SpectrumController

def main():

    if not os.geteuid() == 0:
        sys.exit('Script must be run as root')

    if len(sys.argv) < 2:
        sys.exit("Missing arguments")

    iface = sys.argv[-1]

    try:
        socket.gethostbyaddr("10.0.1.10")
        print "IP 10.0.1.10 already alive"
    except socket.herror:
        ret = os.system("ip addr add 10.0.1.10/24 broadcast 10.0.1.255 dev " + iface)
        if ret != 0:
            sys.exit("Unable to set ip address for detector")
        else:
            print "Interface " + iface + " configured successfully"

    sc = SpectrumController()
    sc.stabilize_probe(700, 1, 1)
    sc.create_session(2, 0, 8)
    sc.run_session()

    #gc = GpsController()
#    try:
#        gc.start()
#        while True:
#            print gc.utc, " - ", gc.fix.latitude, " - ", gc.fix.longitude
#            time.sleep(1)
#    except KeyboardInterrupt:
#        gc.stopController()
#        print "Exiting..."
#    except:
#        gc.stopController()
#        print "Error..."

if __name__ == '__main__':
    main()
