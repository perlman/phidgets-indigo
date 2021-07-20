# -*- coding: utf-8 -*-
#
# Bulk of the code for actually interacting with the phidget devices.
#

import sys
import logging
import json
import time
import threading
import traceback
import indigo

import phidget_util

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
    PHIDGET_DATA_INTERVAL = 1000          # ms
    PHIDGET_INITIAL_CONNECT_TIMEOUT = 5   # s

    def __init__(self, phidget, indigo_plugin=None, channelInfo=ChannelInfo(), indigoDevice=None, logger=None):
        self.phidget = phidget      # PhidgetAPI object for this phidget
        self.phidget.parent = self  # Reference back to this object from the PhidgetAPI
        self.logger = logger        # Where do we log?
        self.channelInfo = channelInfo
        self.indigoDevice = indigoDevice
        self.indigo_plugin = indigo_plugin

    def start(self):
        self.logger.debug("Creating " + self.__class__.__name__ + " for Indigo device '" + str(self.indigoDevice.name) + "' (%d)" % self.indigoDevice.id)

        self.phidget.setDeviceSerialNumber(self.channelInfo.serialNumber)
        self.phidget.setChannel(self.channelInfo.channel)
        self.phidget.setIsRemote(self.channelInfo.netInfo.isRemote)
        self.phidget.setIsHubPortDevice(self.channelInfo.isHubPortDevice)
        self.phidget.setHubPort(self.channelInfo.hubPort)

        # Set the initial connection timer
        self.timer = threading.Timer(self.PHIDGET_INITIAL_CONNECT_TIMEOUT, self.connectionTimeoutHandler)
        self.timer.start()

        # Add appropriate handlers
        self.addPhidgetHandlers()

        # Open the phidget asynchronously.
        self.phidget.open()

    def connectionTimeoutHandler(self):
        self.indigoDevice.setErrorStateOnServer('Detached')
        self.logger.error("No response creating " + self.__class__.__name__ + " for Indigo device '" +
            str(self.indigoDevice.name) + "' (%d)" % self.indigoDevice.id +
            ' after %d seconds.' % self.PHIDGET_INITIAL_CONNECT_TIMEOUT)

    def onErrorHandler(self, ph, errorCode, errorString):
        """Default error handler for Phidgets."""
        # TODO: Set error state in Indigo
        ph.parent.logger.error("[Phidget Error Event] -> " + errorString + " (" + str(errorCode) + ")\n")

    def onDetachHandler(self, ph):
        self.indigoDevice.setErrorStateOnServer('Detached')
        phidget_util.logPhidgetEvent(ph, self.logger.debug, "Detach")

    def onAttachHandler(self, ph):
        self.timer.cancel()
        self.indigoDevice.setErrorStateOnServer(None)
        phidget_util.logPhidgetEvent(ph, self.logger.debug, "Attach")

    def stop(self):
        self.timer.cancel()
        self.logger.debug("Stopping " + self.__class__.__name__ + " for Indigo device '" + str(self.indigoDevice.name) + "' (%d)" % self.indigoDevice.id)
        self.phidget.close()


    #
    # Methods to be implemented by subclasses
    #

    def addPhidgetHandlers(self):
        raise Exception("addPhidgetHandlers() must be handled by subclass")

    def getDeviceDisplayStatesId(self):
        raise Exception("getDeviceDisplayStateId() must be handled by subclass")

    def getDeviceStateList(self):
        raise Exception("getDeviceStateList() must be handled by subclass")

    def actionControlDevice(self, action):
        raise Exception("actionControlDevice() may be handled by subclass")