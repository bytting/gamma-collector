# Controller for a Canberra Osprey gamma detector
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

from multiprocessing import Process
from proto import *
from datetime import datetime
import os, sys, time, socket, threading, logging
import Utilities

Utilities.setup()

from DeviceFactory import *
from ParameterCodes import *
from CommandCodes import *
from ParameterTypes import *
from PhaData import *

class SessionThread(threading.Thread):
    def __init__(self, event, target, session_name, iterations, delay, livetime):
        threading.Thread.__init__(self)
        self._stopped = event
        self._target = target
        self._session_name = session_name
        self._iterations = iterations
        self._delay = delay
        self._livetime = livetime

    def run(self):
        while not self._stopped.wait(self._delay):
            self._iterations = self._iterations - 1
            if self._iterations < 0:
                break
            logging.info('running once')
            self._target(self._session_name, self._livetime)
            logging.info('running once done')

class SpecProc(Process):
    def __init__(self, fd):
        Process.__init__(self)
        self.fd = fd
        self.running = False
        self.send_lock = threading.Lock()
        self.group = 1
        self.input = 1
        self.dtb = DeviceFactory.createInstance(DeviceFactory.DeviceInterface.IDevice)
        self.dtb.open("", Utilities.getLynxAddress())
        logging.info('spec: using device ' + self.dtb.getParameter(ParameterCodes.Network_MachineName, 0))
        self.dtb.lock("administrator", "password", self.input)

    def run(self):
        logging.info('spec: staring service')
        self.running = True
        while(self.running):
            if self.fd.poll():
                self.dispatch(self.fd.recv())

        self.fd.close()
        logging.info('spec: terminating')

    def send_msg(self, msg):
        self.send_lock.acquire()
        try:
            self.fd.send(msg)
        except:
            logging.error('spec: send exception: ' + sys.exc_info()[0])
        finally:
            self.send_lock.release()

    def dispatch(self, msg):
        if msg.command == 'set_gain':
            voltage = msg.arguments["voltage"]
            coarse = msg.arguments["coarse_gain"]
            fine = msg.arguments["fine_gain"]
            self.stabilize_probe(voltage, coarse, fine)
            logging.info('spec: gain has been set')
            msg.command = 'set_gain_ok'
            self.send_msg(msg)
        elif msg.command == 'close':
            self.running = False
        elif msg.command == 'new_session':
            self.session_name = msg.arguments['session_name']
            self.session_dir = os.path.expanduser("~/ashes/") + self.session_name
            os.makedirs(self.session_dir, 0777)
            logging.info('new session dir: ' + self.session_dir)
            self.session_stop = threading.Event()
            self.session = SessionThread(
                    self.session_stop,
                    self.session_run_once,
                    self.session_name,
                    int(msg.arguments['iterations']),
                    float(msg.arguments['delay']),
                    float(msg.arguments['livetime']))
            msg.command = 'new_session_ok'
            self.send_msg(msg)
            self.session.start()
        elif msg.command == 'stop_session':
            if not self.session_stop.isSet():
                self.session_stop.set()
                self.session.join()
                logging.info('session stopped')
            msg.command = 'stop_session_ok'
            self.send_msg(msg)
        else:
            logging.warning('spec: unknown command ' + cmd.command)

    def session_run_once(self, session_name, livetime):
        msg = Message(command='get_spectrum_ok')
        msg.arguments['session_name'] = session_name
        msg.arguments['livetime'] = livetime
        self.reset_acquisition()
        self.run_acquisition(msg)
        self.send_msg(msg)

    def stabilize_probe(self, voltage, coarse_gain, fine_gain):
        # Turn on HV
        Stabilized_Probe_Bussy = 0x00080000
        Stabilized_Probe_OK = 0x00100000
        dtb_probe_type = self.dtb.getParameter(ParameterCodes.Input_Status, self.input)
        if((dtb_probe_type & Stabilized_Probe_OK) != Stabilized_Probe_OK):
            #HV_Value = Utilities.readLine("Enter HV Value: ")
            self.dtb.setParameter(ParameterCodes.Input_Voltage, int(voltage), self.input)
            self.dtb.setParameter(ParameterCodes.Input_VoltageStatus, True, self.input)
            #Wait till ramping is complete
            logging.info('spec: ramping HVPS...')
            while(self.dtb.getParameter(ParameterCodes.Input_VoltageRamping, self.input) is True):
                time.sleep(.4)
        # Set gain
        self.dtb.setParameter(ParameterCodes.Input_CoarseGain, float(coarse_gain), self.input) # [1.0, 2.0, 4.0, 8.0]
        self.dtb.setParameter(ParameterCodes.Input_FineGain, float(fine_gain), self.input) # [1.0, 5.0]

    def reset_acquisition(self):
        #Disable all acquisition
        Utilities.disableAcquisition(self.dtb, self.input)
        #Set the acquisition mode. The Only Available Spectral in Osprey is Pha = 0
        self.dtb.setParameter(ParameterCodes.Input_Mode, 0, self.input)
        #Setup presets
        self.dtb.setParameter(ParameterCodes.Preset_Options, 1, self.input)
        #Clear data and time
        self.dtb.control(CommandCodes.Clear, self.input)
        #Set the current memory group
        self.dtb.setParameter(ParameterCodes.Input_CurrentGroup, self.group, self.input)

    def run_acquisition(self, msg):
        livetime = float(msg.arguments["livetime"])
        # Setup presets
        self.dtb.setParameter(ParameterCodes.Preset_Live, livetime, self.input)
        # Clear data and time
        self.dtb.control(CommandCodes.Clear, self.input)
        # Start the acquisition
        self.dtb.control(CommandCodes.Start, self.input)
        while True:
            sd = self.dtb.getSpectralData(self.input, self.group)
            if ((0 == (StatusBits.Busy & sd.getStatus())) and (0 == (StatusBits.Waiting & sd.getStatus()))):
                break
            time.sleep(.1)

        chans = sd.getSpectrum().getCounts()
        total_count = 0
        channel_string = ''
        for ch in chans:
            total_count += ch
            channel_string += str(ch) + ' '

        msg.arguments["channels"] = channel_string.strip()
        msg.arguments["channel_count"] = len(chans)
        msg.arguments["uncorrected_total_count"] = total_count
        msg.arguments["livetime"] = sd.getLiveTime()
        msg.arguments["realtime"] = sd.getRealTime()
        msg.arguments["computational_limit"] = sd.getComputationalValue()
        msg.arguments["status"] = Utilities.getStatusDescription(sd.getStatus())
        """print "Input: %d; Group: %d"%(sd.getInput(), sd.getGroup())"""
        #self.save(sd, i)

#    def save(self, sd, idx):
#        chans = sd.getSpectrum().getCounts()
#        mca, sec, rt, lt, dat, tim, off, nc = 1, 0, sd.getRealTime(), sd.getLiveTime(), "07DEC151", "0707", 0, len(chans) # FIXME
#        hdr = pack("hhhhii8s4shh", -1, mca, 1, sec, rt, lt, dat, tim, off, nc)
#        with open(self.source_dir + os.path.sep + str(idx) + ".chn", "w+b") as f:
#            f.write(hdr)
#            int_array = array('L', chans)
#            int_array.tofile(f)
#            f.close()
