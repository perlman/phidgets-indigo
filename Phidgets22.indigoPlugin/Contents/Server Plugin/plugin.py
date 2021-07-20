# -*- coding: utf-8 -*-

import indigo
import logging
import traceback
import json

# Phidget libraries
from Phidget22.Devices.Log import Log
from Phidget22.Net import Net, PhidgetServerType
from Phidget22.Phidget import Phidget
from Phidget22.PhidgetException import PhidgetException
from PhidgetInfo import PhidgetInfo

# Classes to describe network & channel search info
from phidget import ChannelInfo, NetInfo

# Our wrappers around phidget objects
from voltageinput import VoltageInputPhidget
from voltageratioinput import VoltageRatioInputPhidget
from digitaloutput import DigitalOutputPhidget
from temperaturesensor import TemperatureSensorPhidget
from digitalinput import DigitalInputPhidget

import phidget_util

class Plugin(indigo.PluginBase):
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        super(Plugin, self).__init__(pluginId, pluginDisplayName, pluginVersion, pluginPrefs)

        self.plugin_file_handler.setLevel(logging.INFO)  # Master Logging Level for Plugin Log file
        self.indigo_log_handler.setLevel(logging.INFO)   # Logging level for Indigo Event Log

        self.activePhidgets = {} # Map between Indigio ID and current instance of phidget
        
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

        loglevel = int(self.pluginPrefs.get('phidgetPluginLoggingLevel', '0'))
        if loglevel:
            self.plugin_file_handler.setLevel(loglevel)  # Master Logging Level for Plugin Log file
            self.indigo_log_handler.setLevel(loglevel)   # Logging level for Indigo Event Log
            self.logger.debug("Setting log level to %s" % logging.getLevelName(loglevel))

        self.logger.debug("Using %s" % Phidget.getLibraryVersion())

        # Should this be configurable?
        Net.enableServerDiscovery(PhidgetServerType.PHIDGETSERVER_DEVICEREMOTE)

    #
    # Methods for working with interactive Indigo UI
    #

    def validatePrefsConfigUi(self, valuesDict):
        # TODO
        return True

    def validateDeviceConfigUi(self, valuesDict, typeId, devId):
        # TODO: Perform some type of verification on the fields?

        # Set an address here
        # TODO: dynamic address updating would require replacing the device and using didDeviceCommPropertyChange to prevent respawn
        valuesDict[u'address'] = valuesDict['serialNumber']

        return (True, valuesDict)

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

    def actionControlDevice(self, action, device):
        if device.id in self.activePhidgets:
            return self.activePhidgets[device.id].actionControlDevice(action)
        else:
            raise Exception("Unexpected device: %s" % device.id)



    def deviceStartComm(self, device):
        # Phidget device type (device.deviceTypeId) are defined in devices.xml
        try:
            # Common properties for _all_ phidgets
            serialNumber = device.pluginProps.get("serialNumber", None)
            serialNumber = int(serialNumber) if serialNumber else 0

            channel = device.pluginProps.get("channel", None)
            channel = int(channel) if channel else -1

            isHubPortDevice = device.pluginProps.get("isHubPortDevice", None)
            isHubPortDevice = bool(isHubPortDevice) if isHubPortDevice else 0

            hubPort = device.pluginProps.get("hubPort", -1)
            hubPort = int(hubPort) if hubPort else -1

            networkPhidgets = self.pluginPrefs.get("networkPhidgets", False)
            enableServerDiscovery = self.pluginPrefs.get("enableServerDiscovery", False)
            
            channelInfo = ChannelInfo(
                serialNumber=serialNumber,
                channel=channel,
                isHubPortDevice=isHubPortDevice,
                hubPort=hubPort,
                netInfo=NetInfo(isRemote=networkPhidgets, serverDiscovery=enableServerDiscovery)
            )

            # Data interval is used by many types. See if it is set
            dataInterval = device.pluginProps.get("dataInterval", None)
            dataInterval = int(dataInterval) if dataInterval else None

            # TODO: Use better default sensor types... this might error if not populated
            if device.deviceTypeId == "voltageInput":
                sensorType = int(device.pluginProps.get("voltageSensorType", 0))
                newPhidget = VoltageInputPhidget(indigo_plugin=self, channelInfo=channelInfo, indigoDevice=device, logger=self.logger, sensorType=sensorType, dataInterval=dataInterval)
            elif device.deviceTypeId == "voltageRatioInput":
                sensorType = int(device.pluginProps.get("voltageRatioSensorType", 0))
                newPhidget = VoltageRatioInputPhidget(indigo_plugin=self, channelInfo=channelInfo, indigoDevice=device, logger=self.logger, sensorType=sensorType, dataInterval=dataInterval)
            elif device.deviceTypeId == "digitalOutput":
                newPhidget = DigitalOutputPhidget(indigo_plugin=self, channelInfo=channelInfo, indigoDevice=device, logger=self.logger)
            elif device.deviceTypeId == "digitalInput":
                newPhidget = DigitalInputPhidget(indigo_plugin=self, channelInfo=channelInfo, indigoDevice=device, logger=self.logger)
            elif device.deviceTypeId == "temperatureSensor":
                if device.pluginProps.get("useThermoCouple", False):
                    thermocoupleType = int(device.pluginProps.get("thermocoupleType", None))
                else:
                    thermocoupleType = None
                newPhidget = TemperatureSensorPhidget(indigo_plugin=self, channelInfo=channelInfo, indigoDevice=device, logger=self.logger, thermocoupleType=thermocoupleType, dataInterval=dataInterval)
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

        # Should this be called every time?
        device.stateListOrDisplayStateIdChanged()

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
