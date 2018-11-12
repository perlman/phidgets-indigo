#! /usr/bin/env python2.5
# -*- coding: utf-8 -*-
####################
# Copyright (c) 2011, Perceptive Automation, LLC. All rights reserved.
# http://www.perceptiveautomation.com

"""Portions Copyright 2010 Phidgets Inc.
This work is licensed under the Creative Commons Attribution 2.5 Canada License.
To view a copy of this license, visit http://creativecommons.org/licenses/by/2.5/ca/
"""

import sys
import time
from time import sleep
from ctypes import *
import datetime
import indigo
import threading
import math
#Phidget specific imports
from Phidgets.Phidget import Phidget
from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException
from Phidgets.Events.Events import AttachEventArgs, DetachEventArgs, ErrorEventArgs, InputChangeEventArgs, OutputChangeEventArgs, SensorChangeEventArgs
from Phidgets.Devices.InterfaceKit import InterfaceKit as CircularTouch

kDirArray = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]

################################################################################
class circulartouch(threading.Thread):
    ########################################
    def __init__(self, plugin, phDevId, phIpAddr, phIpPort, phSerial, triggerDict):
        self.plugin = plugin
        self.shutdown = False
        #if self.plugin.logLevel > 3:
        #   self.plugin.debugLog("CONNECTIONS DICT = %s" % self.plugin.connectionsDict)

        self.phDevice = indigo.devices[phDevId]

        self.phDevId = phDevId
        self.phDevName = self.phDevice.name
        self.phIpAddr = phIpAddr
        self.phIpPort = phIpPort
        self.phSerial = phSerial
        self.typeDisplayName = self.plugin.pluginDisplayName + " circularTouch"
        self.decimalPlaces = int(self.phDevice.pluginProps['fcCustomDecimal'])
        self.centerTop = int(self.phDevice.pluginProps['circularTouchTop'])  
        posLabels = self.phDevice.pluginProps['posLabels'].replace(' ','')  
        self.posLabels = posLabels.split(',')
        self.isAttached  = False
        self.startup = True
        self.errorCount = 0

        if self.plugin.logLevel > 1: indigo.server.log('Thread starting for: %s' % self.phDevName, type=self.typeDisplayName)
        threading.Thread.__init__(self)
        if self.plugin.logLevel > 1: indigo.server.log('Thread init finished for: %s' % self.phDevName, type=self.typeDisplayName)

    def __del__(self):
        pass

    ######################
    def initializeCircularTouch(self):
        logMsg = "Setting CircularTouch Options"
        if self.plugin.logLevel > 1: indigo.server.log(logMsg, type=self.typeDisplayName)
        
        if self.plugin.logLevel > 2: indigo.server.log(u'Starting threshold setting for: %s' % (self.phDevice.name), type=self.typeDisplayName, isError=False)
  
        aTrigger = int(self.phDevice.pluginProps['circularTouchSensorTrigger'])
        self.plugin.phidgetConnDict[self.phDevId].setSensorChangeTrigger(0, aTrigger)

        if self.plugin.logLevel > 2:
            indigo.server.log('Setup for device \"%s\" complete, listening for events' % self.phDevice.name, type=self.typeDisplayName)

    ######################
    def stop(self):
        if self.plugin.logLevel > 1: indigo.server.log('Thread init killed for: %s' % self.phDevName, type=self.typeDisplayName)
        self.shutdown = True

    ######################
    def run(self):
        if self.plugin.logLevel > 2: indigo.server.log('Thread run() called', type=self.typeDisplayName)
        # DEFINE HANDLERS

        def CircularTouchAttached(e):
            if self.plugin.logLevel > 1:
                indigo.server.log(u'Entered circularTouchAttached for device: %s' % (self.phDevName), type=self.typeDisplayName, isError=False)
            if self.plugin.logLevel > 0 and not self.startup:
                indigo.server.log(u'circularTouch "%s" is now attached' % (self.phDevName), type=self.typeDisplayName, isError=False)

            self.isAttached  = True
         
            if not self.startup: self.initializeCircularTouch()

            self.phDevice.setErrorStateOnServer(None)
            now = datetime.datetime.now()
            self.phDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
            self.phDevice.updateStateOnServer(key='onOffState', value='online')

            self.startup = False

        def CircularTouchDetached(e):
            if self.plugin.logLevel > 1:
                indigo.server.log(u'Entered CircularTouchDetached for device: %s' % (self.phDevName), type=self.typeDisplayName, isError=False)
            if self.plugin.logLevel > 0:
                indigo.server.log(u'CircularTouch "%s" has been detached' % (self.phDevName), type=self.typeDisplayName, isError=True)
            self.phDevice.setErrorStateOnServer(u'offline')

            self.isAttached  = False

        def CircularTouchError(e):
            if self.plugin.logLevel > 1:
                indigo.server.log(u'Entered CircularTouchError for device: %s' % (self.phDevName), type=self.typeDisplayName, isError=False)

            try:
                source = e.device
                self.plugin.debugLog("CircularTouch %i: Phidget Error %i: %s" % (source.getSerialNum(), e.eCode, e.description))
            except PhidgetException, e:
                self.plugin.errorLog("circularTouch Exception (circularTouch Error) from serial %s, %i: %s" % (source.getSerialNum(), e.code, e.details))
                time.sleep(2)

            if self.plugin.logLevel > 2: indigo.server.log('circularTouch thread run() finished error handler declaration', type=self.typeDisplayName)

        def CircularTouchSensorChanged(e):
            try:
                source = e.device
                deviceName = source.getDeviceName()
                serial = str(source.getSerialNum())

                value = e.value # int(abs(e.value - 1000)) # Reversed order of raw data

                # if int(value - self.centerTop) < 0: # corrected for orientation
                #     value = int(abs(value - self.centerTop))
                # else:
                #     value = int(1000 - (value - self.centerTop))

                if int(value + self.centerTop) <= 1000: # corrected for orientation
                    value = int(value + self.centerTop)
                else:
                    value = int(abs(1000 - (value + self.centerTop)))
                
                degreePos = int(value/2.777777)
                headingIn = int((degreePos/22.5)+0.5)
                heading = self.posLabels[int(headingIn) % 16]

                now = datetime.datetime.now()


                if self.plugin.logLevel > 2:
                    indigo.server.log(u'Entered CircularTouchSensorChanged for device: %s, value: %s' % (self.phDevName, value), type=self.typeDisplayName, isError=False)

                if self.plugin.logLevel > 2:
                    indigo.server.log(u"Sensor details for:%s, , devid %s, connector %s" % (deviceName, self.phDevice.id, port), type=self.typeDisplayName)
                else:
                    self.plugin.debugLog("Entered sensor change handlers")

                # set the circularTouch last update time and position value
                self.phDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
                self.phDevice.updateStateOnServer(key='pAbsValue', value=float(value), decimalPlaces=self.decimalPlaces)
                self.phDevice.updateStateOnServer(key='pDegrees', value=float(degreePos), decimalPlaces=self.decimalPlaces)
                self.phDevice.updateStateOnServer(key='pHeading', value=heading, decimalPlaces=self.decimalPlaces)

                if self.plugin.logLevel > 2: indigo.server.log('circularTouch thread run() finished sensor change handler declaration', type=self.typeDisplayName)
            except Exception, e:
                self.plugin.errorLog("Sensor change error:%s" % e)

        def CircularTouchInputChanged(e):
            try:
                source = e.device
                port = e.index
                #  deviceName = source.getDeviceName()

                if port == 0:
                    stateName = 'iContact'
                elif port == 1:
                    stateName = 'iProximity'
                else:
                    exit(1)

                value = False  # "off"
                if e.state:
                    value = True  # "on"
                self.phDevice.updateStateOnServer(key=stateName, value=value)

                if self.plugin.logLevel > 2:
                    indigo.server.log(u'Entered CircularTouchInputChanged for device: %s, index: %s' % (self.phDevName, port), type=self.typeDisplayName, isError=False)
            except Exception, e:
                self.plugin.errorLog("Input change error:%s" % e)

            if self.plugin.logLevel > 2: indigo.server.log('circularTouch thread run() finished input change handler declaration', type=self.typeDisplayName)

        if self.plugin.logLevel > 2: indigo.server.log('circularTouch thread run() finished handler declarations', type=self.typeDisplayName)

        # End of handlers
        #
        # Start of connection function
        if self.plugin.logLevel > 1:
            indigo.server.log(u'Start attach for device: %s' % (self.phDevName), type=self.typeDisplayName, isError=False)

        if self.plugin.phlibLogging:
            logMessage = 'Started thread for Phidgets circularTouch device "' + indigo.devices[int(self.phDevId)].name + '"'

            try:
                Phidget.log(1, 'circularTouch thread', logMessage)
            except NameError, e:
                self.plugin.errorLog("error message: %s" % (e))
            except:
                self.plugin.errorLog("Unexpected error:%s for device %s" % (sys.exc_info()[0], indigo.devices[int(self.phDevId)].name))

            if self.plugin.logLevel > 2:
                indigo.server.log(u'Low level phidgets libs logging started for device %s at level %s to file %s' %\
                (indigo.devices[int(self.phDevId)].name, self.plugin.phlibLogLevel, self.plugin.phlibLogFile), type="Phidgets", isError=False)

        try:
            if self.plugin.logLevel > 2: indigo.server.log("Creating CircularTouch for serial: %s" % (self.phSerial), type=self.typeDisplayName)
            self.plugin.phidgetConnDict[self.phDevId] = CircularTouch()
        except RuntimeError, e:
            self.plugin.errorLog("Runtime Exception: %s" % e.details)
            self.plugin.errorLog("Exiting....")
            exit(1)
        if self.plugin.logLevel > 2: indigo.server.log('circularTouch thread run() Created the circularTouch object', type=self.typeDisplayName)

        try:
            self.plugin.phidgetConnDict[self.phDevId].setOnAttachHandler(CircularTouchAttached)
            self.plugin.phidgetConnDict[self.phDevId].setOnDetachHandler(CircularTouchDetached)
            self.plugin.phidgetConnDict[self.phDevId].setOnErrorhandler(CircularTouchError)
            self.plugin.phidgetConnDict[self.phDevId].setOnInputChangeHandler(CircularTouchInputChanged)
            self.plugin.phidgetConnDict[self.phDevId].setOnSensorChangeHandler(CircularTouchSensorChanged)
        except Exception, e:
            indigo.server.log("circularTouch Exception (Attach Handlers) from serial %s, %s" % (self.phSerial, e), type=self.typeDisplayName, isError=True)
            self.plugin.errorLog("Exiting....")
            exit(1)
        except PhidgetException, e:
            indigo.server.log("circularTouch Exception (Attach Handlers) from serial %s, %i: %s" %
                             (self.phSerial, e.code, e.details), type=self.typeDisplayName, isError=True)
            self.plugin.errorLog("Exiting....")
            exit(1)
        if self.plugin.logLevel > 2: 
            indigo.server.log('circularTouch thread run() set all the handlers', type=self.typeDisplayName)

        if self.plugin.logLevel > 2: self.plugin.debugLog("Opening phidget object....")

        try:
            self.plugin.phidgetConnDict[self.phDevId].openRemoteIP(self.phIpAddr, self.phIpPort, serial=self.phSerial)
        except PhidgetException, e:
            indigo.server.log("circularTouch Exception (Open circularTouch) from serial %s, %i: %s" % (self.phSerial, e.code, e.details), type=self.typeDisplayName, isError=True)
            self.plugin.errorLog("Exiting....")
            exit(1)
        if self.plugin.logLevel > 2: indigo.server.log('circularTouch thread run() opened the Phidget device', type=self.typeDisplayName)

        # try:
        #     self.plugin.phidgetConnDict[self.phDevId].waitForAttach(10000)
        # except PhidgetException, e:
        #     self.phDevice.setErrorStateOnServer(u'offline')
        #     self.plugin.errorLog("CircularTouch: Wait for Attach time exceeded for device %s" % (indigo.devices[int(self.phDevId)].name))
        #     self.plugin.errorLog("CircularTouch: Will continue waiting for 15 minutes")
        #     try:
        #         self.plugin.phidgetConnDict[self.phDevId].waitForAttach(900000)
        #     except PhidgetException, e:
        #         self.plugin.errorLog("CircularTouch: Maximum 15 min wait for Attach time exceeded from device %s" % (indigo.devices[int(self.phDevId)].name))
        #         self.plugin.errorLog("CircularTouch: Please disable communications for this device")
        #         try:
        #              self.plugin.phidgetConnDict[self.phDevId].closePhidget()
        #              exit(1)
        #         except PhidgetException, e:
        #             self.plugin.errorLog("CircularTouch Exception (Wait for Attach Close) from serial %s, %i: %s" % (source.getSerialNum(), e.code, e.details))
        #             self.plugin.errorLog("Exiting....")
        #             exit(1)

        startWaitAttachTime = time.time()

        while not self.isAttached:
            self.plugin.sleep(0.5)
            if time.time() - startWaitAttachTime > self.plugin.attachWaitTime:
                self.phDevice.setErrorStateOnServer(u'offline')
                self.plugin.errorLog("CircularTouch: Could not attach to device %s. It has been set to offline" % (indigo.devices[int(self.phDevId)].name))
                self.plugin.threadAvailableDict[str(self.phDevId)] = {'threadUp': False}
                self.plugin.phidgetConnDict[self.phDevId].closePhidget()
                if self.plugin.logLevel > 0: indigo.server.log(u"Exiting Thread for ifKit device %s" % sensorDevice.name, type=self.typeDisplayName, isError=False)
                exit(1)

        if self.plugin.logLevel > 2: indigo.server.log('circularTouch thread run() phidget device attached', type=self.typeDisplayName)

        # Now that the circularTouch is up, we need to set the change trigger and data rate settings
        self.initializeCircularTouch()

        self.plugin.threadAvailableDict[str(self.phDevId)] = {'threadUp': True}

        if self.plugin.logLevel > 0:
            indigo.server.log('Setup for CircularTouch "%s" complete, device Available' % indigo.devices[int(self.phDevId)].name, type=self.typeDisplayName)

        # Ok, we're running, let the world know
        self.plugin.threadAvailableDict[str(self.phDevId)] = {'threadUp': True}

        while not self.shutdown:
            self.plugin.sleep(0.5)

        # and now let the world know we've stopped
        self.plugin.threadAvailableDict[str(self.phDevId)] = {'threadUp': False}

        if self.pluplugin.logLevel > 1: indigo.server.log('closing CircularTouch')

        self.plugin.phidgetConnDict[self.phDevId].closePhidget()

        now = datetime.datetime.now()
        self.phDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
        self.phDevice.updateStateOnServer(key='onOffState', value='offline')
        if self.plugin.logLevel > 0: indigo.server.log(u"Exiting Thread for circularTouch device %s" % self.phDevice.name, type=self.typeDisplayName, isError=False)
