#
# Random utility functions.
#

from Phidget22.Devices.Log import Log

def setApiLogLevel(level, filename):
    if level:
        Log.enable(level, filename)
    else:
        Log.disable()

