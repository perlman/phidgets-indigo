    #! /usr/bin/env python
# -*- coding: utf-8 -*-

import indigo
import logging
import traceback

from phidget import NetInfo, ChannelInfo
from phidget import PhidgetManager
from phidget import VoltageInputPhidget
from Phidget22.PhidgetException import PhidgetException
import phidget_util

class Plugin(indigo.PluginBase):
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        super(Plugin, self).__init__(pluginId, pluginDisplayName, pluginVersion, pluginPrefs)

        self.plugin_file_handler.setLevel(logging.DEBUG)  # Master Logging Level for Plugin Log file
        self.indigo_log_handler.setLevel(logging.DEBUG)   # Logging level for Indigo Event Log

        self.activePhidgets = {}
        self.phidgetManager = PhidgetManager()

    def __del__(self):
        indigo.PluginBase.__del__(self)

    def startup(self):
        if self.pluginPrefs.get('phidgetApiLogging', False):
            self.phidgetApiLogLevel = int(self.pluginPrefs['phidgetApiLogLevel'])
            phidget_util.setApiLogLevel(self.phidgetApiLogLevel, "/tmp/phidgets.log")      
        else:
            self.phidgetApiLogLevel = 0
    
    def validatePrefsConfigUi(self, valuesDict):
        return True

    def validateDeviceConfigUi(self, valuesDict, typeId, devId):
        # TODO: Verify integer fields
        return True

    def getDeviceStateList(self, dev):
        # TODO: Figure out how to do dynamic states for sub-types (e.g. specific sensor types)
        newStatesList = self.phidgetManager.getDeviceStateList(dev.deviceTypeId)
        self.logger.debug(newStatesList)
        return newStatesList

    def getDeviceDisplayStateId(self, dev):
        # TODO: Ask each device for the default state to display
        return self.phidgetManager.getDeviceDisplayStateId(dev.deviceTypeId)

    def deviceStartComm(self, device):
        # TODO: Generalize to any phidget type
        # TODO: Add support for local & defined servers
        if device.deviceTypeId == VoltageInputPhidget.INDIGO_DEVICE_TYPE:
            serialNumber = int(device.pluginProps.get("serialNumber", -1))
            channel = int(device.pluginProps.get("channel", -1))

            # TODO: These should be a global setting
            networkPhidgets = self.pluginPrefs.get("networkPhidgets", False)
            enableServerDiscovery = self.pluginPrefs.get("enableServerDiscovery", False)

            channelInfo = ChannelInfo(
                serialNumber=serialNumber,
                channel=channel,
                netInfo=NetInfo(isRemote=networkPhidgets, serverDiscovery=enableServerDiscovery)
            )

            try:
                newPhidget = VoltageInputPhidget(channelInfo=channelInfo, indigoDevice=device, logger=self.logger)
                self.activePhidgets[device.id] = newPhidget
                newPhidget.start()
            except PhidgetException as e:
                self.logger.error("%d: %s\n" % (e.code, e.details))
                self.logger.error(traceback.format_exc())
            except Exception as e:
                self.logger.error(traceback.format_exc())
        else:
            self.logger.error("Unknown device type: %s" % device.deviceTypeId)

    def deviceStopComm(self, device):
        myPhidget = self.activePhidgets.pop(device.id)
        myPhidget.stop()

    def shutdown(self):
        # TODO: Close Phidget connections
        pass

