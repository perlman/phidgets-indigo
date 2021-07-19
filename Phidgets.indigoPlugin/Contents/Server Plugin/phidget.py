#
# Bulk of the code for actually interacting with the phidget devices.
#

import sys
import logging
import json
import traceback
import indigo


class NetInfo():
    def __init__(self, isRemote=None, serverDiscovery=None, hostname=None, port=None, password=None):
        self.isRemote = isRemote
        self.serverDiscovery = serverDiscovery
        self.hostname = hostname
        self.port = port
        self.password = password

class ChannelInfo():
    def __init__(self, serialNumber=-1, hubPort=-1, isHubPortDevice=0, channel=-1, netInfo=NetInfo()):
        self.serialNumber = serialNumber
        self.hubPort = hubPort
        self.isHubPortDevice = isHubPortDevice
        self.channel = channel
        self.netInfo = netInfo


class PhidgetBase(object):
    """
    Base class for phidget devices living in Indigo.
    This will be extended for the various types of devices.   
    """
    PHIDGET_DATA_INTERVAL = 1000     # ms

    def __init__(self, phidget, indigo_plugin=None, channelInfo=ChannelInfo(), indigoDevice=None, logger=None):
        self.phidget = phidget      # PhidgetAPI object for this phidget
        self.phidget.parent = self  # Reference back to this object from the PhidgetAPI
        self.logger = logger        # Where do we log?
        self.channelInfo = channelInfo
        self.indigoDevice = indigoDevice
        self.indigo_plugin = indigo_plugin

    def start(self):
        self.phidget.setDeviceSerialNumber(self.channelInfo.serialNumber)
        self.phidget.setChannel(self.channelInfo.channel)
        self.phidget.setIsRemote(self.channelInfo.netInfo.isRemote)
        self.phidget.setIsHubPortDevice(self.channelInfo.isHubPortDevice)
        self.phidget.setHubPort(self.channelInfo.hubPort)

        # Add appropriate handlers
        self.addPhidgetHandlers()

        # Open the phidget asynchronously.
        self.phidget.open()

    def onErrorHandler(self, ph, errorCode, errorString):
        """Default error handler for Phidgets."""
        # TODO: Set error state in Indigo
        ph.parent.logger.error("[Phidget Error Event] -> " + errorString + " (" + str(errorCode) + ")\n")

    def onAttachHandler(self, ph):
        raise Exception("onAttachHandler() must be handled by subclass")

    def addPhidgetHandlers(self):
        raise Exception("addPhidgetHandlers() must be handled by subclass")

    def stop(self):
        self.phidget.close()

    def getDeviceDisplayStateId(deviceTypeId):
        raise Exception("getDeviceDisplayStateId() must be handled by subclass")

    def getDeviceStateList(deviceTypeId):
        raise Exception("getDeviceStateList() must be handled by subclass")
