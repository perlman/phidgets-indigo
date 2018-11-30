
import sys
import indigo
import logging

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
        self.password = hostname

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


class VoltageInputPhidget(PhidgetBase):
    INDIGO_DEVICE_TYPE="voltageInput"
    VOLTAGEINPUT_DATA_INTERVAL=1000
    VOLTAGEINPUT_VOLTAGE_CHANGE_TRIGGER=5.0
    def __init__(self, *args, **kwargs):
        super(VoltageInputPhidget, self).__init__(phidget=VoltageInput(), *args, **kwargs)

    def addPhidgetHandlers(self):
        self.phidget.setOnAttachHandler(VoltageInputPhidget.onAttachHandler)
        self.phidget.setOnVoltageChangeHandler(VoltageInputPhidget.onVoltageChangeHandler)

    @staticmethod
    def onVoltageChangeHandler(ph, voltage):
        device = ph.parent.indigoDevice.updateStateOnServer("state", value=voltage)
        #ph.parent.logger.debug("[Voltage Event] -> Voltage: " + str(voltage))
        pass

    @staticmethod
    def onAttachHandler(ph):
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
