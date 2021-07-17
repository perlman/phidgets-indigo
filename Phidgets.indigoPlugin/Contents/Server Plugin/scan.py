#! /usr/env/python

#
# Utility to scan for available phidgets
#

import sys
import time

from Phidget22.Devices.Manager import Manager
from Phidget22.Net import Net, PhidgetServerType
from Phidget22.Devices.Log import Log
from Phidget22.ChannelClass import ChannelClass

class PhidgetDevice():
    def __init__(self, channel):
        self.serialNumber = channel.getDeviceSerialNumber()
        self.deviceClass = channel.getDeviceClass()
        self.deviceName = channel.getDeviceName()
        self.sku = channel.getDeviceSKU()
        self.channelClass = channel.getChannelClass()
        self.channelSubClass = channel.getChannelSubclass()
        self.deviceId = channel.getDeviceID()
        self.serverPeerName = channel.getServerPeerName()
        self.getChannelName = channel.getChannelName()

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
    finder = PhidgetFinder()
    finder.open()

    print("Phidget Simple Playground (plug and unplug devices)")
    print("Waiting for 3 seconds")

    time.sleep(2)

    for device in finder.devices:
        print(device)

    print("Available serial numbers are: %s" % list(finder.getSerialNumbers()))
    print("Available serial numbers for devices with voltage input are : %s" % list(finder.getSerialNumbers(channelClass=ChannelClass.PHIDCHCLASS_VOLTAGEINPUT)))


    finder.close()


if __name__ == "__main__":
    main()
