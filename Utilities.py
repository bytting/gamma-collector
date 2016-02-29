import sys
import socket
import os
import platform
import logging

def setup():    
    """
    Description:
        This method will setup the Python package path to
        include the Lynx communications package defined
        by the \PythonExamples\DataTypes directory that came 
        with the SDK CD.
    Arguments:
        none
    Return:
        none
    """
    toolkitPath = os.getcwd() + os.path.sep + "../osprey"
    sys.path.append(toolkitPath)
    
def readLine(txt):
    """
    Description:
        This method will print the text that is supplied
        to the Python console and wait for the user to
        enter a response.  The purpose is to hide the 
        differences in the implementation of raw_input
        between different OS's.  Yes, there are subtle
        difference.
    Arguments:
        txt  (in, string) The text to display
    Return: 
        (string)    The entered value
    """
    val = raw_input(txt)
    return val.replace("\r", "")

def getStatusDescription(status):
    """
    Description:
        This method will return a string that describes the
        meaning of the various states contained in the status
        parameter.
    Arguments:
        status (in, int) The status value
    Return:
        (String) The description
    """
    exec "from ParameterTypes import *"
    statMsg="Idle "
    if (0 != (status&StatusBits.Busy)): statMsg="Busy "
    if (0 != (status&StatusBits.APZinprog)): statMsg+="APZ "
    if (0 != (status&StatusBits.Diagnosing)): statMsg+="Diagnosing "
    if (0 != (status&StatusBits.ExternalTriggerEvent)): statMsg+="Ext trig "
    if (0 != (status&StatusBits.Fault)): statMsg+="Fault "
    if (0 != (status&StatusBits.GroupComplete)): statMsg+="Group complete "
    if (0 != (status&StatusBits.HVramping)): statMsg+="HVPS ramping "
    if (0 != (status&StatusBits.Idle)): statMsg+="Idle "
    if (0 != (status&StatusBits.PresetCompReached)): statMsg+="Comp Preset reached "
    if (0 != (status&StatusBits.PresetTimeReached)): statMsg+="Time Preset reached "
    if (0 != (status&StatusBits.PresetSweepsReached)): statMsg+="Sweeps Preset reached "
    if (0 != (status&StatusBits.Rebooting)): statMsg+="Rebooting "
    if (0 != (status&StatusBits.UpdatingImage)): statMsg+="Updating firmware "
    if (0 != (status&StatusBits.Waiting)): statMsg+="Waiting "
    if (0 != (status&StatusBits.AcqNotStarted)): statMsg+="Acquisition not started because preset already reached "
    if (0 != (status&StatusBits.OverflowStop)): statMsg+="Acquisition stopped because channel contents overflowed "
    if (0 != (status&StatusBits.ExternalStop)): statMsg+="Acquisition stopped because of external stop "
    if (0 != (status&StatusBits.ManualStop)): statMsg+="Acquisition stopped because of manual stop "
    
    return statMsg

def getLynxAddress():
    return "10.0.1.4"
    
def getSpectralMode():
    """
    Description:
        This method will return the spectral acquisition mode
        that has been entered by the Python console
    Arguments:
        none
    Return: 
        (int) The value
    """
    error=True
    while error:
        try:
            val = readLine("Select the acquisition mode: (0=Pha, 1=Dlfc)")
            val = int(val)
            if (0 == val):
                return val      #Pha
            elif(1 == val):
                return 3        #Dlfc
        except: 
            pass
def getListMode():
    """
    Description:
        This method will return the list acquisition mode
        that has been entered by the Python console
    Arguments:
        none
    Return: 
        (int) The value
    """
    error=True
    while error:
        try:
            val = readLine("Select the acquisition mode: (0=List, 1=Tlist)")
            val = int(val)
            if (0 == val):
                return 4 #List
            elif(1 == val):
                return 5 #Tlist
        except: 
            pass
def getPresetMode():
    """
    Description:
        This method will return the preset mode
        that has been entered by the Python console
    Arguments:
        none
    Return: 
        (int) The value
    """
    error=True
    while error:
        try:
            val = readLine("Select the preset mode: (0=None, 1=Real, 2=Live)")
            val = int(val)
            if (0 == val):
                return 0 #PresetModes.PresetNone
            elif(1 == val):
                return 2 #PresetModes.PresetRealTime
            elif(2 == val):
                return 1 #PresetModes.PresetLiveTime
        except: 
            pass
def getMCSPresetMode():
    """
    Description:
        This method will return the MCS preset mode
        that has been entered by the Python console
    Arguments:
        none
    Return: 
        (int) The value
    """
    error=True
    while error:
        try:
            val = readLine("Select the acquisition mode: (0=None, 1=Sweeps)")
            val = int(val)
            if (0 == val):
                return 0 #PresetModes.PresetNone
            elif(1 == val):
                return 4 #PresetModes.PresetSweeps            
        except: 
            pass        
def getFloat(text, min, max):
    """
    Description:
        This method will return a floating point value
        that has been entered by the Python console
    Arguments:
        text    (in, string) The text description
        min     (in, float) The min value
        max     (in, float) The max value
    Return: 
        (float) The value
    """
    val=0.0
    error = True
    while error:
        try:
            val = readLine(text)
            val = float(val)
            if ((val >= min) and (val <= max)):
                return val
        except:
            pass
def getInt(text, min, max):
    """
    Description:
        This method will return an integer value
        that has been entered by the Python console
    Arguments:
        text    (in, string) The text description
        min     (in, int) The min value
        max     (in, int) The max value
    Return: 
        (int) The value
    """
    val=0
    error = True
    while error:
        try:
            val = readLine(text)
            val = int(val)
            if ((val >= min) and (val <= max)):
                return val
        except:
            pass
def dumpException(ex):
    """
    Description:
        This method will print out the exception
        information
    Arguments:
        ex    (in, Exception) The exception
    Return: 
        none
    """
    print "Exception caught.  Details: %s"%str(ex)
    
RolloverTime=long(0)                #This needs to be clears after a start command.
ROLLOVERBIT=0x00008000              #The rollover bit

def reconstructAndOutputTlistData(td, timeBase, clear):
    """
    Description:
        This method will reconstruct the time events for time
        stamped list mode before displaying on output
    Arguments:
        td (in, TlistData).  The time stamped list data buffer.
        timeBase (in, int).  The time base (nS)
        clear (in, bool).    Resets the global time counter
    Return:
        none
    """
    global RolloverTime
    if (clear): RolloverTime = long(0)
    
    recTime=0
    recEvent=0
    Time=long(0)  
    conv = float(timeBase)
    conv /= 1000 #Convert to ms
    
    for event in td.getEvents():          
        recTime=event.getTime()
        recEvent=event.getEvent()
        
        if (0 == (recTime&ROLLOVERBIT)): 
            Time = RolloverTime | (recTime & 0x7FFF)
        else:
            LSBofTC = int(0)
            MSBofTC = int(0)
            LSBofTC |= (recTime & 0x7FFF) << 15
            MSBofTC |= recEvent << 30
            RolloverTime = MSBofTC | LSBofTC 
            
            #goto next event
            continue
        print "Event: " + str(event.getEvent()) + "; Time (uS): " + str(Time*conv)
        Time=0
        
def isLocalAddressAccessible():
    """
    Description:
        This method will determine whether the network address
        of the local network adapter can be obtained.
    Arguments:
        none
    Return: 
        (bool)    True indicates that the network address can be obtained
    """
    try:
        if ("Linux" == platform.system()):
            remote = ("www.python.org", 80)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect( remote )
            ip, localport = s.getsockname()
            s.close()
        else:
            return True
    except:
        return False
    return True

def disableAcquisition(dtb, input):
    """
    Description:
        This method will stop all forms of data acquisition which includes
        any of the following:
            -) SCA collection
            -) Auxiliary counter collection
            -) PHA
            -) MCS
            -) MSS
            -) DLFC
            -) List
            -) Tlist
    Arguments:
        dtb (in, IDevice).  The device interface.
        input (in, int).  The input number
    Return: 
        none
    """
    
    logging.info('disableAcquisition 1')
    exec "from ParameterCodes import *"
    exec "from CommandCodes import *"
    exec "from ParameterTypes import *"
    
    logging.info('disableAcquisition 2')
    #Make sure the input is locked before attempting any operations
    dtb.lock("administrator", "password", input)
    
    logging.info('disableAcquisition 3')
    #Stop acquisition
    try:
        dtb.control(CommandCodes.Stop, input)
    except:
        pass
    logging.info('disableAcquisition 4')
    #Abort acquisition (only needed for MSS or MCS collections)
    try:
        dtb.control(CommandCodes.Abort, input)
    except:
        pass
    logging.info('disableAcquisition 5')
    #Stop SCA collection
    try:
        dtb.setParameter(ParameterCodes.Input_SCAstatus, 0, input)
    except:
        pass
    logging.info('disableAcquisition 6')
    #Stop Aux counter collection
    try:
        dtb.setParameter(ParameterCodes.Counter_Status, 0, input)
    except:
        pass
    logging.info('disableAcquisition 7')
        
        
    
