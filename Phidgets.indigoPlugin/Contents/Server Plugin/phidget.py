import sys
import indigo
import logging
import json

from Phidget22.Devices.VoltageInput import VoltageInput
from Phidget22.Devices.VoltageRatioInput import VoltageRatioInput
from Phidget22.PhidgetException import PhidgetException
from Phidget22.Net import Net, PhidgetServerType
from Phidget22.DeviceClass import DeviceClass
from Phidget22.ChannelSubclass import ChannelSubclass
from Phidget22.Unit import Unit
from Phidget22.VoltageRatioSensorType import VoltageRatioSensorType
from Phidget22.VoltageSensorType import VoltageSensorType

import phidget_util

class NetInfo():
    def __init__(self, isRemote=None, serverDiscovery=None, hostname=None, port=None, password=None):
        self.isRemote = isRemote
        self.serverDiscovery = serverDiscovery
        self.hostname = hostname
        self.port = port
        self.password = password


class ChannelInfo():
    def __init__(self, serialNumber=-1, hubPort=-1, isHubPortDevice=0, channel=-1, isVINT=None, netInfo=NetInfo()):
        self.serialNumber = serialNumber
        self.hubPort = hubPort
        self.isHubPortDevice = isHubPortDevice
        self.channel = channel
        self.isVINT = isVINT
        self.netInfo = netInfo


class PhidgetBase(object):
    """Base class for phidget devices living in Indigo."""
    PHIDGET_DEVICE_TYPE_DESC = "UNKNOWN"
    PHIDGET_DEVICE_TYPE = None
    PHIDGET_SENSOR_KEY = None
    PHIDGET_DATA_INTERVAL = 1000     # ms

    def __init__(self, phidget, indigo_plugin=None, phidget_type=None, channelInfo=ChannelInfo(), indigoDevice=None, logger=None):
        self.phidget = phidget      # PhidgetAPI object for this phidget
        self.phidget.parent = self  # Reference back to this object from the PhidgetAPI
        self.logger = logger
        self.channelInfo = channelInfo
        self.indigoDevice = indigoDevice
        self.indigo_plugin = indigo_plugin
        self.phidget_type = int(phidget_type)   # Argument from main phidget menu (e.g., sensor #)

    def start(self):
        self.phidget.setDeviceSerialNumber(self.channelInfo.serialNumber)
        self.phidget.setChannel(self.channelInfo.channel)
        self.phidget.setIsRemote(self.channelInfo.netInfo.isRemote)
        self.phidget.setIsHubPortDevice(self.channelInfo.isHubPortDevice)
        self.phidget.setHubPort(self.channelInfo.hubPort)

        # Todo: This should be a plugin-wide setting
        Net.enableServerDiscovery(PhidgetServerType.PHIDGETSERVER_DEVICEREMOTE)

        # Add appropriate handlers
        self.addPhidgetHandlers()

        # Open the phidget asynchronously.
        self.phidget.open()

    def addPhidgetHandlers(self):
        raise Exception("addPhidgetHandlers() must be handled by subclass")

    def stop(self):
        self.phidget.close()

    def onErrorHandler(self, ph, errorCode, errorString):
        # TODO: Set the device to an error state?
        ph.parent.logger.error("[Phidget Error Event] -> " + errorString + " (" + str(errorCode) + ")\n")

    @classmethod
    def getDeviceDisplayStateId(cls, deviceTypeId):
        raise Exception("getDeviceDisplayStateId() must be handled by subclass")

    @classmethod
    def getDeviceStateList(cls, deviceTypeId):
        raise Exception("getDeviceStateList() must be handled by subclass")

    @classmethod
    def getDeviceSensorMenu(cls, deviceTypeId, phidgetInfo={}):
        items = []
        for item in phidgetInfo.get(cls.PHIDGET_SENSOR_KEY, {}):
            items.append( ("option%d" % item['value'], item['description']) )
        return items

    @classmethod
    def getPhidgetMenu(cls, phidgetInfo={}):
        items = []
        for item in phidgetInfo.get(cls.PHIDGET_SENSOR_KEY, {}):
            items.append( ("%s#%d" % (cls.PHIDGET_DEVICE_TYPE, item['value']),
                           "%s (%s)" % (item['description'], cls.PHIDGET_DEVICE_TYPE_DESC)))
        return items

class VoltageInputPhidget(PhidgetBase):
    PHIDGET_DEVICE_TYPE_DESC="Voltage Input"
    PHIDGET_DEVICE_TYPE="voltageInput"          # deviceId used by Indigo
    PHIDGET_SENSOR_KEY="VoltageSensorType"      # Key used in phdigets.json; derived from the Phidget22 filename

    def __init__(self, *args, **kwargs):
        super(VoltageInputPhidget, self).__init__(phidget=VoltageInput(), *args, **kwargs)
        self.sensor_unit = Unit()

    def addPhidgetHandlers(self):
        self.phidget.setOnErrorHandler(self.onErrorHandler)
        self.phidget.setOnAttachHandler(self.onAttachHandler)
        self.phidget.setOnVoltageChangeHandler(self.onVoltageChangeHandler)
        self.phidget.setOnSensorChangeHandler(self.onSensorChangeHandler)

    def onVoltageChangeHandler(self, ph, voltage):
        ph.parent.indigoDevice.updateStateOnServer("voltage", value=voltage, uiValue="%f V" % voltage)

    def onSensorChangeHandler(self, ph, sensorValue, sensorUnit):
        ph.parent.indigoDevice.updateStateOnServer("sensorValue", value=sensorValue, uiValue="%f %s" % (sensorValue, sensorUnit.symbol))

    def onAttachHandler(self, ph):
        try:
            phidget_util.logPhidgetEvent(ph, self.logger.info, "Attach")
            ph.setDataInterval(PhidgetBase.PHIDGET_DATA_INTERVAL)
            self.logger.debug("Adding sensor type %d" % self.phidget_type)
            ph.setSensorType(self.phidget_type)
        except PhidgetException as e:
            self.logger.error("%d: %s\n" % (e.code, e.details))
            self.logger.error(traceback.format_exc())
        except Exception as e:
            self.logger.error(traceback.format_exc())

    def getDeviceStateList(self):
        newStatesList = indigo.List()
        newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType("voltage", "voltage", "voltage"))
        if self.phidget_type != VoltageSensorType.SENSOR_TYPE_VOLTAGE:
            newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType("sensorValue", "sensorValue", "sensorValue"))
        return newStatesList
    
    def getDeviceDisplayStateId(self):
        if self.phidget_type != VoltageRatioSensorType.SENSOR_TYPE_VOLTAGERATIO:
            return "sensorValue"
        else:
            return "voltage"

    
class VoltageRatioInputPhidget(PhidgetBase):
    PHIDGET_DEVICE_TYPE_DESC="Voltage Ratio Input"
    PHIDGET_DEVICE_TYPE="voltageRatioInput"           # deviceId used by Indigo
    PHIDGET_SENSOR_KEY="VoltageRatioSensorType"       # Key used in phdigets.json; derived from the Phidget22 filename
    
    def __init__(self, *args, **kwargs):
        super(VoltageRatioInputPhidget, self).__init__(phidget=VoltageRatioInput(), *args, **kwargs)

    def addPhidgetHandlers(self):
        self.phidget.setOnErrorHandler(self.onErrorHandler)
        self.phidget.setOnAttachHandler(self.onAttachHandler)
        self.phidget.setOnVoltageRatioChangeHandler(self.onVoltageRatioChangeHandler)
        self.phidget.setOnSensorChangeHandler(self.onSensorChangeHandler)

    def onVoltageRatioChangeHandler(self, ph, voltageRatio):
        ph.parent.indigoDevice.updateStateOnServer("voltageRatio", value=voltageRatio, uiValue="%f V/V" % voltageRatio)

    def onSensorChangeHandler(self, ph, sensorValue, sensorUnit):
        ph.parent.indigoDevice.updateStateOnServer("sensorValue", value=sensorValue, uiValue="%f %s" % (sensorValue, sensorUnit.symbol))

    def onAttachHandler(self, ph): 
        try:
            phidget_util.logPhidgetEvent(ph, self.logger.info, "Attach")
            ph.setDataInterval(PhidgetBase.PHIDGET_DATA_INTERVAL)
            self.logger.debug("Adding sensor type %d" % self.phidget_type)
            ph.setSensorType(self.phidget_type)
        except PhidgetException as e:
            self.logger.error("%d: %s\n" % (e.code, e.details))
            self.logger.error(traceback.format_exc())
        except Exception as e:
            self.logger.error(traceback.format_exc())

    def getDeviceStateList(self):
        newStatesList = indigo.List()
        newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType("voltageRatio", "voltageRatio", "voltageRatio"))
        if self.phidget_type != VoltageRatioSensorType.SENSOR_TYPE_VOLTAGERATIO:
            newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType("sensorValue", "sensorValue", "sensorValue"))
        return newStatesList
    
    def getDeviceDisplayStateId(self):
        if self.phidget_type != VoltageRatioSensorType.SENSOR_TYPE_VOLTAGERATIO:
            return "sensorValue"
        else:
            return "voltageRatio"


class PhidgetManager(object):
    PHIDGET_CLASSES = [VoltageInputPhidget, VoltageRatioInputPhidget]

    def __init__(self, phidgetInfoFile=None):
        if phidgetInfoFile:
            # Read JSON with human-readable phidget sensors/modes/etc.
            with open(phidgetInfoFile, 'r') as f:
                self.phidgetInfo = json.load(f)
        else:
            self.phidgetInfo = {}

    def getClassByTypeId(self, phidget_class_id):
        for phidgetClass in PhidgetManager.PHIDGET_CLASSES:
            if phidgetClass.PHIDGET_DEVICE_TYPE == phidget_class_id:
                return phidgetClass
        return None

    def getPhidgetTypeMenu(self):
        menu = []
        for phidget_class in PhidgetManager.PHIDGET_CLASSES:            
            menu = menu + phidget_class.getPhidgetMenu(self.phidgetInfo)
        return sorted(menu, key=lambda x: (x[1][0].isdigit(), x[1]))

