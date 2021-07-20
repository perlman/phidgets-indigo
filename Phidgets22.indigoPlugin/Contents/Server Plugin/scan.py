#! /usr/env/python

#
# Utility to scan for available phidgets
#

import time
import re

from Phidget22.Devices.Manager import Manager
from Phidget22.Net import Net, PhidgetServerType
from Phidget22.ChannelClass import ChannelClass
from Phidget22.ChannelSubclass import ChannelSubclass
from Phidget22.DeviceClass import DeviceClass
from Phidget22.DeviceID import DeviceID
from Phidget22.Phidget import Phidget


class PhidgetDevice():
    def __init__(self, channel):
        # device
        self.serialNumber = channel.getDeviceSerialNumber()
        self.deviceClass = channel.getDeviceClass()
        self.deviceName = channel.getDeviceName()
        self.deviceId = channel.getDeviceID()
        self.deviceLabel = channel.getDeviceLabel()
        self.deviceSku = channel.getDeviceSKU()
        # channel
        self.sku = channel.getDeviceSKU()
        self.channel = channel.getChannel()
        self.channelClass = channel.getChannelClass()
        self.channelSubClass = channel.getChannelSubclass()
        self.channelName = channel.getChannelName()
        self.deviceParent = channel.getParent()
        if channel.getDeviceClass() == DeviceClass.PHIDCLASS_INTERFACEKIT:
            self.devicePort = channel.getChannel()
        else:
            self.devicePort = channel.getHubPort()
        if channel.getIsRemote():
            self.serverPeerName = channel.getServerPeerName()
            self.serverHostname = channel.getServerHostname()
            self.serverName = channel.getServerName()
            self.serverIpAddr = channel.getServerPeerName()
            self.serverUniqueName = channel.getServerUniqueName()
        else:
            self.serverPeerName = "Local"
            self.serverHostname = "Local"
            self.serverName = "Local"
            self.serverIpAddr = "Local"
            self.serverUniqueName = "Local"
        try:
            self.channelCount = "Hub Port Count: %s" % channel.getHubPortCount()
        except Exception:
            self.channelCount = channel.getDeviceChannelCount(ChannelClass.PHIDCHCLASS_NOTHING)
            self.channelCountDO = channel.getDeviceChannelCount(ChannelClass.PHIDCHCLASS_DIGITALOUTPUT)
            self.channelCountDI = channel.getDeviceChannelCount(ChannelClass.PHIDCHCLASS_DIGITALINPUT)
            self.channelCountVI = channel.getDeviceChannelCount(ChannelClass.PHIDCHCLASS_VOLTAGEINPUT)
            self.channelCountVR = channel.getDeviceChannelCount(ChannelClass.PHIDCHCLASS_VOLTAGERATIOINPUT)
        # hub
        self.hubPort = channel.getHubPort()

    def __str__(self):
        return '<device ' + ' '.join(['%s=%s' % (x, getattr(self, x)) for x in vars(self)]) + '>'


class PhidgetFinder():
    def __init__(self, use_network=True):
        if use_network:
            Net.enableServerDiscovery(PhidgetServerType.PHIDGETSERVER_DEVICEREMOTE)
        self.manager = Manager()
        self.devices = set()

    def open(self):
        self.manager.open()
        self.manager.setOnAttachHandler(self.AttachHandler)
        self.manager.setOnDetachHandler(self.DetachHandler)

    def AttachHandler(self, manager, channel):
        newPh = PhidgetDevice(channel)
        self.devices.add(newPh)

    def DetachHandler(self, manager, channel):
        detachedDevice = channel
        serialNumber = detachedDevice.getDeviceSerialNumber()
        deviceName = detachedDevice.getDeviceName()
        print("Goodbye Device " + str(deviceName) + ", Serial Number: " + str(serialNumber))

    def getSerialNumbers(self, channelClass=None):
        numbers = set()
        for device in self.devices:
            if channelClass and device.channelClass != channelClass:
                continue

            numbers.add(device.serialNumber)
        return numbers

    def close(self):
        self.manager.close()

    def __del__(self):
        self.close()


def printReport(phType, devices):
    if phType == 'other':
        print('Other')
    else:
        print(ChannelClass.getName(phType))
    devList = {}
    if phType == 'other':
        for device in sorted(devices):
            if device.channelClass not in [5, 6, 13, 29, 31, 36]:
                print(device.deviceLabel)
                print(device.hubPort)
                print(device.channel)
                devKey = device.serverName + " : " + device.deviceName + " : " + str(device.channel)
                devList[devKey] = [device.deviceLabel, device.serialNumber, device.devicePort,
                                   ChannelClass.getName(device.channelClass), ChannelSubclass.getName(device.channelSubClass),
                                   device.serverIpAddr, device.hubPort, device.channel]
    else:
        for device in sorted(devices):
            if device.channelClass == phType:
                devKey = device.serverName + " : " + device.deviceName + " : " + str(device.channel)
                devList[devKey] = [device.deviceLabel, device.serialNumber, device.devicePort,
                                   ChannelClass.getName(device.channelClass), ChannelSubclass.getName(device.channelSubClass),
                                   device.serverIpAddr, device.hubPort, device.channel]

    for device in sorted(devList):
        print("%s | %s" % (device, devList[device]))

    print("\n")


def main():
    # Example on how to use this class
    finder = PhidgetFinder()
    finder.open()

    toSleep = 3
    print("Phidget Simple Playground (plug and unplug devices)")
    libraryVersion = Phidget.getLibraryVersion()
    print("Library Version: " + str(libraryVersion))
    print("Waiting for " + str(toSleep) + " seconds")

    time.sleep(toSleep)

    # printReport(ChannelClass.PHIDCHCLASS_DIGITALOUTPUT, finder.devices)
    # printReport(ChannelClass.PHIDCHCLASS_DIGITALINPUT, finder.devices)
    # printReport(ChannelClass.PHIDCHCLASS_VOLTAGEINPUT, finder.devices)
    # printReport('other', finder.devices)

    # matchString = '283587'
    matchString = '\d*'
    for device in sorted(finder.devices):
        if re.match(matchString, str(device.serialNumber)):
            print('\nNew Device: ' + device.deviceName + ' - ' + device.serverName)
            for var in sorted(vars(device)):
                value = getattr(device, var)
                # Check if we have an enumeration for this var...
                if var == "channelClass":
                    print('    %s = %s (%s)' % (var, value, ChannelClass.getName(value)))
                elif var == "channelSubClass":
                    print('    %s = %s (%s)' % (var, value, ChannelSubclass.getName(value)))
                elif var == "deviceId":
                    print('    %s = %s (%s)' % (var, value, DeviceID.getName(value)))
                elif var == "deviceClass":
                    print('    %s = %s (%s)' % (var, value, DeviceClass.getName(value)))
                # ... now print everything else
                else:
                    print('    %s = %s' % (var, value))

    finder.close()


if __name__ == "__main__":
    main()
