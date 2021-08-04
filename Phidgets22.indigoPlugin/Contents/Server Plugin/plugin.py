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
from frequencycounter import FrequencyCounterPhidget
from humiditysensor import HumiditySensorPhidget

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
        # self.logger.error("%s\n%s\n" % (valuesDict, typeId))
        returnValue = True
        errorDict = indigo.Dict()

        # Set an address here
        # TODO: dynamic address updating would require replacing the device and using didDeviceCommPropertyChange to prevent respawn

        # Calculate something for the Indigo device address property
        if bool(valuesDict['isVintHub']) and not bool(valuesDict['isVintDevice']):
            valuesDict[u'address'] = valuesDict['serialNumber'] + "|p" + valuesDict['hubPort']
        elif not bool(valuesDict['isVintHub']) and not bool(valuesDict['isVintDevice']):   # an interfaceKit
            if typeId == 'digitalInput':
                valuesDict[u'address'] = valuesDict['serialNumber'] + "|di-" + valuesDict['channel']
            elif typeId == 'digitalOutput':
                valuesDict[u'address'] = valuesDict['serialNumber'] + "|do-" + valuesDict['channel']
            elif typeId == 'voltageRatioInput':
                valuesDict[u'address'] = valuesDict['serialNumber'] + "|vr-" + valuesDict['channel']
            elif typeId == 'voltageInput':
                valuesDict[u'address'] = valuesDict['serialNumber'] + "|av-" + valuesDict['channel']
            else:
                valuesDict[u'address'] = valuesDict['serialNumber'] + "|p-" + valuesDict['channel']
        elif 'hubPort' in valuesDict and len(valuesDict['hubPort']) > 0 and 'channel' in valuesDict and len(valuesDict['channel']) > 0:
            valuesDict[u'address'] = valuesDict['serialNumber'] + "|p" + valuesDict['hubPort'] + "-c" + valuesDict['channel']
        elif 'hubPort' in valuesDict and len(valuesDict['hubPort']):
            valuesDict[u'address'] = valuesDict['serialNumber'] + "|p" + valuesDict['hubPort']
        elif 'channel' in valuesDict and len(valuesDict['channel']) > 0:
            valuesDict[u'address'] = valuesDict['serialNumber'] + "|c" + valuesDict['channel']
        else:
            valuesDict[u'address'] = valuesDict['serialNumber']

        # Make sure we have a useful serial number
        if not valuesDict['serialNumber']:
            errorDict['serialNumber'] = "A serial number is required"
            returnValue = False
        elif not valuesDict['serialNumber'].isdigit():
            errorDict['serialNumber'] = "The serial number must be numeric"
            returnValue = False
        elif len(valuesDict['serialNumber']) < 5:
            errorDict['serialNumber'] = "Serial number too short"
            returnValue = False
        # else we should check to see if this serial number can actually be reached

        try:
            if 'dataInterval' in valuesDict:
                valuesDict['dataInterval'] = int(valuesDict['dataInterval'])
                if valuesDict['dataInterval'] >= 0 and valuesDict['dataInterval'] <= 5000:
                    pass
                else:
                    returnValue = False
                    errorDict['dataInterval'] = "The value of this field must be from 0 to 1000"
        except Exception as e:
                returnValue = False
                errorDict['dataInterval'] = "Illegal valuye"

        return (returnValue, valuesDict, errorDict)

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

    def actionControlSensor(self, action, device):
        if device.id in self.activePhidgets:
            return self.activePhidgets[device.id].actionControlSensor(action)
        else:
            raise Exception("Unexpected device: %s" % device.id)

    def deviceStartComm(self, device):
        # Phidget device type (device.deviceTypeId) are defined in devices.xml
        # TODO: Clean this up by refactoring into factory methods for each Phidget type

        try:
            # Common properties for _all_ phidgets
            serialNumber = device.pluginProps.get("serialNumber", None)
            serialNumber = int(serialNumber) if serialNumber else -1

            channel = device.pluginProps.get("channel", None)
            channel = int(channel) if channel else -1

            # isHubPortDevice is true only when non-VINT devices are attached to a VINT hub
            isVintHub = device.pluginProps.get("isVintHub", None)
            isVintHub = bool(isVintHub) if isVintHub else 0
            isVintDevice = device.pluginProps.get("isVintDevice", None)
            isVintDevice = bool(isVintDevice) if isVintDevice else 0
            isHubPortDevice = int(isVintHub and not isVintDevice)

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
            decimalPlaces = int(device.pluginProps.get("decimalPlaces", 3)) # Sane default 3 decimal places?

            # TODO: Use better default sensor types... this might error if not populated
            if device.deviceTypeId == "voltageInput":
                sensorType = int(device.pluginProps.get("voltageSensorType", 0))
                voltageChangeTrigger = float(device.pluginProps.get("voltageChangeTrigger", 0))
                sensorValueChangeTrigger = float(device.pluginProps.get("sensorValueChangeTrigger", 0))
                newPhidget = VoltageInputPhidget(indigo_plugin=self, channelInfo=channelInfo, indigoDevice=device, decimalPlaces=decimalPlaces, logger=self.logger, sensorType=sensorType, dataInterval=dataInterval, voltageChangeTrigger=voltageChangeTrigger, sensorValueChangeTrigger=sensorValueChangeTrigger)
            elif device.deviceTypeId == "voltageRatioInput":
                # voltageRatioChangeTrigger = float(device.pluginProps.get("voltageRatioChangeTrigger", 0))
                # sensorValueChangeTrigger = float(device.pluginProps.get("sensorValueChangeTrigger", 0))
                # sensorType = int(device.pluginProps.get("voltageRatioSensorType", 0))
                newPhidget = VoltageRatioInputPhidget(indigo_plugin=self, channelInfo=channelInfo, indigoDevice=device, logger=self.logger)
            elif device.deviceTypeId == "digitalOutput":
                newPhidget = DigitalOutputPhidget(indigo_plugin=self, channelInfo=channelInfo, indigoDevice=device, logger=self.logger)
            elif device.deviceTypeId == "digitalInput":
                newPhidget = DigitalInputPhidget(indigo_plugin=self, channelInfo=channelInfo, indigoDevice=device, logger=self.logger)
            elif device.deviceTypeId == "temperatureSensor":
                temperatureChangeTrigger = float(device.pluginProps.get("temperatureChangeTrigger", 0))
                displayTempUnit = device.pluginProps.get("displayTempUnit", "C")
                if device.pluginProps.get("useThermoCouple", False):
                    thermocoupleType = int(device.pluginProps.get("thermocoupleType", None))
                else:
                    thermocoupleType = None
                newPhidget = TemperatureSensorPhidget(indigo_plugin=self, channelInfo=channelInfo, indigoDevice=device, logger=self.logger, decimalPlaces=decimalPlaces, displayTempUnit=displayTempUnit, thermocoupleType=thermocoupleType, dataInterval=dataInterval, temperatureChangeTrigger=temperatureChangeTrigger)
            elif device.deviceTypeId == "frequencyCounter":
                filterType = int(device.pluginProps.get("filterType", 0))
                frequencyCutoff = float(device.pluginProps.get("frequencyCutoff", 1))
                displayStateName = device.pluginProps.get("displayStateName", None)
                newPhidget = FrequencyCounterPhidget(indigo_plugin=self, channelInfo=channelInfo, indigoDevice=device, logger=self.logger, decimalPlaces=decimalPlaces, filterType=filterType, dataInterval=dataInterval, frequencyCutoff=frequencyCutoff, displayStateName=displayStateName)
            elif device.deviceTypeId == "humiditySensor":
                humidityChangeTrigger = float(device.pluginProps.get("humidityChangeTrigger", 0))
                newPhidget = HumiditySensorPhidget(indigo_plugin=self, channelInfo=channelInfo, indigoDevice=device, logger=self.logger, decimalPlaces=decimalPlaces, humidityChangeTrigger=humidityChangeTrigger, dataInterval=dataInterval)
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
