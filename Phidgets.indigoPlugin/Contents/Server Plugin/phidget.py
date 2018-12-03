
import sys
import indigo
import logging
import json

from Phidget22.Devices.VoltageInput import VoltageInput, VoltageSensorType
from Phidget22.PhidgetException import PhidgetException
from Phidget22.Net import Net, PhidgetServerType
from Phidget22.DeviceClass import DeviceClass
from Phidget22.ChannelSubclass import ChannelSubclass

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
    INDIGO_DEVICE_TYPE = None
    PHIDGET_SENSOR_KEY = None

    def __init__(self, phidget, channelInfo=ChannelInfo(), indigoDevice=None, logger=None):
        self.phidget = phidget      # PhidgetAPI object for this phidget
        self.phidget.parent = self  # Reference back to this object from the PhidgetAPI
        self.logger = logger
        self.value = None
        self.channelInfo = channelInfo
        self.indigoDevice = indigoDevice

    def getValue(self):
        return self.value

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
        # Must be implemented by subclasses
        pass

    def stop(self):
        self.phidget.close()

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
            items.append( ("option%d" % item['value'], item['desc']) )
        return items
    
class VoltageInputPhidget(PhidgetBase):
    INDIGO_DEVICE_TYPE="voltageInput"           # deviceId used by Indigo
    PHIDGET_SENSOR_KEY="VoltageSensorType"      # Key used in phdigets.json; derived from the python filename
    VOLTAGEINPUT_DATA_INTERVAL=1000
    VOLTAGEINPUT_VOLTAGE_CHANGE_TRIGGER=5.0

    def __init__(self, *args, **kwargs):
        super(VoltageInputPhidget, self).__init__(phidget=VoltageInput(), *args, **kwargs)

    def addPhidgetHandlers(self):
        self.phidget.setOnAttachHandler(self.onAttachHandler)
        self.phidget.setOnVoltageChangeHandler(self.onVoltageChangeHandler)

    def onVoltageChangeHandler(self, ph, voltage):
        device = ph.parent.indigoDevice.updateStateOnServer("voltage", value=voltage)

    def onAttachHandler(self, ph):
        try:
            channelClassName = ph.getChannelClassName()
            serialNumber = ph.getDeviceSerialNumber()
            channel = ph.getChannel()
            deviceClass = ph.getDeviceClass()

            if(deviceClass == DeviceClass.PHIDCLASS_VINT):
                hubPort = ph.getHubPort()
                ph.parent.logger.debug("Attach event: (\n\t-> Channel Class: " + channelClassName + "\n\t-> Serial Number: " +
                    str(serialNumber) + "\n\t-> Hub Port: " + str(hubPort) + "\n\t-> Channel:  " + str(channel) + "\n")
            else:
                ph.parent.logger.debug("Attach event: \n\t-> Channel Class: " + channelClassName + "\n\t-> Serial Number: " +
                    str(serialNumber) + "\n\t-> Channel:  " + str(channel) + "\n")

            ph.parent.logger.debug("%f %f %f %f" % (ph.getMinDataInterval(), ph.getMaxDataInterval(),
                ph.getMinVoltageChangeTrigger(), ph.getMaxVoltageChangeTrigger()))
            ph.setDataInterval(VOLTAGEINPUT_DATA_INTERVAL)
            ph.setVoltageChangeTrigger(VOLTAGEINPUT_VOLTAGE_CHANGE_TRIGGER)

            if(ph.getChannelSubclass() == ChannelSubclass.PHIDCHSUBCLASS_VOLTAGEINPUT_SENSOR_PORT):
                ph.setSensorType(VoltageSensorType.SENSOR_TYPE_VOLTAGE)
        except PhidgetException as e:
            sys.stderr.write("%d: %s\n" % (e.code, e.details))
            traceback.print_exc()

    @classmethod
    def getDeviceStateList(cls, deviceTypeId):
        newStatesList = indigo.List()
        newState = indigo.Dict()
        newState[u"Disabled"] = False
        newState[u"Type"] = indigo.kTriggerKeyType.Number
        newState[u"Key"] = "voltage"
        newState[u"StateLabel"] = "Voltage"
        newState[u"TriggerLabel"] = "Voltage"
        newStatesList.append(newState)
        return newStatesList
    
    @classmethod
    def getDeviceDisplayStateId(cls, deviceTypeId):
        return "voltage"

class PhidgetManager(object):
    PHIDGET_CLASSES = [VoltageInputPhidget]

    def __init__(self, phidgetInfoFile=None):
        if phidgetInfoFile:
            # Read JSON with human-readable phidget sensors/modes/etc.
            with open(phidgetInfoFile, 'r') as f:
                self.phidgetInfo = json.load(f)
        else:
            self.phidgetInfo = {}

    def getClassByTypeId(self, deviceTypeId):
        for phidgetClass in PhidgetManager.PHIDGET_CLASSES:
            if phidgetClass.INDIGO_DEVICE_TYPE == deviceTypeId:
                return phidgetClass
            else:
                return None

    def getDeviceDisplayStateId(self, deviceTypeId):
        return self.getClassByTypeId(deviceTypeId).getDeviceDisplayStateId(deviceTypeId)

    def getDeviceStateList(self, deviceTypeId):
        return self.getClassByTypeId(deviceTypeId).getDeviceStateList(deviceTypeId)

    def getDeviceSensorMenu(self, deviceTypeId):
        return self.getClassByTypeId(deviceTypeId).getDeviceSensorMenu(deviceTypeId, self.phidgetInfo)
