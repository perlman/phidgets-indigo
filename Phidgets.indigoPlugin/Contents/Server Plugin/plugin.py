    #! /usr/bin/env python
# -*- coding: utf-8 -*-

import indigo
import logging
import traceback
import json

from phidget import NetInfo, ChannelInfo
from phidget import PhidgetManager
from phidget import VoltageInputPhidget, VoltageRatioInputPhidget
from Phidget22.PhidgetException import PhidgetException
from Phidget22.Phidget import Phidget
import phidget_util

class Plugin(indigo.PluginBase):
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        super(Plugin, self).__init__(pluginId, pluginDisplayName, pluginVersion, pluginPrefs)

        self.plugin_file_handler.setLevel(logging.DEBUG)  # Master Logging Level for Plugin Log file
        self.indigo_log_handler.setLevel(logging.DEBUG)   # Logging level for Indigo Event Log

        self.activePhidgets = {}
        self.phidgetManager = PhidgetManager(phidgetInfoFile='../Resources/phidgets.json')

        self.logger.setLevel(logging.DEBUG)

    def __del__(self):
        indigo.PluginBase.__del__(self)

    def startup(self):
        # Setup logging in the phidgets library
        if self.pluginPrefs.get('phidgetApiLogging', False):
            self.phidgetApiLogLevel = int(self.pluginPrefs['phidgetApiLogLevel'])
            self.phidgetApiLogfile = self.pluginPrefs['phidgetApiLogfile']
            phidget_util.setApiLogLevel(self.phidgetApiLogLevel, self.phidgetApiLogfile)
        else:
            self.phidgetApiLogLevel = 0
    
    def validatePrefsConfigUi(self, valuesDict):
        # TODO
        return True

    def validateDeviceConfigUi(self, valuesDict, typeId, devId):
        # TODO
        return True

    def getPhidgetTypeMenu(self, filter="", valuesDict=None, typeId="", targetId=0):
        return self.phidgetManager.getPhidgetTypeMenu()

    def getDeviceStateList(self, device):
        (phidget_class_id, phidget_type) = phidget_util.phidgetDecodeMenu(device.pluginProps.get("phidgetType", None))
        if device.id in self.activePhidgets:
            return self.activePhidgets[device.id].getDeviceStateList(phidget_class_id)
        else:
            indigo.List()

    def getDeviceDisplayStateId(self, device):
        (phidget_class_id, phidget_type) = phidget_util.phidgetDecodeMenu(device.pluginProps.get("phidgetType", None))
        if device.id in self.activePhidgets:
            return self.activePhidgets[device.id].getDeviceDisplayStateId(phidget_class_id)
        else:
            return None

    def deviceStartComm(self, device):
        # TODO: Use gemeral fumction for this
        (phidget_class_id, phidget_type) = phidget_util.phidgetDecodeMenu(device.pluginProps.get("phidgetType", None))

        if phidget_class_id in [VoltageInputPhidget.PHIDGET_DEVICE_TYPE, VoltageRatioInputPhidget.PHIDGET_DEVICE_TYPE]:
            serialNumber = int(device.pluginProps.get("serialNumber", -1))
            channel = int(device.pluginProps.get("channel", -1))
            networkPhidgets = self.pluginPrefs.get("networkPhidgets", False)
            enableServerDiscovery = self.pluginPrefs.get("enableServerDiscovery", False)
            channelInfo = ChannelInfo(
                serialNumber=serialNumber,
                channel=channel,
                netInfo=NetInfo(isRemote=networkPhidgets,
                serverDiscovery=enableServerDiscovery)
            )

            try:
                if phidget_class_id == VoltageInputPhidget.PHIDGET_DEVICE_TYPE:
                    newPhidget = VoltageInputPhidget(indigo_plugin=self, channelInfo=channelInfo, phidget_type=phidget_type, indigoDevice=device, logger=self.logger)
                elif phidget_class_id == VoltageRatioInputPhidget.PHIDGET_DEVICE_TYPE:
                    newPhidget = VoltageRatioInputPhidget(indigo_plugin=self, channelInfo=channelInfo, phidget_type=phidget_type, indigoDevice=device, logger=self.logger)
                else:
                    raise Exception("Unexpected device type: %s" % device.deviceTypeId)
                self.activePhidgets[device.id] = newPhidget
                newPhidget.start()
                device.stateListOrDisplayStateIdChanged()
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
        Phidget.finalize(0)
