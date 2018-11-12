#! /usr/bin/env python2.5
# -*- coding: utf-8 -*-
####################
# Copyright (c) 2011, Perceptive Automation, LLC. All rights reserved.
# http://www.perceptiveautomation.com

"""Portions Copyright 2010 Phidgets Inc.
This work is licensed under the Creative Commons Attribution 2.5 Canada License.
To view a copy of this license, visit http://creativecommons.org/licenses/by/2.5/ca/
"""

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
from Phidgets.Devices.TemperatureSensor import TemperatureSensor


################################################################################
class tempsensor(threading.Thread):
    ########################################
    def __init__(self, plugin, phDevId, phIpAddr, phIpPort, phSerial, triggerDict):
        self.plugin = plugin
        self.shutdown = False
        #if self.plugin.logLevel > 3:
        #   self.plugin.debugLog("CONNECTIONS DICT = %s" % self.plugin.connectionsDict)

        self.phDevId = phDevId
        self.ifKitDev = indigo.devices[phDevId]
        self.phDevName = self.ifKitDev.name
        self.phIpAddr = phIpAddr
        self.phIpPort = phIpPort
        self.phSerial = phSerial
        self.phDevice = indigo.devices[self.phDevId]
        self.typeDisplayName = self.plugin.pluginDisplayName + " TempSensor"
        self.startup = True
        self.triggerDict = triggerDict
        self.isAttached = False

        if self.plugin.logLevel > 1: indigo.server.log('Thread starting for: %s' % self.phDevName, type=self.typeDisplayName)

        threading.Thread.__init__(self)

        if self.plugin.logLevel > 1: indigo.server.log('Thread init finished for: %s' % self.phDevName, type=self.typeDisplayName)

    ######################
    def __del__(self):
        pass

    ######################
    def stop(self):
        if self.plugin.logLevel > 1: indigo.server.log('Thread init killed for: %s' % self.phDevName, type=self.typeDisplayName)
        self.shutdown = True

    ######################
    def initializeTempSensor(self):
        logMsg = "Setting temp sensor Options " 
        if self.plugin.logLevel > 1: indigo.server.log(logMsg, type=self.typeDisplayName)

        # Set the device options
        model = self.phDevice.pluginProps['phStandalonePhidgetModel']

        try:
            if model == '1048' or model == '1051':
                self.plugin.phidgetConnDict[self.phDevId].setThermocoupleType(0, int(self.phDevice.pluginProps['tCouple0']))
                self.plugin.phidgetConnDict[self.phDevId].setTemperatureChangeTrigger(0, float(self.phDevice.pluginProps['tSens0']))
            if model == '1048':
                self.plugin.phidgetConnDict[self.phDevId].setThermocoupleType(1, int(self.phDevice.pluginProps['tCouple1']))
                self.plugin.phidgetConnDict[self.phDevId].setTemperatureChangeTrigger(1, float(self.phDevice.pluginProps['tSens1']))
                self.plugin.phidgetConnDict[self.phDevId].setThermocoupleType(2, int(self.phDevice.pluginProps['tCouple2']))
                self.plugin.phidgetConnDict[self.phDevId].setTemperatureChangeTrigger(2, float(self.phDevice.pluginProps['tSens2']))
                self.plugin.phidgetConnDict[self.phDevId].setThermocoupleType(3, int(self.phDevice.pluginProps['tCouple3']))
                self.plugin.phidgetConnDict[self.phDevId].setTemperatureChangeTrigger(3, float(self.phDevice.pluginProps['tSens3']))
        except:
            self.plugin.errorLog('Error writing temp sensor settings to the Phidget %s' % model)

        if self.plugin.logLevel > 2:
            indigo.server.log(u'sense chg 0 = %s' % self.plugin.phidgetConnDict[self.phDevId].getTemperatureChangeTrigger(0), type='Phidgets temp sensor')
            indigo.server.log(u't-type  0 = %s' % self.plugin.phidgetConnDict[self.phDevId].getThermocoupleType(0), type='Phidgets temp sensor')
            indigo.server.log(u'sense chg 1 = %s' % self.plugin.phidgetConnDict[self.phDevId].getTemperatureChangeTrigger(1), type='Phidgets temp sensor')
            indigo.server.log(u't-type  1 = %s' % self.plugin.phidgetConnDict[self.phDevId].getThermocoupleType(1), type='Phidgets temp sensor')
            indigo.server.log(u'sense chg 2 = %s' % self.plugin.phidgetConnDict[self.phDevId].getTemperatureChangeTrigger(2), type='Phidgets temp sensor')
            indigo.server.log(u't-type  2 = %s' % self.plugin.phidgetConnDict[self.phDevId].getThermocoupleType(2), type='Phidgets temp sensor')
            indigo.server.log(u'sense chg 3 = %s' % self.plugin.phidgetConnDict[self.phDevId].getTemperatureChangeTrigger(3), type='Phidgets temp sensor')
            indigo.server.log(u't-type  3 = %s' % self.plugin.phidgetConnDict[self.phDevId].getThermocoupleType(3), type='Phidgets temp sensor')

    ######################
    def run(self):
        if self.plugin.logLevel > 2: indigo.server.log('Thread run() called', type=self.typeDisplayName)

        #Event Handler Callback Functions
        def TemperatureSensorAttached(e):
            if self.plugin.logLevel > 1:
                indigo.server.log(u'Entered TemperatureSensorAttached for device: %s' % (self.phDevName), type=self.typeDisplayName, isError=False)
            if self.plugin.logLevel > 0 and not self.startup:
                indigo.server.log(u'TempSensor %s is now attached' % (self.phDevName), type=self.typeDisplayName, isError=False)

            self.isAttached = True

            if not self.startup: self.initializeTempSensor()

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

        def TemperatureSensorDetached(e):
            if self.plugin.logLevel > 1:
                indigo.server.log(u'Entered TemperatureSensorDetached for device: %s' % (self.phDevName), type=self.typeDisplayName, isError=False)
            if self.plugin.logLevel > 0:
                indigo.server.log(u'TempSensor %s has been detached' % (self.phDevName), type=self.typeDisplayName, isError=True)
            self.phDevice.setErrorStateOnServer(u'offline')

            for trigger in self.triggerDict:
                if self.plugin.logLevel > 2:
                    indigo.server.log(u'DEBUG: %s::%s::%s' % (trigger, self.triggerDict[trigger]['devid'],self.triggerDict[trigger]['event']), type=self.typeDisplayName, isError=False)
                if self.triggerDict[trigger]['devid'] == int(self.phDevId) and self.triggerDict[trigger]['event'] == 'detach':
                    self.plugin.triggerEvent(trigger, self.phDevId)

        def TemperatureSensorError(e):
            if self.plugin.logLevel > 1:
                indigo.server.log(u'Entered TemperatureSensorError for device: %s' % (self.phDevName), type=self.typeDisplayName, isError=False)

            # See f we need to suppress 36871 (potential exceeded) for this device. But, first we need to extract the device indexout of the error message
            if e.eCode == 36871:
                errorString = e.description
                stringIndex = errorString.find('Thermocouple')
                if stringIndex >= 0:
                    # self.plugin.errorLog("TempSensor index: %i" % (stringIndex))
                    tIndex = errorString[stringIndex+13:stringIndex+14]
                    # self.plugin.errorLog("TempSensor Index: '%s'" % (tIndex))
                    eSuppress = self.phDevice.pluginProps['tError' + tIndex]
                    # self.plugin.errorLog("TempSensor suppress: '%s'" % (eSuppress))
                    if eSuppress:
                        if self.plugin.logLevel > 2: indigo.server.log('TempSensor thread error message: "%s", was supressed' % e.description, type=self.typeDisplayName)
                        return   
            try:
                source = e.device
                if source.isAttached():
                    self.plugin.errorLog("TempSensor %i: Phidget Error %i: %s" % (source.getSerialNum(), e.eCode, e.description))
            except PhidgetException, e:
                # self.plugin.errorLog("TempSensor Exception (TempSensorError) %i: %s" % (e.code, e.details))
                time.sleep(5)
        if self.plugin.logLevel > 2: indigo.server.log('TempSensor thread run() finished error handler declaration', type=self.typeDisplayName)

        def TemperatureSensorTemperatureChanged(e):
            if self.plugin.logLevel > 1:
                indigo.server.log(u'Entered TemperatureSensorTemperatureChanged for device: %s' % (self.phDevName), type=self.typeDisplayName, isError=False)

            ambient = 0.00
            source = e.device
            try:
                ambient = self.plugin.phidgetConnDict[self.phDevId].getAmbientTemperature()
                if self.plugin.logLevel > 2: indigo.server.log("TempSensor  %i: Ambient Temp: %f -- Thermocouple %i temperature: %f -- Potential: %f" % (source.getSerialNum(), ambient, e.index, e.temperature, e.potential))
            except PhidgetException, e:
                self.plugin.errorLog("TempSensor Exception (TempSensorError) %i: %s" % (e.code, e.details))

            # See if we need to convert anything to Fahrenheit
            if self.phDevice.pluginProps['ambientScale'] == 'fahrenheit':
                ambient = 9.0/5.0 * ambient + 32

            if self.phDevice.pluginProps['tScale' + str(e.index)] == 'fahrenheit':
                temp = 9.0/5.0 * e.temperature + 32
            else:
                temp = e.temperature

            # Now fx any readings that are "off the scale"
            if e.temperature < -50 or e.temperature > 785:
                temp = "n/a"

            now = datetime.datetime.now()
            self.phDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
            self.phDevice.updateStateOnServer(key='ambient', value=ambient, decimalPlaces=int(self.phDevice.pluginProps['tDecimal']))
            self.phDevice.updateStateOnServer(key='temp' + str(e.index), value=temp, decimalPlaces=int(self.phDevice.pluginProps['tDecimal']))

            if self.plugin.logLevel > 2: indigo.server.log('TempSensor: Output Change Handler. Index:%s changed to:%s' % (str(e.index), str(e.temperature)), type=self.typeDisplayName)
        if self.plugin.logLevel > 2: indigo.server.log('TempSensor thread run() finished temp change handler declaration', type=self.typeDisplayName)

        """END OF HANDLERS"""
        # Create an TempSensor object
        if self.plugin.logLevel > 1:
            indigo.server.log(u'Start attach for device: %s' % (self.phDevName), type=self.typeDisplayName, isError=False)

        if self.plugin.phlibLogging:
            logMessage = 'Started thread for Phidgets tempsensor device "' + indigo.devices[int(self.phDevId)].name + '"'

            try:
                Phidget.log(1, 'tempsensor thread', logMessage)
            except:
                self.plugin.errorLog("Unexpected error:%s" % sys.exc_info()[0])

            if self.plugin.logLevel > 0:
                indigo.server.log(u'Low level phidgets libs logging started for device %s at level %s to file %s' %
                                 (indigo.devices[int(self.phDevId)].name, self.plugin.phlibLogLevel, self.plugin.phlibLogFile), type="Phidgets", isError=False)

        try:
            self.plugin.phidgetConnDict[self.phDevId] = TemperatureSensor()
        except RuntimeError, e:
            self.plugin.errorLog("TempSensor Exception (attach Handlers) %i: %s" % (e.code, e.details))
            self.plugin.errorLog("Exiting....")
            exit(1)
        if self.plugin.logLevel > 2: indigo.server.log('TempSensor thread run() Created the TempSensor object', type=self.typeDisplayName)

        try:
            self.plugin.phidgetConnDict[self.phDevId].setOnAttachHandler(TemperatureSensorAttached)
            self.plugin.phidgetConnDict[self.phDevId].setOnDetachHandler(TemperatureSensorDetached)
            self.plugin.phidgetConnDict[self.phDevId].setOnErrorhandler(TemperatureSensorError)
            self.plugin.phidgetConnDict[self.phDevId].setOnTemperatureChangeHandler(TemperatureSensorTemperatureChanged)
        except PhidgetException, e:
            self.plugin.errorLog("TempSensor Exception (attach Handlers) %i: %s" % (e.code, e.details))
            self.plugin.errorLog("Exiting....")
            exit(1)
        if self.plugin.logLevel > 2: indigo.server.log('TempSensor thread run() set all the handlers', type=self.typeDisplayName)

        try:
            self.plugin.phidgetConnDict[self.phDevId].openRemoteIP(self.phIpAddr, self.phIpPort,  serial=self.phSerial)
        except PhidgetException, e:
            self.plugin.errorLog("TempSensor Exception (Open Phidget) %i: %s" % (e.code, e.details))
            self.plugin.errorLog("Exiting....")
            exit(1)
        if self.plugin.logLevel > 2: indigo.server.log('TempSensor thread run() opened the Phidget device', type=self.typeDisplayName)

        # try:
        #     self.plugin.phidgetConnDict[self.phDevId].waitForAttach(10000)
        # except PhidgetException, e:
        #     self.phDevice.setErrorStateOnServer(u'offline')
        #     self.plugin.errorLog("TempSensor: Wait for Attach time exceeded for device %s" % (indigo.devices[int(self.phDevId)].name))
        #     self.plugin.errorLog("TempSensor: Will continue waiting for 15 minutes")
        #     try:
        #         self.plugin.phidgetConnDict[self.phDevId].waitForAttach(900000)
        #     except PhidgetException, e:
        #         self.plugin.errorLog("TempSensor: Maximum 15 min wait for Attach time exceeded from device %s" % (indigo.devices[int(self.phDevId)].name))
        #         self.plugin.errorLog("TempSensor: Please disable communications for this device")
        #         try:
        #              self.plugin.phidgetConnDict[self.phDevId].closePhidget()
        #              exit(1)
        #         except PhidgetException, e:
        #             self.plugin.errorLog("TempSensor Exception (Wait for Attach Close) from serial %s, %i: %s" % (source.getSerialNum(), e.code, e.details))
        #             self.plugin.errorLog("Exiting....")
        #             exit(1)

        startWaitAttachTime = time.time()

        while not self.isAttached:
            self.plugin.sleep(0.5)
            if time.time() - startWaitAttachTime > self.plugin.attachWaitTime:
                self.phDevice.setErrorStateOnServer(u'offline')
                self.plugin.errorLog("TempSensor: Could not attach to device %s. It has been set to offline" % (indigo.devices[int(self.phDevId)].name))
                self.plugin.threadAvailableDict[str(self.phDevId)] = {'threadUp': False}
                self.plugin.phidgetConnDict[self.phDevId].closePhidget()
                if self.plugin.logLevel > 0: indigo.server.log(u"Exiting Thread for ifKit device %s" % sensorDevice.name, type=self.typeDisplayName, isError=False)
                exit(1)

        if self.plugin.logLevel > 2: indigo.server.log('TempSensor thread run() phidget device attached', type=self.typeDisplayName)

        self.initializeTempSensor()

        if self.plugin.logLevel > 0: indigo.server.log('Setup for device \"%s\" complete, listening for events' % indigo.devices[int(self.phDevId)].name, type=self.typeDisplayName)

        while not self.shutdown:
            self.plugin.sleep(0.5)

        if self.plugin.logLevel > 2: indigo.server.log('closing temp sensor')

        try:
            self.plugin.phidgetConnDict[self.phDevId].closePhidget()
        except PhidgetException, e:
            self.plugin.errorLog("TempSensor Exception (Close Phidget) %i: %s" % (e.code, e.details))
            self.plugin.errorLog("Exiting....")

        now = datetime.datetime.now()
        self.phDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
        self.phDevice.updateStateOnServer(key='onOffState', value='offline')

        if self.plugin.logLevel > 0: indigo.server.log(u"Exiting Thread for ifKit device %s" % phDevice.name)

        exit(0)
