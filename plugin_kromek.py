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

import os
from ctypes import *

so = CDLL('/usr/lib/libSpectrometerDriver.so')

so.kr_Initialise.argtypes = [c_void_p, c_void_p]
so.kr_Initialise(c_void_p(None), c_void_p(None))

so.kr_GetNextDetector.argtypes = [c_uint]
so.kr_GetNextDetector.restype = c_uint
did = so.kr_GetNextDetector(c_uint(0))
if did == 0:
    print "No detector found"
    so.kr_Destruct()
    os.exit(1)
else:
    print "Using detector %d\n" % (did)

print "Run detector for 5 seconds"
so.kr_BeginDataAcquisition.argtypes = [c_uint, c_uint, c_uint]
so.kr_BeginDataAcquisition.restype = c_int
so.kr_BeginDataAcquisition(c_uint(did), c_uint(5000), c_uint(0))

so.kr_IsAcquiringData.argtypes = [c_uint]
so.kr_IsAcquiringData.restype = c_int
while so.kr_IsAcquiringData(c_uint(did)):
    pass

total_count = c_uint(0)
spectrum = (c_uint * 4096)()
so.kr_GetAcquiredData.argtypes = [c_uint, POINTER(c_uint), POINTER(c_uint), POINTER(c_uint), POINTER(c_uint)]
so.kr_GetAcquiredData.restype = c_int
so.kr_GetAcquiredData(c_uint(did), spectrum, byref(total_count), None, None)

print "Total count: %d\n" % (total_count.value)
print "Spectrum:\n"
for i in range(4096):
    print "%d " % (spectrum[i]),
print

so.kr_Destruct()
