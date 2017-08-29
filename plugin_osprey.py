# Detector plugin for Canberra Osprey gamma detectors
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

import os, sys, time
from gc_exceptions import ProtocolError

# Import API for the detector
toolkitPath = os.getcwd() + os.path.sep + '../DataTypes'
sys.path.append(toolkitPath)

from DeviceFactory import *
from ParameterCodes import *
from CommandCodes import *
from ParameterTypes import *
from PhaData import *

_detector_interface_ip = '10.0.1.4'
_detector_group = 1
_detector_input = 1
_detector = None

def initializeDetector(config):

    if set(config) < set(('voltage', 'coarse_gain', 'fine_gain', 'num_channels', 'lld', 'uld')):
        raise ProtocolError('detector_config_error', "Unable to initialize detector: missing configuration items")

    try:

        # Create and acquire detector
        global _detector
        _detector = DeviceFactory.createInstance(DeviceFactory.DeviceInterface.IDevice)
        _detector.open("", _detector_interface_ip)
        _detector.lock('administrator', 'password', _detector_input)

        # Osprey API constants
        Stabilized_Probe_Busy = 0x00080000
        Stabilized_Probe_OK = 0x00100000

        # Set voltage
        probe_status = _detector.getParameter(ParameterCodes.Input_Status, _detector_input)
        if((probe_status & Stabilized_Probe_OK) != Stabilized_Probe_OK):
            _detector.setParameter(ParameterCodes.Input_Voltage, int(config['voltage']), _detector_input)
            _detector.setParameter(ParameterCodes.Input_VoltageStatus, True, _detector_input)
            # Wait until ramping is complete
            while(_detector.getParameter(ParameterCodes.Input_VoltageRamping, _detector_input) is True):
                time.sleep(0.4)

        # Set infinite session timeout
        _detector.setParameter(ParameterCodes.Configuration_SessionTimeout, 0, _detector_input)

        # Set gain levels and discriminators
        _detector.setParameter(ParameterCodes.Input_CoarseGain, float(config['coarse_gain']), _detector_input) # [1.0, 2.0, 4.0, 8.0]
        _detector.setParameter(ParameterCodes.Input_FineGain, float(config['fine_gain']), _detector_input) # [1.0, 5.0]
        _detector.setParameter(ParameterCodes.Input_NumberOfChannels, int(config['num_channels']), _detector_input)
        _detector.setParameter(ParameterCodes.Input_LLDmode, 1, _detector_input) # Set manual LLD mode
        _detector.setParameter(ParameterCodes.Input_LLD, float(config['lld']), _detector_input)
        _detector.setParameter(ParameterCodes.Input_ULD, float(config['uld']), _detector_input)

    except Exception as ex:
        raise ProtocolError('error', str(ex))

def initializeSession(config):
    pass

def finalizeSession(config):
    pass

def acquireSpectrum(args):

    if set(args) < set(('session_name', 'livetime')):
        raise ProtocolError('error', "Unable to acquire spectrum: Missing arguments")

    try:

        # Reset acquisition
        _detector.control(CommandCodes.Stop, _detector_input)
        _detector.control(CommandCodes.Abort, _detector_input)
        _detector.setParameter(ParameterCodes.Input_SCAstatus, 0, _detector_input)
        _detector.setParameter(ParameterCodes.Counter_Status, 0, _detector_input)
        _detector.setParameter(ParameterCodes.Input_Mode, 0, _detector_input)
        _detector.setParameter(ParameterCodes.Preset_Options, 1, _detector_input)
        _detector.control(CommandCodes.Clear, _detector_input)
        _detector.setParameter(ParameterCodes.Input_CurrentGroup, _detector_group, _detector_input)

        # Setup presets
        _detector.setParameter(ParameterCodes.Preset_Live, float(args['livetime']), _detector_input)
        # Clear data and time
        _detector.control(CommandCodes.Clear, _detector_input)
        # Start the acquisition
        _detector.control(CommandCodes.Start, _detector_input)

        while True:
            sd = _detector.getSpectralData(_detector_input, _detector_group)
            if ((0 == (StatusBits.Busy & sd.getStatus())) and (0 == (StatusBits.Waiting & sd.getStatus()))):
                break
            time.sleep(0.1)

        # Extract spectrum from detector
        channels = sd.getSpectrum().getCounts()

        # Add spectrum data to response message
        msg = {
            'command': 'spectrum',
            'session_name': args['session_name'],
            'channels': ' '.join(map(str, channels)),
            'num_channels': len(channels),
            'total_count': sum(channels),
            'livetime': sd.getLiveTime(),
            'realtime': sd.getRealTime()
        }

    except Exception as ex:
        raise ProtocolError('error', str(ex))

    return msg
