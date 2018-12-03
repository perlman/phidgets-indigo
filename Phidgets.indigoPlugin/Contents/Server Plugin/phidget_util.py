#
# Random utility functions.
#

from Phidget22.Devices.Log import Log
from Phidget22.DeviceClass import DeviceClass

def setApiLogLevel(level, filename):
    if level:
        Log.enable(level, filename)
    else:
        Log.disable()

def logPhidgetEvent(ph, logger, eventType="UNKNOWN"):
    channelClassName = ph.getChannelClassName()
    serialNumber = ph.getDeviceSerialNumber()
    channel = ph.getChannel()
    deviceClass = ph.getDeviceClass()

    if(deviceClass == DeviceClass.PHIDCLASS_VINT):
        hubPort = ph.getHubPort()
        logger(eventType + " event: -> Channel Class: " + channelClassName + " -> Serial Number: " +
            str(serialNumber) + " -> Hub Port: " + str(hubPort) + " -> Channel:  " + str(channel))
    else:
        logger(eventType + " event: -> Channel Class: " + channelClassName + " -> Serial Number: " +
            str(serialNumber) + " -> Channel:  " + str(channel))

    return