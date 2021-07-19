#! /usr/env/python

#
# Utility to scan for available phidgets
#

import time

from Phidget22.Devices.Manager import Manager
from Phidget22.Net import Net, PhidgetServerType
from Phidget22.ChannelClass import ChannelClass
from Phidget22.DeviceClass import DeviceClass
from Phidget22.Phidget import *


class PhidgetDevice():
    def __init__(self, channel):
        self.serialNumber = channel.getDeviceSerialNumber()
        self.deviceClass = channel.getDeviceClass()
        self.deviceName = channel.getDeviceName()
        self.sku = channel.getDeviceSKU()
        self.channelClass = channel.getChannelClass()
        self.channelSubClass = channel.getChannelSubclass()
        self.deviceId = channel.getDeviceID()
        self.channelName = channel.getChannelName()
        self.deviceLabel = channel.getDeviceLabel()

        if channel.getDeviceClass() == DeviceClass.PHIDCLASS_INTERFACEKIT:
            self.devicePort = channel.getChannel()
        else:
            self.devicePort = channel.getHubPort()

        if channel.getIsRemote():
            self.serverPeerName = channel.getServerPeerName()
            self.serverHostname = channel.getServerHostname()
            self.serverName = channel.getServerName()
            self.serverIpAddr = channel.getServerPeerName()
        else:
            self.serverPeerName = "Local"
            self.serverHostname = "Local"
            self.serverName = "Local"
            self.serverIpAddr = "Local"

        # print("server name: %s" % channel.getServerName())
        # print("server host name: %s" % channel.getServerHostname())
        # print("parent: %s" % channel.getParent())
        # print("peer: %s" % channel.getServerPeerName())
        # print("channel: %s" % channel.getChannel())
        # print("Channel Name: %s" % channel.getChannelName())
        # print("Unique Name: %s" % channel.getServerUniqueName())

        # print("Device Name: %s" % channel.getDeviceName())
        # print("Hub Port: %s" % channel.getHubPort())
        # print("Channel Class: %s" % channel.getChannelClass())
        # print("Device Class: %s" % channel.getDeviceClass())
        # try:
        #     print("Hub Port Count: %s" % channel.getHubPortCount())
        # except:
        #     print("Device Channel Count: %s" % channel.getDeviceChannelCount(ChannelClass.PHIDCHCLASS_NOTHING))
        #     print("DO Channel Count: %s" % channel.getDeviceChannelCount(ChannelClass.PHIDCHCLASS_DIGITALOUTPUT))
        #     print("DI Channel Count: %s" % channel.getDeviceChannelCount(ChannelClass.PHIDCHCLASS_DIGITALINPUT))
        #     print("AI Channel Count: %s" % channel.getDeviceChannelCount(ChannelClass.PHIDCHCLASS_VOLTAGEINPUT))
        #     print("ARI Channel Count: %s" % channel.getDeviceChannelCount(ChannelClass.PHIDCHCLASS_VOLTAGERATIOINPUT))

    def __str__(self):
        return '<device '+' '.join(['%s=%s' % (x, getattr(self, x)) for x in vars(self)]) + '>'


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


def main():
    # Example on how to use this class

    devList = {}
    finder = PhidgetFinder()
    finder.open()

    toSleep = 6
    print("Phidget Simple Playground (plug and unplug devices)")
    libraryVersion = Phidget.getLibraryVersion()
    print("Library Version: " + str(libraryVersion))
    print("Waiting for " + str(toSleep) + " seconds")

    time.sleep(toSleep)

    for phType in [ChannelClass.PHIDCHCLASS_DIGITALINPUT, ChannelClass.PHIDCHCLASS_DIGITALOUTPUT, ChannelClass.PHIDCHCLASS_VOLTAGEINPUT]:
        print(ChannelClass.getName(phType))
        devList = {}
        for device in sorted(finder.devices):
            if device.channelClass == phType:
                devKey = device.serverName + " : " + device.deviceName
                devList[devKey] = [device.deviceLabel, device.serialNumber, device.devicePort + 1, device.channelClass, device.serverIpAddr]

        for device in sorted(devList):
            print("%s | %s" % (device, devList[device]))

        print("\n")

    print("other")
    devList = {}
    for device in sorted(finder.devices):
        if device.channelClass not in [5, 6, 13, 29, 31, 36]:
            devKey = device.serverName + " : " + device.deviceName
            devList[devKey] = [device.deviceLabel, device.serialNumber, device.devicePort, device.channelClass, device.serverIpAddr]

    for device in sorted(devList):
        print("%s | %s" % (device, devList[device]))

    # for device in sorted(finder.devices):
    #     if device.deviceName != "Dictionary":
    #         if device.channelClass == ChannelClass.PHIDCHCLASS_DIGITALINPUT:
    #             print("DI: %s | %s | %s | %s" % (device.serialNumber, device.serverHostname, device.deviceName, device.devicePort))
    #         elif device.channelClass == ChannelClass.PHIDCHCLASS_DIGITALOUTPUT:
    #             print("DO: %s | %s | %s | %s" % (device.serialNumber, device.serverHostname, device.deviceName, device.devicePort))
    #         elif device.channelClass == ChannelClass.PHIDCHCLASS_VOLTAGEINPUT or device.channelClass == ChannelClass.PHIDCHCLASS_VOLTAGERATIOINPUT:
    #             print("AI: %s | %s | %s | %s" % (device.serialNumber, device.serverHostname, device.deviceName, device.devicePort))
    #         else:
    #             print("OTHER: %s | %s | %s" % (device.serialNumber, device.serverHostname, device.deviceName))

    # print("Available serial numbers are: %s" % list(finder.getSerialNumbers()))
    # print("Available serial numbers for devices with voltage input are : %s" \
    #  % list(finder.getSerialNumbers(channelClass=ChannelClass.PHIDCHCLASS_VOLTAGEINPUT)))

    finder.close()


if __name__ == "__main__":
    main()
