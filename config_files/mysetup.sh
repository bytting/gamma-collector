#!/bin/bash

# Wait a while
sleep 8

# Set up detector interface
ip addr add 10.0.1.10/24 broadcast 10.0.1.255 dev eth1

# Start GPS service
gpsd /dev/ttyUSB0

# Wait a while
sleep 5

# Start burn
nohup /home/drb/dev/py/burn/burn.py &
