#!/usr/bin/env bash

# Wait a while
sleep 5

# Configure detector interface
ip addr add 10.0.1.10/24 broadcast 10.0.1.255 dev eth1

# Start GPS service
gpsd /dev/ttyUSB0

# Wait a while
sleep 5

# Run burn
/usr/bin/env python2 ./burn
