#! /usr/bin/env python2.5
# -*- coding: utf-8 -*-
####################
# Copyright (c) 2013, Berkinet - Richard Perlman

"""Portions Copyright 2010 Phidgets Inc.
This work is licensed under the Creative Commons Attribution 2.5 Canada License.
To view a copy of this license, visit http://creativecommons.org/licenses/by/2.5/ca/
"""

import sys
import time
from ctypes import *
import datetime
import indigo
import threading
#Phidget specific imports
from Phidgets.Phidget import Phidget
from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException
from Phidgets.Events.Events import AttachEventArgs, DetachEventArgs, ErrorEventArgs, InputChangeEventArgs, OutputChangeEventArgs, SensorChangeEventArgs
from Phidgets.Devices.RFID import RFID


################################################################################
class rfid(threading.Thread):
    ########################################
    def __init__(self, plugin, phDevId, phIpAddr, phIpPort, phSerial, triggerDict):
        self.plugin = plugin
        self.shutdown = False
        if self.plugin.logLevel > 2: indigo.server.log('RFID thread starting', type="self.typeDisplayName")
        #if self.plugin.logLevel > 3:
        #   self.plugin.debugLog("CONNECTIONS DICT = %s" % self.plugin.connectionsDict)

        self.phDevId = phDevId
        self.phDevice = indigo.devices[self.phDevId]
        self.phDevName = self.phDevice.name
        self.phIpAddr = phIpAddr
        self.phIpPort = phIpPort
        self.phSerial = phSerial
        self.triggerDict = triggerDict

        self.typeDisplayName = self.plugin.pluginDisplayName + " rfid"
        self.startup = True

        threading.Thread.__init__(self)
        if self.plugin.logLevel > 2: indigo.server.log('RFID thread init finished', type="self.typeDisplayName")
  
    ######################
    def __del__(self):
        pass

    ######################
    def initializeRfidReader(self):
        logMsg = "Setting Frequency Counter Options"
        if self.plugin.logLevel > 1: indigo.server.log(logMsg, type=self.typeDisplayName)

        # Set the device options
        logMsg = "RFID Turning on the Antenna"
        if self.plugin.logLevel > 2: indigo.server.log(logMsg, type="self.typeDisplayName")
        self.plugin.phidgetConnDict[self.phDevId].setAntennaOn(True)
        self.phDevice.updateStateOnServer(key='antenna', value='on')

        ledOnState = self.plugin.phidgetConnDict[self.phDevId].getLEDOn()
        self.phDevice.updateStateOnServer(key='onboardLED', value=ledOnState)

        try:
            lastTag = self.plugin.phidgetConnDict[self.phDevId].getLastTag()
            logMsg = "RFID " + source.getSerialNum() + "Last Tag read was: %s" + lastTag.lower()
            if self.plugin.logLevel > 0: indigo.server.log(logMsg, type="self.typeDisplayName")
        except PhidgetException, e:
            logMsg = "RFID " + ": Last Tag not available (not yet received from device, or not yet set by user)"
            indigo.server.log(logMsg, type="self.typeDisplayName")

    ######################
    def stop(self):
        self.plugin.debugLog('stopRFIDThread Called')
        self.shutdown = True

    ######################
    def writeDigitalOutput(self, index, state):
        self.plugin.debugLog("RFID write digital out received request: Set index:%s to %s" % (index, state))
        try:
            self.plugin.phidgetConnDict[self.phDevId].setOutputState(index, state)
        except:
            raise
        if self.plugin.logLevel > 2: self.plugin.debugLog("RFID: write digital out Set index:%s to %s" % (index, state))

    ######################
    def run(self):
        if self.plugin.logLevel > 2: indigo.server.log('RFID thread run() called', type="self.typeDisplayName")
        # DEFINE HANDLERS

        def rfidAttached(e):
            # attached = e.device
            if self.plugin.logLevel > 1:
                indigo.server.log(u'Entered rfidAttached for device: %s' % (self.phDevName), type=self.typeDisplayName, isError=False)
            if self.plugin.logLevel > 0 and not self.startup:
                indigo.server.log(u'RFID Reader %s is now attached' % (self.phDevName), type=self.typeDisplayName, isError=False)

            if not self.startup:  self.initializeRfidReader()
            
            self.startup = False
            self.phDevice.setErrorStateOnServer(None)
            now = datetime.datetime.now()
            self.phDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
            self.phDevice.updateStateOnServer(key='onOffState', value='online')
            
            for trigger in self.triggerDict:
                if self.plugin.logLevel > 2:
                    indigo.server.log(u'DEBUG: %s::%s::%s' % (trigger, self.triggerDict[trigger]['devid'],self.triggerDict[trigger]['event']), type=self.typeDisplayName, isError=False)
                if self.triggerDict[trigger]['devid'] == int(self.phDevId) and self.triggerDict[trigger]['event'] == 'attach':
                    self.plugin.triggerEvent(trigger, self.phDevId)

        def rfidDetached(e):
            if self.plugin.logLevel > 1:
                indigo.server.log(u'Entered rfidDetached for device: %s' % (self.phDevName), type=self.typeDisplayName, isError=False)
            if self.plugin.logLevel > 0:
                indigo.server.log(u'RFID Reader %s has been detached' % (self.phDevName), type=self.typeDisplayName, isError=True)
            self.phDevice.setErrorStateOnServer(u'offline')

            for trigger in self.triggerDict:
                if self.plugin.logLevel > 2:
                    indigo.server.log(u'DEBUG: %s::%s::%s' % (trigger, self.triggerDict[trigger]['devid'],self.triggerDict[trigger]['event']), type=self.typeDisplayName, isError=False)
                if self.triggerDict[trigger]['devid'] == int(self.phDevId) and self.triggerDict[trigger]['event'] == 'detach':
                    self.plugin.triggerEvent(trigger, self.phDevId)
                    
        def rfidError(e):
            try:
                source = e.device
                self.plugin.errorLog("RFID %i: Phidget Error %i: %s" % (source.getSerialNum(), e.eCode, e.description))
            except PhidgetException, e:
                self.plugin.errorLog("RFID Exception (rfidError) %i: %s" % (e.code, e.details))
                time.sleep(5)

        def rfidOutputChanged(e):
            source = e.device
            self.plugin.debugLog("RFID %i: Output %i State: %s" % (source.getSerialNum(), e.index, e.state))

            #now = datetime.datetime.now()
            #self.phDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
            self.phDevice.updateStateOnServer(key='output' + str(e.index), value=str(e.state))
            if self.plugin.logLevel > 0: indigo.server.log('RFID: Output Change Handler. Index:%s changed to:%s' % (str(e.index), str(e.state)), type="self.typeDisplayName")

        def rfidTagGained(e):
            source = e.device
            deviceName = source.getDeviceName()
            serial = int(source.getSerialNum())
            self.plugin.debugLog('Entered RFID Tag Gained handler')

            if self.plugin.logLevel > 2:
                self.plugin.debugLog('Entered RFID Tag Gained handler for:%s, serial:%s' % (deviceName, serial))
            else:
                self.plugin.debugLog("Entered RFID Tag Gained handler")

            #rfid.setLEDOn(1)
            #if serial in self.plugin.phRFIDDict:
            tagValue = e.tag.lower()
            self.plugin.debugLog('RFID Tag Gained handler found tag:%s' % (tagValue))
            now = datetime.datetime.now()
            self.phDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
            self.phDevice.updateStateOnServer(key='currentTag', value=tagValue)

            logMsg = "RFID tag " + tagValue + " read on reader " + str(source.getSerialNum())
            if self.plugin.logLevel > 0: indigo.server.log(logMsg, type="self.typeDisplayName")

        def rfidTagLost(e):
            source = e.device
            deviceName = source.getDeviceName()
            serial = int(source.getSerialNum())

            if self.plugin.logLevel > 2:
                self.plugin.debugLog("Entered RFID Tag Lost handler for:%s, serial:%s" % (deviceName, serial))
            else:
                self.plugin.debugLog("Entered RFID Tag Lost handler")

            #rfid.setLEDOn(1)
            #if serial in self.plugin.phRFIDDict:
            tagValue = e.tag.lower()

            #now = datetime.datetime.now()
            #self.phDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
            self.phDevice.updateStateOnServer(key='lastTag', value=tagValue)

            logMsg = "RFID tag " + tagValue + " lost on reader " + str(source.getSerialNum())
            if self.plugin.logLevel > 2: indigo.server.log(logMsg, type="self.typeDisplayName")

        if self.plugin.logLevel > 2: indigo.server.log('RFID thread run() finished handler declarations', type="self.typeDisplayName")

        """
        END OF HANDLERS
        self.plugin.errorLog("RFID: Create an RFID object")
        Create an RFID object
        """

        if self.plugin.phlibLogging:
            logMessage = 'Started thread for Phidgets RFID device "' + indigo.devices[int(self.phDevId)].name + '"'

            try:
                Phidget.log(1, 'RFID thread', logMessage)
            except:
                self.plugin.errorLog("Unexpected error:%s" % sys.exc_info()[0])

            if self.plugin.logLevel > 0:
                indigo.server.log(u'Low level phidgets libs logging started for device %s at level %s to file %s' %\
                (indigo.devices[int(self.phDevId)].name, self.plugin.phlibLogLevel, self.plugin.phlibLogFile), type="Phidgets", isError=False)

        try:
            self.plugin.phidgetConnDict[self.phDevId] = RFID()
        except RuntimeError, e:
            self.plugin.errorLog("Runtime Exception: %s" % e.details)
            self.plugin.errorLog("Exiting....")
            exit(1)
        if self.plugin.logLevel > 2: indigo.server.log('RFID thread run() Created the RFID object', type="self.typeDisplayName")

        #Main Program Code
        try:
            self.plugin.phidgetConnDict[self.phDevId].setOnAttachHandler(rfidAttached)
            self.plugin.phidgetConnDict[self.phDevId].setOnDetachHandler(rfidDetached)
            self.plugin.phidgetConnDict[self.phDevId].setOnErrorhandler(rfidError)
            self.plugin.phidgetConnDict[self.phDevId].setOnOutputChangeHandler(rfidOutputChanged)
            self.plugin.phidgetConnDict[self.phDevId].setOnTagHandler(rfidTagGained)
            self.plugin.phidgetConnDict[self.phDevId].setOnTagLostHandler(rfidTagLost)
        except PhidgetException, e:
            self.plugin.errorLog("RFID Exception (attach Handlers) %i: %s" % (e.code, e.details))
            self.plugin.errorLog("Exiting....")
            exit(1)
        if self.plugin.logLevel > 2: indigo.server.log('RFID thread run() set all the handlers', type="self.typeDisplayName")

        #self.plugin.errorLog("RFID: Ready to open Phidget")
        try:
            #rfid.openPhidget()
            self.plugin.phidgetConnDict[self.phDevId].openRemoteIP(self.phIpAddr, self.phIpPort, serial=self.phSerial)
        except PhidgetException, e:
            self.plugin.errorLog("RFID Reader Exception (Open Phidget) %i: %s" % (e.code, e.details))
            self.plugin.errorLog("Exiting....")
            exit(1)
        if self.plugin.logLevel > 2: indigo.server.log('RFID thread run() opened the Phidget device', type="self.typeDisplayName")
        self.plugin.debugLog("Waiting for attach....")

        # try:
        #     self.plugin.phidgetConnDict[self.phDevId].waitForAttach(10000)
        # except PhidgetException, e:
        #     self.phDevice.setErrorStateOnServer(u'offline')
        #     self.plugin.errorLog("RFID Reader: Wait for Attach time exceeded for device %s" % (indigo.devices[int(self.phDevId)].name))
        #     self.plugin.errorLog("RFID Reader: Will continue waiting for 15 minutes")
        #     try:
        #         self.plugin.phidgetConnDict[self.phDevId].waitForAttach(900000)
        #     except PhidgetException, e:
        #         self.plugin.errorLog("RFID Reader: Maximum 15 min wait for Attach time exceeded from device %s" % (indigo.devices[int(self.phDevId)].name))
        #         self.plugin.errorLog("RFID Reader: Please disable communications for this device")
        #         try:
        #              self.plugin.phidgetConnDict[self.phDevId].closePhidget()
        #              exit(1)
        #         except PhidgetException, e:
        #             self.plugin.errorLog("RFID Reader Exception (Wait for Attach Close) from serial %s, %i: %s" % (source.getSerialNum(), e.code, e.details))
        #             self.plugin.errorLog("Exiting....")
        #             exit(1)
        startWaitAttachTime = time.time()

        while not self.isAttached:
            self.plugin.sleep(0.5)
            if time.time() - startWaitAttachTime > self.plugin.attachWaitTime:
                self.phDevice.setErrorStateOnServer(u'offline')
                self.plugin.errorLog("RFID Reader: Could not attach to device %s. It has been set to offline" % (indigo.devices[int(self.phDevId)].name))
                self.plugin.threadAvailableDict[str(self.phDevId)] = {'threadUp': False}
                self.plugin.phidgetConnDict[self.phDevId].closePhidget()
                if self.plugin.logLevel > 0: indigo.server.log(u"Exiting Thread for ifKit device %s" % sensorDevice.name, type=self.typeDisplayName, isError=False)
                exit(1)

        # try:
        #     self.plugin.phidgetConnDict[self.phDevId].waitForAttach(10000)
        # except PhidgetException, e:
        #     self.phDevice.setErrorStateOnServer(u'offline')
        #     self.plugin.errorLog("RFID Reader Exception (Wait for Attach) from serial %s, %i: %s" % (self.phSerial, e.code, e.details))
        #     try:
        #         self.plugin.phidgetConnDict[self.phDevId].closePhidget()
        #         exit(1)
        #     except PhidgetException, e:
        #         self.plugin.errorLog("RFID Reader  Exception (Wait for Attach Close) from serial %s, %i: %s" % (source.getSerialNum(), e.code, e.details))
        #         self.plugin.errorLog("Exiting....")
        #         exit(1)
        if self.plugin.logLevel > 2: indigo.server.log('RFID thread run() phidget device attached', type="self.typeDisplayName")

        self.initializeRfidReader()

        # logMsg = "RFID Turning on the Antenna"
        # if self.plugin.logLevel > 2: indigo.server.log(logMsg, type="self.typeDisplayName")
        # self.plugin.phidgetConnDict[self.phDevId].setAntennaOn(True)
        # self.phDevice.updateStateOnServer(key='antenna', value='on')

        # ledOnState = self.plugin.phidgetConnDict[self.phDevId].getLEDOn()
        # self.phDevice.updateStateOnServer(key='onboardLED', value=ledOnState)

        # try:
        #     lastTag = self.plugin.phidgetConnDict[self.phDevId].getLastTag()
        #     logMsg = "RFID " + source.getSerialNum() + "Last Tag read was: %s" + lastTag.lower()
        #     if self.plugin.logLevel > 0: indigo.server.log(logMsg, type="self.typeDisplayName")
        # except PhidgetException, e:
        #     logMsg = "RFID " + ": Last Tag not available (not yet received from device, or not yet set by user)"
        #     indigo.server.log(logMsg, type="self.typeDisplayName")

        # now = datetime.datetime.now()
        # self.phDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
        # self.phDevice.updateStateOnServer(key='onOffState', value='online')

        self.plugin.debugLog("The result:%s" % self.plugin.phidgetConnDict[self.phDevId].getDeviceName())
        self.plugin.debugLog(u"Connection was successful")

        if self.plugin.logLevel > 0:
            #indigo.server.log('Setup complete, listening for events', type=self.typeDisplayName)
            indigo.server.log('Setup for device \"%s\" complete, listening for events' % indigo.devices[int(self.phDevId)].name, type="self.typeDisplayName")

        while not self.shutdown:
            self.plugin.sleep(0.5)
        if self.plugin.logLevel > 2: self.plugin.debugLog('RFID thread exiting')

        try:
            self.plugin.phidgetConnDict[self.phDevId].closePhidget()
        except PhidgetException, e:
            self.plugin.errorLog("RFID Exception (Close Phidget) %i: %s" % (e.code, e.details))
            self.plugin.errorLog("Exiting....")
            exit(1)

        now = datetime.datetime.now()
        self.phDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
        self.phDevice.updateStateOnServer(key='onOffState', value='offline')
        self.plugin.debugLog(u"Exiting Run Concurrent Thread")

        exit(0)
