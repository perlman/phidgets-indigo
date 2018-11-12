#! /usr/bin/env python2.5
# -*- coding: utf-8 -*-
####################
# Copyright (c) 2011, Perceptive Automation, LLC. All rights reserved.
# http://www.perceptiveautomation.com

"""Portions Copyright 2010 Phidgets Inc.
This work is licensed under the Creative Commons Attribution 2.5 Canada License.
To view a copy of this license, visit http://creativecommons.org/licenses/by/2.5/ca/
"""

###  count x 1000/time(ms) = frequency(Hz)
import os
import sys
import time
from ctypes import *
import random
import datetime
import indigo
import threading
#Phidget specific imports
from Phidgets.Phidget import Phidget
from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException
from Phidgets.Events.Events import AttachEventArgs, DetachEventArgs, ErrorEventArgs, InputChangeEventArgs, OutputChangeEventArgs, SensorChangeEventArgs
from Phidgets.Devices.FrequencyCounter import FrequencyCounter


################################################################################
class frequencycounter(threading.Thread):
    ########################################
    def __init__(self, plugin, phDevId, phIpAddr, phIpPort, phSerial, triggerDict):
        self.plugin = plugin
        self.shutdown = False

        self.phDevId = phDevId
        self.ifKitDev = indigo.devices[phDevId]
        self.phDevName = self.ifKitDev.name
        self.phIpAddr = phIpAddr
        self.phIpPort = phIpPort
        self.phSerial = phSerial
        self.phDevice = indigo.devices[self.phDevId]
        self.typeDisplayName = self.plugin.pluginDisplayName + " FreqCounter"
        self.startup = True
        self.triggerDict = triggerDict
        self.lastStatusState = True
        self.isAttached = False

        # Setup some global info about this device so we don't have to do it every time the update handler is called
        try:
            if self.phDevice.pluginProps['fcUseCustom']:
                self.formula = lambda c, t: eval(self.phDevice.pluginProps['fcCustomFormula'])
                self.custStateName = self.phDevice.pluginProps['fcCustomName']
            else:
                self.formula = None
                self.custStateName = None

            self.counterIndex = int(self.phDevice.pluginProps['fcCounter'])
            self.useCustom = self.phDevice.pluginProps['fcUseCustom']
            self.customDecimal = int(self.phDevice.pluginProps['fcCustomDecimal'])
        except Exception, e:
            e1 = sys.exc_info()[0]
            self.plugin.errorLog('Error writing settings to the Phidget %s. Error code %s, %s' % (model, e, e1))

        if self.plugin.logLevel > 1: indigo.server.log('Initializing thread for device %s found: cust state name=%s, counterIndex=%i' % (self.phDevName, self.custStateName, self.counterIndex), type=self.typeDisplayName, isError=False)

        # ... and start the thread
        if self.plugin.logLevel > 1: indigo.server.log('Thread starting for: %s' % self.phDevName, type=self.typeDisplayName)
        threading.Thread.__init__(self)
        if self.plugin.logLevel > 1: indigo.server.log('Thread init finished for: %s' % self.phDevName, type=self.typeDisplayName)

    ########################################
    def __del__(self):
        pass

    ######################
    def initializeFrequencyCounter(self):
        logMsg = "Setting Frequency Counter Options"
        if self.plugin.logLevel > 1: indigo.server.log(logMsg, type=self.typeDisplayName)

        # Set the device options
        try:
            self.plugin.phidgetConnDict[self.phDevId].setEnabled(0, True)
            self.plugin.phidgetConnDict[self.phDevId].setFilter(0, int(self.phDevice.pluginProps['fcInType']))
            self.plugin.phidgetConnDict[self.phDevId].setTimeout(self.counterIndex, int(self.phDevice.pluginProps['fcTimeOut'])*1000)
        except Exception, e:
            e1 = sys.exc_info()[0]
            model = self.phDevice.pluginProps['phStandalonePhidgetModel']
            self.plugin.errorLog('Error writing settings to the Phidget %s. Error code %s, %s' % (model, e, e1))

    ######################
    def stop(self):
        if self.plugin.logLevel > 1: indigo.server.log('Thread init killed for: %s' % self.phDevName, type=self.typeDisplayName)
        self.shutdown = True

    ######################
    def run(self):
        if self.plugin.logLevel > 2: indigo.server.log('Thread run() called', type=self.typeDisplayName)

        #Event Handler Callback Functions
        def FrequencyCounterAttached(e):
            if self.plugin.logLevel > 1:
                indigo.server.log(u'Entered frequencyCounterAttached for device: %s' % (self.phDevName), type=self.typeDisplayName, isError=False)
            if self.plugin.logLevel > 0 and not self.startup:
                indigo.server.log(u'%s is now attached' % (self.phDevName), type=self.typeDisplayName, isError=False)

            self.isAttached = True
            if not self.startup: self.initializeFrequencyCounter()
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

        def FrequencyCounterDetached(e):
            if self.plugin.logLevel > 1:
                indigo.server.log(u'Entered FrequencyCounter Detached for device: %s' % (self.phDevName), type=self.typeDisplayName, isError=False)
            if self.plugin.logLevel > 0:
                indigo.server.log(u'FrequencyCounter %s has been detached' % (self.phDevName), type=self.typeDisplayName, isError=True)
            self.phDevice.setErrorStateOnServer(u'offline')
   
            for trigger in self.triggerDict:
                if self.plugin.logLevel > 2:
                    indigo.server.log(u'DEBUG: %s::%s::%s' % (trigger, self.triggerDict[trigger]['devid'],self.triggerDict[trigger]['event']), type=self.typeDisplayName, isError=False)
                if self.triggerDict[trigger]['devid'] == int(self.phDevId) and self.triggerDict[trigger]['event'] == 'detach':
                    self.plugin.triggerEvent(trigger, self.phDevId)

        def FrequencyCounterError(e):
            if self.plugin.logLevel > 1:
                indigo.server.log(u'Entered FrequencyCounterError for device: %s' % (self.phDevName), type=self.typeDisplayName, isError=False)
            try:
                source = e.device
                if source.isAttached():
                    self.plugin.errorLog("FrequencyCounter %i: Phidget Error %i: %s" % (source.getSerialNum(), e.eCode, e.description))
            except PhidgetException, e:
                # self.plugin.errorLog("FrequencyCounter Exception (FrequencyCounterError) %i: %s" % (e.code, e.details))
                time.sleep(5)
        if self.plugin.logLevel > 2: indigo.server.log('FrequencyCounter thread run() finished error handler declaration', type=self.typeDisplayName)

        def FrequencyCount(e):
            if e.index == self.counterIndex :
                source = e.device
                if self.plugin.logLevel > 1:
                    indigo.server.log(u'Entered FrequencyCounter count received for device: %s' % (self.phDevName), type=self.typeDisplayName, isError=False)
                    indigo.server.log(u'Frequency Counter %i: Count Detected -- Index %s: Time %i -- Counts %i' % (source.getSerialNum(), e.index, e.time, e.counts), type=self.typeDisplayName, isError=False)

                # Convert the time to ms (the input is in μs)
                fcTime  = float(e.time/1000)
                # Calculate the frequency (Hz)
                fcFreq = (e.counts * 1000)/fcTime

                now = datetime.datetime.now()

                self.phDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
                self.phDevice.updateStateOnServer(key='count', value=e.counts)
                self.phDevice.updateStateOnServer(key='time', value=fcTime, uiValue=str(fcTime) + ' ms')
                self.phDevice.updateStateOnServer(key='frequency', value=fcFreq, decimalPlaces=2, uiValue=str(round(fcFreq,2)) + ' Hz')
                if self.lastStatusState:
                    self.phDevice.updateStateOnServer(key='state', value=1)
                    self.lastStatusState = False
                else:
                    self.phDevice.updateStateOnServer(key='state', value=0)
                    self.lastStatusState = True

                # Update the custom fields, if they are enabled and have formulas
                if self.useCustom:
                    if self.plugin.logLevel > 2: indigo.server.log('Custom is true', type=self.typeDisplayName, isError=True)
                    customValue = self.formula(e.counts, fcTime)
                    self.phDevice.updateStateOnServer(key=self.custStateName, value=customValue, decimalPlaces=self.customDecimal, uiValue=str(round(float(customValue), self.customDecimal)) + '  ' + self.custStateName)

                if self.plugin.logLevel > 2: indigo.server.log('Frequency Counter %i: Count Detected -- Index %i: Time %i -- Counts %i  -- Freq %2.10f' % (source.getSerialNum(), e.index, myTime, e.counts, myFreq), type=self.typeDisplayName, isError=False)
            else:
                if self.plugin.logLevel > 2: indigo.server.log('The count update was not for our counter', type=self.typeDisplayName, isError=False)

        if self.plugin.logLevel > 2: indigo.server.log('FrequencyCounter thread run() finished count change handler declaration', type=self.typeDisplayName)

        """END OF HANDLERS"""

        if self.plugin.logLevel > 1:
            indigo.server.log(u'Start attach for device: %s' % (self.phDevName), type=self.typeDisplayName, isError=False)

        if self.plugin.phlibLogging:
            logMessage = 'Started thread for Phidgets FrequencyCounter device "' + indigo.devices[int(self.phDevId)].name + '"'

            try:
                Phidget.log(1, 'FrequencyCounter thread', logMessage)
            except:
                self.plugin.errorLog("Unexpected error:%s" % sys.exc_info()[0])

            if self.plugin.logLevel > 0:
                indigo.server.log(u'Low level phidgets libs logging started for device %s at level %s to file %s' %
                                 (indigo.devices[int(self.phDevId)].name, self.plugin.phlibLogLevel, self.plugin.phlibLogFile), type="Phidgets", isError=False)

        # Create an FrequencyCounter object
        try:
            self.plugin.phidgetConnDict[self.phDevId] = FrequencyCounter()
        except RuntimeError, e:
            self.plugin.errorLog("FrequencyCounter Exception (attach Handlers) %i: %s" % (e.code, e.details))
            self.plugin.errorLog("Exiting....")
            exit(1)
        if self.plugin.logLevel > 2: indigo.server.log('FrequencyCounter thread run() Created the FrequencyCounter object', type=self.typeDisplayName)

        try:
            self.plugin.phidgetConnDict[self.phDevId].setOnAttachHandler(FrequencyCounterAttached)
            self.plugin.phidgetConnDict[self.phDevId].setOnDetachHandler(FrequencyCounterDetached)
            self.plugin.phidgetConnDict[self.phDevId].setOnErrorhandler(FrequencyCounterError)
            self.plugin.phidgetConnDict[self.phDevId].setOnFrequencyCountHandler(FrequencyCount)
        except PhidgetException, e:
            self.plugin.errorLog("FrequencyCounter Exception (attach Handlers) %i: %s" % (e.code, e.details))
            self.plugin.errorLog("Exiting....")
            exit(1)
        if self.plugin.logLevel > 2: indigo.server.log('FrequencyCounter thread run() set all the handlers', type=self.typeDisplayName)

        #self.plugin.errorLog("FrequencyCounter: Ready to open Phidget")

        try:
            self.plugin.phidgetConnDict[self.phDevId].openRemoteIP(self.phIpAddr, self.phIpPort,  serial=self.phSerial)
        except PhidgetException, e:
            self.plugin.errorLog("FrequencyCounter Exception (Open Phidget) %i: %s" % (e.code, e.details))
            self.plugin.errorLog("Exiting....")
            exit(1)
        if self.plugin.logLevel > 1: indigo.server.log('FrequencyCounter thread run() opened the Phidget device', type=self.typeDisplayName)

        # try:
        #     self.plugin.phidgetConnDict[self.phDevId].waitForAttach(10000)
        # except PhidgetException, e:
        #     self.phDevice.setErrorStateOnServer(u'offline')
        #     self.plugin.errorLog("FrequencyCounter: Wait for Attach time exceeded for device %s" % (indigo.devices[int(self.phDevId)].name))
        #     self.plugin.errorLog("FrequencyCounter: Will continue waiting for 15 minutes")
        #     try:
        #         self.plugin.phidgetConnDict[self.phDevId].waitForAttach(900000)
        #     except PhidgetException, e:
        #         self.plugin.errorLog("FrequencyCounter: Maximum 15 min wait for Attach time exceeded from device %s" % (indigo.devices[int(self.phDevId)].name))
        #         self.plugin.errorLog("FrequencyCounter: Please disable communications for this device")
        #         try:
        #              self.plugin.phidgetConnDict[self.phDevId].closePhidget()
        #              exit(1)
        #         except PhidgetException, e:
        #             self.plugin.errorLog("FrequencyCounter Exception (Wait for Attach Close) from serial %s, %i: %s" % (source.getSerialNum(), e.code, e.details))
        #             self.plugin.errorLog("Exiting....")
        #             exit(1)

        startWaitAttachTime = time.time()

        while not self.isAttached:
            self.plugin.sleep(0.5)
            if time.time() - startWaitAttachTime > self.plugin.attachWaitTime:
                self.phDevice.setErrorStateOnServer(u'offline')
                self.plugin.errorLog("Frequency Counter: Could not attach to device %s. It has been set to offline" % (indigo.devices[int(self.phDevId)].name))
                self.plugin.threadAvailableDict[str(self.phDevId)] = {'threadUp': False}
                self.plugin.phidgetConnDict[self.phDevId].closePhidget()
                if self.plugin.logLevel > 0: indigo.server.log(u"Exiting Thread for ifKit device %s" % sensorDevice.name, type=self.typeDisplayName, isError=False)
                exit(1)

        # try:
        #     self.plugin.phidgetConnDict[self.phDevId].waitForAttach(10000)
        # except PhidgetException, e:
        #     self.phDevice.setErrorStateOnServer(u'offline')
        #     self.plugin.errorLog("FrequencyCounter Exception (Wait for Attach) from serial %s, %i: %s" % (self.phSerial, e.code, e.details))
        #     try:
        #          self.plugin.phidgetConnDict[self.phDevId].closePhidget()
        #          exit(1)
        #     except PhidgetException, e:
        #         self.plugin.errorLog("FrequencyCounter Exception (Wait for Attach Close) from serial %s, %i: %s" % (source.getSerialNum(), e.code, e.details))
        #         self.plugin.errorLog("Exiting....")
        #         exit(1)

        if self.plugin.logLevel > 2: indigo.server.log('FrequencyCounter thread run() phidget device attached', type=self.typeDisplayName)

        # Here is where we initialize the Freq Counter to the Device's property settings
        self.initializeFrequencyCounter()

        if self.plugin.logLevel > 0: indigo.server.log('Setup for device \"%s\" complete, listening for events' % indigo.devices[int(self.phDevId)].name, type=self.typeDisplayName)

        while not self.shutdown:
            self.plugin.sleep(0.5)

        if self.plugin.logLevel > 2: indigo.server.log('closing frequency counter')

        try:
            self.plugin.phidgetConnDict[self.phDevId].closePhidget()
        except PhidgetException, e:
            self.plugin.errorLog("FrequencyCounter Exception (Close Phidget) %i: %s" % (e.code, e.details))
            self.plugin.errorLog("Exiting....")

        now = datetime.datetime.now()
        self.phDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
        self.phDevice.updateStateOnServer(key='onOffState', value='offline')

        if self.plugin.logLevel > 0: indigo.server.log(u"Exiting Thread for ifKit device %s" % phDevice.name)

        exit(0)
