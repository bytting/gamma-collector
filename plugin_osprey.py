# Detector controller for gamma measurements
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

import os, sys, time, gc_proto as proto

# Import API for the detector
toolkitPath = os.getcwd() + os.path.sep + "../DataTypes"
sys.path.append(toolkitPath)

from DeviceFactory import *
from ParameterCodes import *
from CommandCodes import *
from ParameterTypes import *
from PhaData import *

detector_interface_ip = "10.0.1.4"
detector_group = 1
detector_input = 1
detector = None

def initializeDetector(config):	
	
	global detector

	try:
		detector = DeviceFactory.createInstance(DeviceFactory.DeviceInterface.IDevice)
		detector.open("", detector_interface_ip)		
		detector.lock("administrator", "password", detector_input)
		
		voltage = int(config["voltage"])
		coarse_gain = float(config["coarse_gain"])
		fine_gain = float(config["fine_gain"])
		num_channels = int(config["num_channels"])
		lld = float(config["lld"])
		uld = float(config["uld"])
		
		_stabilizeProbe(voltage, coarse_gain, fine_gain, num_channels, lld, uld)

		return True, None

	except Exception as e:

		return False, e.args

def acquireSpectrum(args):	
		
	try:
		_resetAcquisition()
			
		# Setup presets
		livetime = float(args["livetime"])
		detector.setParameter(ParameterCodes.Preset_Live, livetime, detector_input)
		# Clear data and time
		detector.control(CommandCodes.Clear, detector_input)
		# Start the acquisition
		detector.control(CommandCodes.Start, detector_input)	
		
		while True:	
			sd = detector.getSpectralData(detector_input, detector_group)
			if ((0 == (StatusBits.Busy & sd.getStatus())) and (0 == (StatusBits.Waiting & sd.getStatus()))):
				break
			time.sleep(.1)
		
		# Extract last spectrum from detector and prepare parameters
		chans = sd.getSpectrum().getCounts()

		# Add spectrum data to response message
		msg = proto.Message('spectrum')
		msg.arguments["channels"] = ' '.join(map(str, chans))
		msg.arguments["num_channels"] = len(chans)
		msg.arguments["total_count"] = sum(chans)
		msg.arguments["livetime"] = sd.getLiveTime()
		msg.arguments["realtime"] = sd.getRealTime()

		return msg

	except Exception as e:

		emsg = proto.Message('error')
		emsg.arguments["message"] = e.args

		return emsg

def _stabilizeProbe(voltage, coarse_gain, fine_gain, num_channels, lld, uld):
	
	# Osprey API constants
	Stabilized_Probe_Busy = 0x00080000
	Stabilized_Probe_OK = 0x00100000

	# Set voltage
	probe_status = detector.getParameter(ParameterCodes.Input_Status, detector_input)	
	if((probe_status & Stabilized_Probe_OK) != Stabilized_Probe_OK):
		detector.setParameter(ParameterCodes.Input_Voltage, voltage, detector_input)
		detector.setParameter(ParameterCodes.Input_VoltageStatus, True, detector_input)
		# Wait until ramping is complete		
		while(detector.getParameter(ParameterCodes.Input_VoltageRamping, detector_input) is True):
			time.sleep(.4)
	
	# Set gain levels and discriminators
	detector.setParameter(ParameterCodes.Input_CoarseGain, coarse_gain, detector_input) # [1.0, 2.0, 4.0, 8.0]
	detector.setParameter(ParameterCodes.Input_FineGain, fine_gain, detector_input) # [1.0, 5.0]
	detector.setParameter(ParameterCodes.Input_NumberOfChannels, num_channels, detector_input)
	detector.setParameter(ParameterCodes.Input_LLDmode, 1, detector_input) # Set manual LLD mode
	detector.setParameter(ParameterCodes.Input_LLD, lld, detector_input)
	detector.setParameter(ParameterCodes.Input_ULD, uld, detector_input)

def _resetAcquisition():
	
	# Stop any current acquisitions
	detector.control(CommandCodes.Stop, detector_input)
	# Abort acquisition (only needed for MSS or MCS collections)
	detector.control(CommandCodes.Abort, detector_input)
	# Stop SCA collection
	detector.setParameter(ParameterCodes.Input_SCAstatus, 0, detector_input)
	# Stop Aux counter collection
	detector.setParameter(ParameterCodes.Counter_Status, 0, detector_input)
	# Set the acquisition mode. The Only Available Spectral in Osprey is Pha = 0
	detector.setParameter(ParameterCodes.Input_Mode, 0, detector_input)
	# Setup presets
	detector.setParameter(ParameterCodes.Preset_Options, 1, detector_input)
	# Clear data and time
	detector.control(CommandCodes.Clear, detector_input)
	# Set the current memory group
	detector.setParameter(ParameterCodes.Input_CurrentGroup, detector_group, detector_input)	
