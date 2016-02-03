#!/bin/bash

ip addr add 10.0.1.10/24 broadcast 10.0.1.255 dev eth1
gpsd /dev/ttyUSB0
