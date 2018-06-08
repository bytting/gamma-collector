# Detector plugin for kromek gamma and neutron detectors
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

import sys, time
from ctypes import *
from gc_exceptions import ProtocolError

TOTAL_RESULT_CHANNELS = 4096

_so = CDLL('/usr/lib/libSpectrometerDriver.so')

_so.kr_Initialise.argtypes = [c_void_p, c_void_p]
_so.kr_Initialise.restype = c_int
_so.kr_GetNextDetector.argtypes = [c_uint]
_so.kr_GetNextDetector.restype = c_uint
_so.kr_GetDeviceSerial.argtypes = [c_uint, POINTER(c_char), c_int, POINTER(c_int)]
_so.kr_GetDeviceSerial.restype = c_int
_so.kr_ClearAcquiredData.argtypes = [c_uint]
_so.kr_ClearAcquiredData.restype = c_int
_so.kr_BeginDataAcquisition.argtypes = [c_uint, c_uint, c_uint]
_so.kr_BeginDataAcquisition.restype = c_int
_so.kr_IsAcquiringData.argtypes = [c_uint]
_so.kr_IsAcquiringData.restype = c_int
_so.kr_GetAcquiredDataEx.argtypes = [c_uint, POINTER(c_uint), POINTER(c_uint), POINTER(c_uint), POINTER(c_uint), c_uint]
_so.kr_GetAcquiredDataEx.restype = c_int

_did = c_uint(0)

def _setDetector(serialname):
    global _did
    _did = c_uint(0)

    serial = (c_char * 200)()
    serial_size = c_int(0)
    while True:
        _did = _so.kr_GetNextDetector(_did)
        if _did == 0:
            break

        _so.kr_GetDeviceName(_did, serial, 200, byref(serial_size))
        if serial.value == serialname:
            print "Using detector %s\n" % (serial.value)
            return

    raise ProtocolError('detector_config_error', "Detector not found: %s" % (serialname))

def initializePlugin():
    _so.kr_Initialise(c_void_p(None), c_void_p(None))

def finalizePlugin():
    _so.kr_Destruct()

def initializeDetector(config):
    global _did

    if set(config) < set(('serialnumber', 'voltage', 'lld')):
        raise ProtocolError('detector_config_error', "Unable to initialize detector: missing configuration items")

    _setDetector(config['serialnumber'])

def finalizeDetector(config):
    pass

def initializeSession(config):
    pass

def finalizeSession(config):
    pass

def acquireSpectrum(args):
    global _did

    if set(args) < set(('session_name', 'livetime')):
        raise ProtocolError('error', "Unable to acquire spectrum: Missing arguments")

    if _did == 0:
        raise ProtocolError('error', "Unable to acquire spectrum: Invalid detector id")

    lt = int(args['livetime'] * 1000.0)
    # _so.kr_ClearAcquiredData(_did)
    _so.kr_BeginDataAcquisition(_did, c_uint(0), c_uint(lt))

    while _so.kr_IsAcquiringData(_did):
        time.sleep(0.1)

    total_count = c_uint(0)
    livetime = c_uint(0)
    realtime = c_uint(0)
    spectrum = (c_uint * TOTAL_RESULT_CHANNELS)()
    flags = c_uint(1)
    _so.kr_GetAcquiredDataEx(_did, spectrum, byref(total_count), byref(realtime), byref(livetime), flags)

    # Add spectrum data to response message
    msg = {
        'command': 'spectrum',
        'session_name': args['session_name'],
        'channels': ' '.join(map(str, spectrum)),
        'num_channels': TOTAL_RESULT_CHANNELS,
        'total_count': int(total_count.value),
        'livetime': float(livetime.value) * 1000.0,
        'realtime': float(realtime.value) * 1000.0
    }

    return msg

if __name__ == "__main__":
    try:
        initializePlugin()
        config = {'serialnumber':'GR1A', 'voltage':700, 'lld':32}
        initializeDetector(config)

        args = {'session_name':'01012000_121212', 'livetime':2}
        msg = acquireSpectrum(args)

        print msg

    except ProtocolError as err:
        print "Exception: ", err
    finally:
        finalizePlugin()

