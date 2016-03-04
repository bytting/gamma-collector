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
from gps import *
from struct import pack
from array import array
import os, sys, math, copy, time, socket, threading, logging

# Import API for the detector
toolkitPath = os.getcwd() + os.path.sep + "../DataTypes"
sys.path.append(toolkitPath)

from DeviceFactory import *
from ParameterCodes import *
from CommandCodes import *
from ParameterTypes import *
from PhaData import *

detector_interface_ip = "10.0.1.4"

class GpsThread(threading.Thread):
    """
    Thread class to handle the gps driver
    """
    def __init__(self, event):
        """
        Description:
            Initialize the gps thread
        """
        threading.Thread.__init__(self)
        self._stopped = event
        self.gpsd = gps(mode=WATCH_ENABLE)
        self.last_lat = 0
        self.last_epx = 0
        self.last_lon = 0
        self.last_epy = 0
        self.last_alt = 0
        self.last_epv = 0
        self.last_speed = 0
        self.last_eps = 0
        self.last_time = ''

    def run(self):
        """
        Description:
            Entry point for the gps thread
        """
        logging.info('gps: starting service')

        # Process any buffered gps signals every .3 seconds
        while not self._stopped.wait(0.3):

            # Update our last measurement until buffer is empty
            while self.gpsd.waiting():
                self.gpsd.next()
                if not math.isnan(self.gpsd.fix.latitude):
                    self.last_lat = self.gpsd.fix.latitude
                if not math.isnan(self.gpsd.fix.epx):
                    self.last_epx = self.gpsd.fix.epx
                if not math.isnan(self.gpsd.fix.longitude):
                    self.last_lon = self.gpsd.fix.longitude
                if not math.isnan(self.gpsd.fix.epy):
                    self.last_epy = self.gpsd.fix.epy
                if not math.isnan(self.gpsd.fix.altitude):
                    self.last_alt = self.gpsd.fix.altitude
                if not math.isnan(self.gpsd.fix.epv):
                    self.last_epv = self.gpsd.fix.epv
                if not math.isnan(self.gpsd.fix.speed):
                    self.last_speed = self.gpsd.fix.speed
                if not math.isnan(self.gpsd.fix.eps):
                    self.last_eps = self.gpsd.fix.eps
                if self.gpsd.utc != None and self.gpsd.utc != '':
                    self.last_time = self.gpsd.utc

        logging.info('gps: terminating')

    @property
    def latitude(self):
        return self.last_lat

    @property
    def epx(self):
        return self.last_epx

    @property
    def longitude(self):
        return self.last_lon

    @property
    def epy(self):
        return self.last_epy

    @property
    def altitude(self):
        return self.last_alt

    @property
    def epv(self):
        return self.last_epv

    @property
    def speed(self):
        return self.last_speed

    @property
    def eps(self):
        return self.last_eps

    @property
    def time(self):
        return self.last_time

class SessionThread(threading.Thread):
    """
    Thread class to govern a single session
    """
    def __init__(self, event, target, msg):
        """
        Description:
            Initialize the session thread
        Arguments:
            event - Event to notify session close
            target - Function running the detector
            msg - The session message containing info about this session
        """
        threading.Thread.__init__(self)
        self._stopped = event
        self._target = target
        self._msg = msg

    def run(self):
        """
        Description:
            Entry point for the session thread
        """
        logging.info('session: starting')
        # Extract the session variables from the session message
        delay = float(self._msg.arguments["delay"]) # Time to wait between each spectrum
        iterations = int(self._msg.arguments["iterations"]) # Number of spectrums to take
        infinite = iterations == -1 # If iterations is -1, run forever
        index = 0 # Keep track of spectrums (spectrum id)

        while not self._stopped.wait(delay):
            if not infinite:
                # Exit when we reach a zero spectrum count
                iterations = iterations - 1
                if iterations < 0:
                    break
            # Run the detector once
            self._target(self._msg, index)
            index = index + 1

        self._target(self._msg, -1)
        logging.info('session: terminating')

class SpecProc(Process):
    """
    Process class for handling the gps and spectrometer
    """
    def __init__(self, fd):
        """
        Description:
            Initialize the spectrometer process
        Arguments:
            fd - file descriptor to pass and receive messages to/from controller
        """
        Process.__init__(self)
        self.fd = fd
        self.running = False
        self.session_running = False
        self.send_lock = threading.Lock() # Lock used to syncronize sending of messages to controller
        self.gps_stop = threading.Event() # Event used to notify gps thread
        self.gps_client = GpsThread(self.gps_stop) # Create the gps thread
        # Initalize the detector
        self.group = 1
        self.input = 1
        self.dtb = DeviceFactory.createInstance(DeviceFactory.DeviceInterface.IDevice)
        self.dtb.open("", detector_interface_ip)
        logging.info('spec: using device ' + self.dtb.getParameter(ParameterCodes.Network_MachineName, 0))
        self.dtb.lock("administrator", "password", self.input)

    def run(self):
        """
        Description:
            Entry point for the spectrometer process
        """
        logging.info('spec: staring service')
        self.running = True
        self.gps_client.start() # Start the gps
        mips_counter = 1000

        # Event loop
        while(self.running):
            if self.fd.poll():
                self.dispatch(self.fd.recv()) # Handle messages from the controller
            else:
                time.sleep(.1)

                if not self.session_running:
                    # Keep the detector alive.
                    # Default session timeout for the detector is 600 seconds
                    mips_counter = mips_counter - 1
                    if mips_counter <= 0:
                        mips_counter = 1000
                        status = self.dtb.getParameter(ParameterCodes.Input_Status, self.input)

        # Cleanup and exit
        self.fd.close()
        self.gps_stop.set()
        self.gps_client.join()
        logging.info('spec: GPS client stopped')
        logging.info('spec: terminating')

    def send_msg(self, msg):
        """
        Description:
            Function to safely pass messages to controller
        Arguments:
            msg - The message to pass
        """
        self.send_lock.acquire()
        try:
            self.fd.send(msg)
        except:
            logging.error('spec: send exception: ' + sys.exc_info()[0])
        finally:
            self.send_lock.release()

    def dispatch(self, msg):
        """
        Description:
            Handle a message received from controller
        Arguments:
            msg - The message received
        """
        if msg.command == 'set_gain': # Set the gain parameters for the detector
            voltage = msg.arguments["voltage"]
            coarse = msg.arguments["coarse_gain"]
            fine = msg.arguments["fine_gain"]
            self.stabilize_probe(voltage, coarse, fine)
            logging.info('spec: gain has been set')
            msg.command = 'set_gain_ok' # Notify ground control that gain has been set
            self.send_msg(msg)
        elif msg.command == 'close': # Controller wants us to close down
            self.running = False
        elif msg.command == 'new_session': # Start a new session
            msg.command = 'new_session_ok'
            self.send_msg(msg)
            self.session_stop = threading.Event()
            self.session = SessionThread(self.session_stop, self.run_session_pass, msg)
            self.session.start()
            self.session_running = True
            logging.info('spec: session thread started')
        elif msg.command == 'stop_session': # Stop any running sessions
            if not self.session_stop.isSet():
                self.session_stop.set()
                self.session.join()
                logging.info('spec: session stopped')
            msg.command = 'stop_session_ok' # Notify ground control that we have stopped any sessions
            self.send_msg(msg)
        else:
            # Unknown command received from controller
            logging.warning('spec: unknown command ' + cmd.command)

    def stabilize_probe(self, voltage, coarse_gain, fine_gain):
        """
        Description:
            Set gain parameters for the detector
        Arguments:
            voltage - The voltage level
            coarse_gain - The coarse gain level
            fine_gain - The fine gain level
        """
        # Osprey API constants
        Stabilized_Probe_Bussy = 0x00080000
        Stabilized_Probe_OK = 0x00100000
        dtb_probe_type = self.dtb.getParameter(ParameterCodes.Input_Status, self.input)
        # Set voltage
        if((dtb_probe_type & Stabilized_Probe_OK) != Stabilized_Probe_OK):
            self.dtb.setParameter(ParameterCodes.Input_Voltage, int(voltage), self.input)
            self.dtb.setParameter(ParameterCodes.Input_VoltageStatus, True, self.input)
            # Wait till ramping is complete
            logging.info('spec: ramping HVPS...')
            while(self.dtb.getParameter(ParameterCodes.Input_VoltageRamping, self.input) is True):
                time.sleep(.4)
        # Set coarse and fine gain
        self.dtb.setParameter(ParameterCodes.Input_CoarseGain, float(coarse_gain), self.input) # [1.0, 2.0, 4.0, 8.0]
        self.dtb.setParameter(ParameterCodes.Input_FineGain, float(fine_gain), self.input) # [1.0, 5.0]

    def run_session_pass(self, req_msg, session_index):
        """
        Description:
            Gather info from gps and detector
        Arguments:
            req_msg - The session message
            session_index - The sequence number in current session
        """
        # Prepare the response message
        resp_msg = copy.deepcopy(req_msg)

        # If session_index is -1 the session is over
        if session_index == -1:
            resp_msg.command = 'session_close'
            self.send_msg(resp_msg)
            self.session_running = False
            return

        resp_msg.command = 'spectrum'
        resp_msg.arguments['session_index'] = session_index

        # Reset detector
        self.reset_acquisition()

        # Gather gps info before running the detector
        resp_msg.arguments['latitude_start'] = self.gps_client.latitude
        resp_msg.arguments['latitude_start_err'] = self.gps_client.epx
        resp_msg.arguments['longitude_start'] = self.gps_client.longitude
        resp_msg.arguments['longitude_start_err'] = self.gps_client.epy
        resp_msg.arguments['altitude_start'] = self.gps_client.altitude
        resp_msg.arguments['altitude_start_err'] = self.gps_client.epv
        resp_msg.arguments['gps_speed_start'] = self.gps_client.speed
        resp_msg.arguments['gps_speed_start_err'] = self.gps_client.eps
        resp_msg.arguments['gps_time_start'] = self.gps_client.time

        # Run the detector
        self.run_acquisition(resp_msg, session_index)

        # Gather gps info after running the detector
        resp_msg.arguments['gps_time_end'] = self.gps_client.time
        resp_msg.arguments['latitude_end'] = self.gps_client.latitude
        resp_msg.arguments['latitude_end_err'] = self.gps_client.epx
        resp_msg.arguments['longitude_end'] = self.gps_client.longitude
        resp_msg.arguments['longitude_end_err'] = self.gps_client.epy
        resp_msg.arguments['altitude_end'] = self.gps_client.altitude
        resp_msg.arguments['altitude_end_err'] = self.gps_client.epv
        resp_msg.arguments['gps_speed_end'] = self.gps_client.speed
        resp_msg.arguments['gps_speed_end_err'] = self.gps_client.eps

        # Save acquisition to file and send a meta message to controller
        fn = self.save_acquisition(resp_msg, session_index)
        m = Message('spectrum_ready')
        m.arguments["filename"] = fn
        self.send_msg(m)

    def reset_acquisition(self):
        """
        Description:
            Reset and initialize the detector
        """
        try:
            self.dtb.control(CommandCodes.Stop, self.input)
            #Abort acquisition (only needed for MSS or MCS collections)
            self.dtb.control(CommandCodes.Abort, self.input)
            #Stop SCA collection
            self.dtb.setParameter(ParameterCodes.Input_SCAstatus, 0, self.input)
            #Stop Aux counter collection
            self.dtb.setParameter(ParameterCodes.Counter_Status, 0, self.input)

            # Set the acquisition mode. The Only Available Spectral in Osprey is Pha = 0
            self.dtb.setParameter(ParameterCodes.Input_Mode, 0, self.input)
            # Setup presets
            self.dtb.setParameter(ParameterCodes.Preset_Options, 1, self.input)
            # Clear data and time
            self.dtb.control(CommandCodes.Clear, self.input)
            # Set the current memory group
            self.dtb.setParameter(ParameterCodes.Input_CurrentGroup, self.group, self.input)
        except:
            logging.error('spec: reset_acquisition failed')

    def run_acquisition(self, msg, session_index):
        """
        Description:
            Run the detector
        Arguments:
            msg - The response message
            session_index - The sequence number in current session
        """
        # Setup presets
        livetime = float(msg.arguments["livetime"])
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

        # Extract last spectrum from detector and prepare parameters
        chans = sd.getSpectrum().getCounts()
        total_count = 0
        channel_string = ''
        for ch in chans:
            total_count += ch
            channel_string += str(ch) + ' '

        # Add spectrum data to the response message
        msg.arguments["channels"] = channel_string.strip()
        msg.arguments["num_channels"] = len(chans)
        msg.arguments["total_count"] = total_count
        msg.arguments["livetime"] = sd.getLiveTime()
        msg.arguments["realtime"] = sd.getRealTime()
        msg.arguments["computational_limit"] = sd.getComputationalValue()
        msg.arguments["spectral_input"] = sd.getInput()
        msg.arguments["spectral_group"] = sd.getGroup()

    def save_acquisition(self, msg, session_index):
        """
        Description:
            Save the gps and specter data to file (json format)
        Arguments:
            msg - The response message
            session_index - The sequence number in current session
        """
        # Build the path to store the response message
        session_name = msg.arguments['session_name']
        session_dir = os.path.expanduser("~/ashes/") + session_name
        if not os.path.isdir(session_dir):
            os.makedirs(session_dir, 0777)
        fname = session_dir + os.path.sep + str(session_index) + ".json"
        # Store the response message to file
        with open(fname, "w") as f:
            json.dump(msg.__dict__, f)
        return fname

    def save_acquisition_as_chn(self, sd, msg, session_index):
        """
        Description:
            Save the the specter data to file (chn format)
        Arguments:
            sd - Spectrum data
            msg - The session message
            session_index - The sequence number in current session
        """
        session_name = msg.arguments['session_name']
        session_dir = os.path.expanduser("~/ashes/") + session_name
        if not os.path.isdir(session_dir):
            os.makedirs(session_dir, 0777)
        chans = sd.getSpectrum().getCounts()
        mca, sec, rt, lt, dat, tim, off, nc = 1, 0, sd.getRealTime(), sd.getLiveTime(), "07DEC151", "0707", 0, len(chans) # FIXME
        hdr = pack("hhhhii8s4shh", -1, mca, 1, sec, rt, lt, dat, tim, off, nc)
        with open(session_dir + os.path.sep + str(session_index) + ".chn", "w+b") as f:
            f.write(hdr)
            int_array = array('L', chans)
            int_array.tofile(f)
