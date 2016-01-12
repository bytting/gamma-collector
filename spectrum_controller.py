# Controller for a Canberra Osprey gamma detector
# Copyright (C) 2016  Dag Robole
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

import Utilities
from datetime import datetime
import time
import socket
import sys
import os
from struct import pack
from array import array

#Setup the Python env
Utilities.setup()

#import the Lynx device proxy and other resources
from DeviceFactory import *
from ParameterCodes import *
from CommandCodes import *
from ParameterTypes import *
from PhaData import *

class SpectrumController:

    def __init__(self):

        self.voltage = 0
        self.coarse_gain = 0
        self.fine_gain = 0
        self.acquisition_interval = 0
        self.acquisition_spacing = 0
        self.acquisition_count = 0
        self.source_dir = ""
        self.group = 1
        #Working with input 1
        self.input = 1
        #Create the interface
        self.dtb = DeviceFactory.createInstance(DeviceFactory.DeviceInterface.IDevice)
        #Open a connection to the device
        self.dtb.open("", Utilities.getLynxAddress())
        #Display the name of the dtb
        print "You are connected to: %s" % self.dtb.getParameter(ParameterCodes.Network_MachineName, 0)
        #Gain ownership
        self.dtb.lock("administrator", "password", self.input)

        self.reset_acquisition()

    def reset_acquisition(self):

        #Disable all acquisition
        Utilities.disableAcquisition(self.dtb, self.input)
        #Set the acquisition mode The Only Available Spectral in Osprey is Pha = 0
        self.dtb.setParameter(ParameterCodes.Input_Mode, 0, self.input)
        #Setup presets
        self.dtb.setParameter(ParameterCodes.Preset_Options, 1, self.input)
        #Clear data and time
        self.dtb.control(CommandCodes.Clear, self.input)

    def stabilize_probe(self, voltage, coarse_gain, fine_gain):

        self.voltage = voltage
        self.coarse_gain = coarse_gain
        self.fine_gain = fine_gain

        #Turn on HV
        Stabilized_Probe_Bussy = 0x00080000
        Stabilized_Probe_OK = 0x00100000

        dtb_probe_type = self.dtb.getParameter(ParameterCodes.Input_Status, self.input)
        if((dtb_probe_type & Stabilized_Probe_OK) != Stabilized_Probe_OK):
            #HV_Value = Utilities.readLine("Enter HV Value: ")
            self.dtb.setParameter(ParameterCodes.Input_Voltage, int(self.voltage), self.input)
            self.dtb.setParameter(ParameterCodes.Input_VoltageStatus, True, self.input)
            #Wait till ramping is complete
            while(self.dtb.getParameter(ParameterCodes.Input_VoltageRamping, self.input) is True):
                print "HVPS is ramping..."
                time.sleep(.2)
        else:
            print "Stabilized Probe detected, HV Ignored!"

        self.dtb.setParameter(ParameterCodes.Input_CoarseGain, self.coarse_gain, self.input) # [1.0, 2.0, 4.0, 8.0]
        self.dtb.setParameter(ParameterCodes.Input_FineGain, self.fine_gain, self.input) # [1.0, 5.0]

    def create_session(self, acquisition_interval, acquisition_spacing, acquisition_count):

        self.acquisition_interval = acquisition_interval
        self.acquisition_spacing = acquisition_spacing
        self.acquisition_count = acquisition_count

        now = datetime.now()
        self.source_dir = os.path.expanduser("/tmp/ashes/") + now.strftime("%Y%m%d_%H%M%S")
        os.makedirs(self.source_dir, 0777)
        print self.source_dir
        #Set the current memory group
        self.dtb.setParameter(ParameterCodes.Input_CurrentGroup, self.group, self.input)

    def run_session(self):

        #Continue to poll device and display information while it is acquiring
        for i in range(0, self.acquisition_count):

            # Setup presets
            self.dtb.setParameter(ParameterCodes.Preset_Live, self.acquisition_interval, self.input)

            #Clear data and time
            self.dtb.control(CommandCodes.Clear, self.input)

            #Start the acquisition
            print "Running acquition for ", self.acquisition_interval, " seconds\n"
            self.dtb.control(CommandCodes.Start, self.input)

            while True:
                sd = self.dtb.getSpectralData(self.input, self.group)
                if ((0 == (StatusBits.Busy & sd.getStatus())) and (0 == (StatusBits.Waiting & sd.getStatus()))):
                    break
                time.sleep(.1)

            self.tick(sd)

            self.save(sd, i)

            print "Sleeping for ", self.acquisition_spacing, " seconds\n"
            time.sleep(self.acquisition_spacing)

    def tick(self, sd):

        print(time.ctime())

        cnts = sd.getSpectrum().getCounts()
        totals = 0
        liveT = 0
        realT = 0
        for cnt in cnts:
            totals += cnt

        """print "Input: %d; Group: %d"%(sd.getInput(), sd.getGroup())"""

        liveT = sd.getLiveTime()
        realT = sd.getRealTime()
        print "Live time (uS): %d; Real time (uS): %d"%(liveT, realT)
        print "Uncorrected total counts: %d; Computational limit: %d"%(totals, sd.getComputationalValue())
        print "Status: %s\n"%(Utilities.getStatusDescription(sd.getStatus()))

    def save(self, sd, idx):

        chans = sd.getSpectrum().getCounts()
        mca, sec, rt, lt, dat, tim, off, nc = 1, 0, sd.getRealTime(), sd.getLiveTime(), "07DEC151", "0707", 0, len(chans) # FIXME
        hdr = pack("hhhhii8s4shh", -1, mca, 1, sec, rt, lt, dat, tim, off, nc)
        with open(self.source_dir + os.path.sep + str(idx) + ".chn", "w+b") as f:
            f.write(hdr)
            int_array = array('L', chans)
            int_array.tofile(f)
            f.close()
