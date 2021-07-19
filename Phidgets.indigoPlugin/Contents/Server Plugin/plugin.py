# -*- coding: utf-8 -*-

import indigo
import logging
import traceback
import json

from Phidget22.Devices.Log import Log
from Phidget22.Net import Net, PhidgetServerType
from Phidget22.Phidget import Phidget
from Phidget22.PhidgetException import PhidgetException
from PhidgetInfo import PhidgetInfo

from phidget import ChannelInfo, NetInfo
from voltageinput import VoltageInputPhidget

class Plugin(indigo.PluginBase):
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        super(Plugin, self).__init__(pluginId, pluginDisplayName, pluginVersion, pluginPrefs)

        self.plugin_file_handler.setLevel(logging.DEBUG)  # Master Logging Level for Plugin Log file
        self.indigo_log_handler.setLevel(logging.DEBUG)   # Logging level for Indigo Event Log

        self.activePhidgets = {} # Map between Indigio ID and current instance of phidget
        
        # TODO: Recreate the PhidgetManager as PhidgetInfoManager
        self.phidgetInfo = PhidgetInfo(phidgetInfoFile='../Resources/phidgets.json')

        self.logger.setLevel(logging.DEBUG)

    def startup(self):
        # Setup logging in the phidgets library
        if self.pluginPrefs.get('phidgetApiLogging', False):
            self.phidgetApiLogLevel = int(self.pluginPrefs['phidgetApiLogLevel'])
            self.phidgetApiLogfile = self.pluginPrefs['phidgetApiLogfile']
            Log.enable(self.phidgetApiLogLevel, self.phidgetApiLogfile)
        else:
            Log.disable()
            self.phidgetApiLogLevel = 0

        # Should this be configurable?
        Net.enableServerDiscovery(PhidgetServerType.PHIDGETSERVER_DEVICEREMOTE)


    #
    # Methods for working with interactive Indigo UI
    #
    def validatePrefsConfigUi(self, valuesDict):
        # TODO
        return True

    def validateDeviceConfigUi(self, valuesDict, typeId, devId):
        # TODO
        return True


    def getPhidgetTypeMenu(self, filter="", valuesDict=None, typeId="", targetId=0):
        classes = filter.split(',')
        return self.phidgetInfo.getPhidgetTypeMenu(classes)


    #
    # Interact with the phidgets
    #

    def getDeviceStateList(self, device):
        if device.id in self.activePhidgets:
            return self.activePhidgets[device.id].getDeviceStateList()
        else:
            indigo.List()

    def getDeviceDisplayStateId(self, device):
        if device.id in self.activePhidgets:
            return self.activePhidgets[device.id].getDeviceDisplayStateId()
        else:
            return None

    def deviceStartComm(self, device):
        # Phidget device type (device.deviceTypeId) are defined in devices.xml

        # Common properties for _all_ phidgets
        serialNumber = int(device.pluginProps.get("serialNumber", -1))
        channel = int(device.pluginProps.get("channel", -1))
        isHubPortDevice = int(device.pluginProps.get("isHubPortDevice", 0))
        try:
            hubPort = int(device.pluginProps.get("hubPort", -1))
        except:
            hubPort = -1
        networkPhidgets = self.pluginPrefs.get("networkPhidgets", False)
        enableServerDiscovery = self.pluginPrefs.get("enableServerDiscovery", False)
        channelInfo = ChannelInfo(
            serialNumber=serialNumber,
            channel=channel,
            isHubPortDevice=isHubPortDevice,
            hubPort=hubPort,
            netInfo=NetInfo(isRemote=networkPhidgets, serverDiscovery=enableServerDiscovery)
        )

        try:
            if device.deviceTypeId == "voltageInput":
                sensorType = int(device.pluginProps.get("voltageInputType", None))
                newPhidget = VoltageInputPhidget(indigo_plugin=self, channelInfo=channelInfo, indigoDevice=device, logger=self.logger, sensorType=sensorType)

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

    #
    # Methods related to shutdown
    #
    def deviceStopComm(self, device):
        myPhidget = self.activePhidgets.pop(device.id)
        myPhidget.stop()

    def shutdown(self):
        Phidget.finalize(0)

    def __del__(self):
        indigo.PluginBase.__del__(self)
