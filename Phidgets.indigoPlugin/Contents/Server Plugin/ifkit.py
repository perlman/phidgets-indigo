#! /usr/bin/env python2.5
# -*- coding: utf-8 -*-
####################
# Copyright (c) 2011, Perceptive Automation, LLC. All rights reserved.
# http://www.perceptiveautomation.com

"""Portions Copyright 2010 Phidgets Inc.
This work is licensed under the Creative Commons Attribution 2.5 Canada License.
To view a copy of this license, visit http://creativecommons.org/licenses/by/2.5/ca/
"""

""" Change log 
8/1 ar - added class variable self.waitForAttachLimit to hold the max time waiting to attach a device. value in milli-seconds
         initially set to 90000 or 90 seconds.abs
8/1 ar - change logic to look as self.waitForAttachLimit to deterimine wait time for attachment.

8/1 ar - added logging messages to trace when a phidget device is requested to be closed and is successfully closed
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
from Phidgets.Devices.InterfaceKit import InterfaceKit


################################################################################
class ifkit(threading.Thread):
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
        self.typeDisplayName = self.plugin.pluginDisplayName + " ifKit"
        self.isAttached  = False
        self.startup = True
        self.errorCount = 0
        self.triggerDict = triggerDict
        # self.plugin.logLevel = 4

        ##### ar 8/1 add constant/variable for timeout wait time ###
        self.waitForAttachLimit = 90000
        #####

        if self.plugin.logLevel > 1: indigo.server.log('Thread starting for: %s' % self.phDevName, type=self.typeDisplayName)
        threading.Thread.__init__(self)
        if self.plugin.logLevel > 1: indigo.server.log('Thread init finished for: %s' % self.phDevName, type=self.typeDisplayName)

    def __del__(self):
        pass

    ######################
    def initializeInterfaceKit(self):
        logMsg = "Setting interfaceKit Options"
        # self.plugin.logLevel = 4
        if self.plugin.logLevel > 1: indigo.server.log(logMsg, type=self.typeDisplayName)

        # Set the device options
        sensorDevice = indigo.devices[self.phDevId]
        
        if self.plugin.logLevel > 2: indigo.server.log(u'Starting data rate and threshold setting for: %s' % (sensorDevice.name), type=self.typeDisplayName, isError=False)

        aSensorNum = int(sensorDevice.pluginProps['ifKitSensors'])
  
        if aSensorNum > 0 and 'ratiometric' in sensorDevice.pluginProps:  # so we don't blow up on older devices.
            if self.plugin.logLevel > 2: indigo.server.log(u'Found %s sensor ports for: %s' % (sensorDevice.pluginProps['ifKitSensors'], sensorDevice.name), type=self.typeDisplayName, isError=False)
            for sensor in xrange(0, aSensorNum):

                if sensor == 0:
                    aRatiometric = sensorDevice.pluginProps['ratiometric']
                    self.plugin.phidgetConnDict[self.phDevId].setRatiometric(aRatiometric)
                    if self.plugin.logLevel > 2:
                        indigo.server.log(u'Found, Ratiometric: %s, for: %s' % (str(aRatiometric), sensorDevice.name), type=self.typeDisplayName)

                aTrigger = int(sensorDevice.pluginProps['ifKitSensorTrigger_' + str(sensor)])
                aRate = int(sensorDevice.pluginProps['ifKitSensorRate_' + str(sensor)])
                if self.plugin.logLevel > 2: indigo.server.log(u'Found, Trigger: %s, Rate: %s, for: %s' % (aTrigger, aRate, sensorDevice.name), type=self.typeDisplayName, isError=False)

                self.plugin.phidgetConnDict[self.phDevId].setDataRate(sensor, aRate)
                self.plugin.phidgetConnDict[self.phDevId].setSensorChangeTrigger(sensor, aTrigger)

        if self.plugin.logLevel > 2:
            indigo.server.log('Setup for device \"%s\" complete, listening for events' % sensorDevice.name, type=self.typeDisplayName)

    ######################
    def stop(self):
        if self.plugin.logLevel > 1: indigo.server.log('Thread init killed for: %s' % self.phDevName, type=self.typeDisplayName)
        self.shutdown = True

    ######################
    # Callback functions for reading and writing (setting output states) to the ifkit
    ######################
    def writeDigitalOutput(self, index, state, pulseLength):
        if self.plugin.logLevel > 1:
            indigo.server.log("Entered writeDigitalOutput: device: %s, Set index:%s to %s, pulseLength: %s" % (self.phDevName, index, state, pulseLength), type=self.typeDisplayName)

        if self.isAttached:
            self.errorCount = 0
            pulseLength = ((float(pulseLength) % 1000) / 1000)  # Make sure we do not pulse for more than 1 second
            try:
                if state == 'pulseOnOff':
                    self.plugin.phidgetConnDict[self.phDevId].setOutputState(index, True)
                    time.sleep(pulseLength)
                    self.plugin.phidgetConnDict[self.phDevId].setOutputState(index, False)
                    if self.plugin.logLevel > 0: self.plugin.debugLog("InterfaceKit: Set index:%s to %s for %sms" % (index, state, pulseLength))
                elif state == 'pulseOffOn':
                    self.plugin.phidgetConnDict[self.phDevId].setOutputState(index, False)
                    time.sleep(pulseLength)
                    self.plugin.phidgetConnDict[self.phDevId].setOutputState(index, True)
                    if self.plugin.logLevel > 0: self.plugin.debugLog("InterfaceKit: Set index:%s to %s for %sms" % (index, state, pulseLength))
                else:
                    self.plugin.phidgetConnDict[self.phDevId].setOutputState(index, state)
                    if self.plugin.logLevel > 1: self.plugin.debugLog("InterfaceKit: Set index:%s to %s" % (index, state))
            except PhidgetException, e:
                self.plugin.errorLog("IfKit writeException (IkKIt Error)%i: %s" % (e.code, e.details))
            except:
                raise
        else:
            if self.errorCount == 0:
                indigo.server.log("writeDigitalOutput: device: %s is not attached. Cannot set index:%s" % (self.phDevName, index), type=self.typeDisplayName, isError=True)
            elif self.errorCount > 0 and self.plugin.logLevel >1:
                indigo.server.log("writeDigitalOutput: device: %s is not attached. Cannot set index:%s" % (self.phDevName, index), type=self.typeDisplayName, isError=True)
            self.errorCount += 1

    def readSensorInput(self, index):
        if self.plugin.logLevel > 1:
            indigo.server.log(u'Entered readSensorInput for device %s , index %s' % (self.phDevName, index), type=self.typeDisplayName, isError=False)

        if self.isAttached :
            self.errorCount = 0
            ifKitIndex = str(self.phSerial) + '-' + str(index)
            # What Indigo ifkit device are we are talking to
            # ifkitDev = indigo.devices[self.phDevId]
            try:
                inValue = self.plugin.phidgetConnDict[self.phDevId].getSensorValue(index)
            except PhidgetException, e:
                if e.code != 5:
                    self.plugin.errorLog("IfKit readSensorInput readException (IkKIt Error)%i: %s" % (e.code, e.details))
            except:
                raise

            # We know which interface kit sent the message.
            # So, next we find out what kind of sensor is attached to the input...     
            # we could also use... model = sensorDevice.pluginProps['phIfKitSensorModel']       
            # devId = int(self.plugin.phIfKitOutputDict[ifKitIndex])
            # sensorDevice = indigo.devices[devId]
            # model = sensorDevice.pluginProps['phIfKitSensorModel']

            devId = self.plugin.phIfKitSensorDict[ifKitIndex]['id']
            model = self.plugin.phIfKitSensorDict[ifKitIndex]['model']
            sensorDevice = indigo.devices[devId]

            tempUnits = sensorDevice.pluginProps['phTemp1']

            # Some, but not many, ifKit sensors have 2 states. So, we make sure we get them
            states = self.plugin.phidgetsDict[model]['states']
            self.plugin.debugLog('Read %s states for %s' % (states, model))
            for state in range(1, states + 1):
                # The formula and decimal precision are stored in the states dictionary
                self.plugin.debugLog('Processing state %s for model %s, device:%s' % (state, model, sensorDevice.name))
                stateKey = self.plugin.phidgetsDict[model][state]['Key']
                formula = self.plugin.phidgetsDict[model][state]['formula']
                if 'decimalPlaces' in sensorDevice.pluginProps:
                    decimalPlaces = int(sensorDevice.pluginProps['decimalPlaces'])
                else:
                    decimalPlaces = self.plugin.phidgetsDict[model][state]['decimalPlaces']

                # Some sensors have formula values (sensor specific data) stored in plugin props
                if model == '1134':
                    # get the necessary value(s) from plugin props
                    # run the formula
                    req = int(sensorDevice.pluginProps['cVal1'])
                    value = formula(inValue, req)
                elif model == '1142':
                    m = float(sensorDevice.pluginProps['cVal1'])
                    b = float(sensorDevice.pluginProps['cVal2'])
                    value = formula(inValue, m, b)
                elif model == '1143':
                    m = float(sensorDevice.pluginProps['cVal1'])
                    b = float(sensorDevice.pluginProps['cVal2'])
                    value = formula(inValue, m, b)
                elif model == '0999c':
                    if len(sensorDevice.pluginProps['cVal1']) > 0:
                        formula = lambda x: eval(sensorDevice.pluginProps['cVal1'])
                    else:
                        formula = lambda x: x
                    value = formula(float(inValue))
                else:
                    if self.plugin.logLevel >1:
                        indigo.server.log(u'readSensorInput for device %s , value %s' % (self.phDevName, inValue), type=self.typeDisplayName, isError=False)

                    value = formula(inValue)
                    if self.plugin.logLevel >1:
                        indigo.server.log(u'readSensorInput for device %s , value %s' % (self.phDevName, value), type=self.typeDisplayName, isError=False)

                # Convert Celsius to Fahrenheit if necessary
                if tempUnits == 'fh':
                    value = ((value * 9) / 5) + 32
                # value = ('%.2f' % value)
                now = datetime.datetime.now()

                #indigo.server.log(u"Updating states for:%s, , devid %s, port %s" % (deviceName, ifkitDev.id, port), type=self.typeDisplayName)
                #indigo.server.log(u"  Sensor info:%s, , state %s, value %s, accuracy %s" % (phDevice.name, stateKey, value, int(decimalPlaces)), type=self.typeDisplayName)

                # set the ifkit last update time
                self.phDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
                # and now update the sensor device
                sensorDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
                sensorDevice.updateStateOnServer(key=stateKey, value=float(value), decimalPlaces=int(decimalPlaces))
                # and, set the default state for visibility in the DEVICES window
                sensorDevice.updateStateOnServer(key='state', value=float(value), decimalPlaces=int(decimalPlaces))
                self.plugin.debugLog('Processed state %s for model %s' % (state, model))
        else:
            if self.errorCount == 0:
                indigo.server.log("readSensorInput: device: %s is not attached. Cannot set index:%s" % (self.phDevName, index), type=self.typeDisplayName, isError=True)
            elif self.errorCount > 0 and self.plugin.logLevel >1:
                indigo.server.log("readSensorInput: device: %s is not attached. Cannot set index:%s" % (self.phDevName, index), type=self.typeDisplayName, isError=True)
            self.errorCount += 1

        if self.plugin.logLevel > 1: indigo.server.log('finished sensor update for index %s' % (index), type=self.typeDisplayName)

    def readDigitalInput(self, index):
        if self.plugin.logLevel > 1:
            indigo.server.log(u'Entered readDigitalInput for device %s , index %s' % (self.phDevName, index), type=self.typeDisplayName, isError=False)

        if self.isAttached :
            self.errorCount = 0
            ifKitIndex = str(self.phSerial) + '-' + str(index)
            # What Indigo ifkit device are we are talking to
            # ifkitDev = indigo.devices[self.phDevId]

            try:
                inValue = self.plugin.phidgetConnDict[self.phDevId].getInputState(index)
            except PhidgetException, e:
                if e.code != 5:
                    self.plugin.errorLog("IfKit readDigitalInput readException (IkKIt Error)%i: %s" % (e.code, e.details))
            except:
                raise

            if ifKitIndex in self.plugin.phIfKitInputDict:
                #ifKitDevId = self.plugin.phIfKitDict[serial]
                devId = int(self.plugin.phIfKitInputDict[ifKitIndex])
                sensorDevice = indigo.devices[devId]
                now = datetime.datetime.now()
                # set the ifkit last update time
                self.phDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
                # and now update the digital input device
                sensorDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
                value = False  # "off"
                if inValue:
                    value = True  # "on"
                sensorDevice.updateStateOnServer(key='onOffState', value=value)
        else:
            if self.errorCount == 0:
                indigo.server.log("readDigitalInput: device: %s is not attached. Cannot set index:%s" % (self.phDevName, index), type=self.typeDisplayName, isError=True)
            elif self.errorCount > 0 and self.plugin.logLevel >1:
                indigo.server.log("readDigitalInput: device: %s is not attached. Cannot set index:%s" % (self.phDevName, index), type=self.typeDisplayName, isError=True)
            self.errorCount += 1

        if self.plugin.logLevel > 1: indigo.server.log('digital input read finished update for index %s' % (index), type=self.typeDisplayName)

    def readDigitalOutput(self, index):
        if self.plugin.logLevel > 1:
            indigo.server.log(u'Entered readDigitalOutput for device %s , index %s' % (self.phDevName, index), type=self.typeDisplayName, isError=False)

        if self.isAttached :
            self.errorCount = 0
            ifKitIndex = str(self.phSerial) + '-' + str(index)
            # What Indigo ifkit device are we are talking to
            # ifkitDev = indigo.devices[self.phDevId]

            try:
                inValue = self.plugin.phidgetConnDict[self.phDevId].getOutputState(index)
            except PhidgetException, e:
                if e.code != 5:
                    self.plugin.errorLog("readDigitalOutput readException (IkKIt Error)%i: %s" % (e.code, e.details))
            except:
                raise

            if ifKitIndex in self.plugin.phIfKitOutputDict:
                #ifKitDevId = self.plugin.phIfKitDict[serial]
                devId = int(self.plugin.phIfKitOutputDict[ifKitIndex])
                sensorDevice = indigo.devices[devId]
                now = datetime.datetime.now()
                # set the ifkit last update time
                self.phDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
                # and now update the digital output device
                sensorDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
                value = False
                if inValue:
                    value = True
                sensorDevice.updateStateOnServer(key='onOffState', value=value)
        else:
            if self.errorCount == 0:
                indigo.server.log("readDigitalOutput: device: %s is not attached. Cannot set index:%s" % (self.phDevName, index), type=self.typeDisplayName, isError=True)
            elif self.errorCount > 0 and self.plugin.logLevel >1:
                indigo.server.log("readDigitalOutput: device: %s is not attached. Cannot set index:%s" % (self.phDevName, index), type=self.typeDisplayName, isError=True)
            self.errorCount += 1

        if self.plugin.logLevel > 1: indigo.server.log('digital output read finished update for index %s' % (index), type=self.typeDisplayName)

    ######################
    def run(self):
        if self.plugin.logLevel > 2: indigo.server.log('Thread run() called', type=self.typeDisplayName)
        # DEFINE HANDLERS

        def inferfaceKitAttached(e):
            if self.plugin.logLevel > 1:
                indigo.server.log(u'Entered inferfaceKitAttached for device: %s' % (self.phDevName), type=self.typeDisplayName, isError=False)
            if self.plugin.logLevel > 0 and not self.startup:
                indigo.server.log(u'InferfaceKit "%s" is now attached' % (self.phDevName), type=self.typeDisplayName, isError=False)

            #self.isAttached = True
         
            if not self.startup: self.initializeInterfaceKit()

            self.phDevice.setErrorStateOnServer(None)
            now = datetime.datetime.now()
            self.phDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
            self.phDevice.updateStateOnServer(key='onOffState', value='online')
            
            for trigger in self.triggerDict:
                if self.plugin.logLevel > 1:
                    indigo.server.log(u'DEBUG: %s::%s::%s' % (trigger, self.triggerDict[trigger]['devid'],self.triggerDict[trigger]['event']), type=self.typeDisplayName, isError=False)
                if self.triggerDict[trigger]['devid'] == int(self.phDevId) and self.triggerDict[trigger]['event'] == 'attach':
                    self.plugin.triggerEvent(trigger, self.phDevId)

            try:
                if self.plugin.logLevel > 1: indigo.server.log("interfaceKitAttached %s: pseudoDevices %s" % (self.phDevId, self.plugin.ifKitPseudoDevDict[str(self.phDevId)]), type=self.typeDisplayName, isError=False)
                attachedDevices = self.plugin.ifKitPseudoDevDict[str(self.phDevId)]
                for pseudoDeviceId in attachedDevices.split(','):
                    pseudoDevice = indigo.devices[int(pseudoDeviceId)]
                    pseudoDevice.setErrorStateOnServer(None)
                    if self.plugin.logLevel > 0 and not self.startup:
                        indigo.server.log(u'InferfaceKit "%s" is attached and connected device "%s" is now available' % (self.phDevice.name, pseudoDevice.name), type=self.typeDisplayName, isError=False)
            except Exception, e:
                 indigo.server.log("inferfaceKitAttached error %s" % (e), type=self.typeDisplayName, isError=True)

            self.isAttached = True
            self.startup = False

        def interfaceKitDetached(e):
            if self.plugin.logLevel > 1:
                indigo.server.log(u'Entered interfaceKitDetached for device: %s' % (self.phDevName), type=self.typeDisplayName, isError=False)
            if self.plugin.logLevel > 0:
                indigo.server.log(u'InterfaceKit "%s" has been detached' % (self.phDevName), type=self.typeDisplayName, isError=True)
            self.phDevice.setErrorStateOnServer(u'offline')

            for trigger in self.triggerDict:
                if self.plugin.logLevel > 2:
                    indigo.server.log(u'DEBUG: %s::%s::%s' % (trigger, self.triggerDict[trigger]['devid'],self.triggerDict[trigger]['event']), type=self.typeDisplayName, isError=False)
                if self.triggerDict[trigger]['devid'] == int(self.phDevId) and self.triggerDict[trigger]['event'] == 'detach':
                    self.plugin.triggerEvent(trigger, self.phDevId)

            try:
                if self.plugin.logLevel > 1: indigo.server.log("interfaceKitDetached %s: pseudoDevices %s" % (self.phDevId, self.plugin.ifKitPseudoDevDict[str(self.phDevId)]), type=self.typeDisplayName, isError=True)
                attachedDevices = self.plugin.ifKitPseudoDevDict[str(self.phDevId)]
                for pseudoDeviceId in attachedDevices.split(','):
                    pseudoDevice = indigo.devices[int(pseudoDeviceId)]
                    pseudoDevice.setErrorStateOnServer(u'offline')
                    if self.plugin.logLevel > 0:
                        indigo.server.log(u'InferfaceKit "%s" has been detached and connected device "%s" is no longer available' % (self.phDevice.name, pseudoDevice.name), type=self.typeDisplayName, isError=True)
            except Exception, e:
                 indigo.server.log("interfaceKitDetached error %s" % (e), type=self.typeDisplayName, isError=True)

            self.isAttached  = False
            # self.plugin.deviceStopComm(self.phDevice)

        def interfaceKitError(e):
            if self.plugin.logLevel > 1:
                indigo.server.log(u'Entered interfaceKitError for device: %s' % (self.phDevName), type=self.typeDisplayName, isError=False)

            try:
                source = e.device
                self.plugin.debugLog("InterfaceKit %i: Phidget Error %i: %s" % (source.getSerialNum(), e.eCode, e.description))
            except PhidgetException, e:
                self.plugin.errorLog("IfKit Exception (IkKIt Error) from serial %s, %i: %s" % (source.getSerialNum(), e.code, e.details))
                time.sleep(2)

        if self.plugin.logLevel > 2: indigo.server.log('ifKit thread run() finished error handler declaration', type=self.typeDisplayName)

        def interfaceKitSensorChanged(e):
            source = e.device
            deviceName = source.getDeviceName()
            port = str(e.index)
            serial = str(source.getSerialNum())
            ifKitIndex = serial + '-' + port

            if self.plugin.logLevel > 1:
                indigo.server.log(u'Entered interfaceKitSensorChanged for device: %s, index: %s' % (self.phDevName, port), type=self.typeDisplayName, isError=False)

            if self.plugin.logLevel > 2:
                indigo.server.log(u"Sensor details for:%s, , devid %s, connector %s" % (deviceName, self.phDevice.id, port), type=self.typeDisplayName)
            else:
                self.plugin.debugLog("Entered sensor change handlers")

            model = 'unknown'
            formula = lambda x: x

            if ifKitIndex in self.plugin.phIfKitSensorDict:
                # We know which interface kit sent the message.
                # So, next we find out what kind of sensor is attached to the input...     
                # we could also use... model = sensorDevice.pluginProps['phIfKitSensorModel']       
                # devId = int(self.plugin.phIfKitOutputDict[ifKitIndex])
                # sensorDevice = indigo.devices[devId]
                # model = sensorDevice.pluginProps['phIfKitSensorModel']

                devId = self.plugin.phIfKitSensorDict[ifKitIndex]['id']
                model = self.plugin.phIfKitSensorDict[ifKitIndex]['model']
                sensorDevice = indigo.devices[devId]

                tempUnits = sensorDevice.pluginProps['phTemp1']

                # Some, but not many, ifKit sensors have 2 states. So, we make sure we get them
                states = self.plugin.phidgetsDict[model]['states']
                self.plugin.debugLog('Read %s states for %s' % (states, model))
                for state in range(1, states + 1):
                    # The formula and decimal precision are stored in the states dictionary
                    self.plugin.debugLog('Processing state %s for model %s, device:%s' % (state, model, sensorDevice.name))
                    stateKey = self.plugin.phidgetsDict[model][state]['Key']
                    formula = self.plugin.phidgetsDict[model][state]['formula']
                    if 'decimalPlaces' in sensorDevice.pluginProps:
                        decimalPlaces = int(sensorDevice.pluginProps['decimalPlaces'])
                    else:
                        decimalPlaces = self.plugin.phidgetsDict[model][state]['decimalPlaces']

                    # Some sensors have formula values (sensor specific data) stored in plugin props
                    if model =='1133':  # We can't seem to get ths code to accept math.log from the saved formula
                        formula = lambda x: 16.801 * math.log(x) + 9.872
                        value = formula(e.value)
                    elif model == '1134':
                        # get the necessary value(s) from plugin props
                        # run the formula
                        req = int(sensorDevice.pluginProps['cVal1'])
                        value = formula(e.value, req)
                    elif model == '1142':
                        m = float(sensorDevice.pluginProps['cVal1'])
                        b = float(sensorDevice.pluginProps['cVal2'])
                        value = formula(e.value, m, b)
                    elif model == '1143':
                        m = float(sensorDevice.pluginProps['cVal1'])
                        b = float(sensorDevice.pluginProps['cVal2'])
                        value = formula(e.value, m, b)
                    elif model == '0999c':
                        if len(sensorDevice.pluginProps['cVal1']) > 0:
                            formula = lambda x: eval(sensorDevice.pluginProps['cVal1'])
                        else:
                            formula = lambda x: x
                        value = formula(float(e.value))
                    else:
                        try:
                            value = formula(float(e.value))
                        except Exception, e:
                            indigo.server.log(u'readSensorInput for device %s , error in formula %s' % (self.phDevName, e), type=self.typeDisplayName, isError=True)

                    # Convert Celsius to Fahrenheit if necessary
                    if tempUnits == 'fh':
                        value = ((value * 9) / 5) + 32
                    #value = ('%.2f' % value)
                    now = datetime.datetime.now()

                    #indigo.server.log(u"Updating states for:%s, , devid %s, port %s" % (deviceName, ifkitDev.id, port), type=self.typeDisplayName)
                    #indigo.server.log(u"  Sensor info:%s, , state %s, value %s, accuracy %s" % (phDevice.name, stateKey, value, int(decimalPlaces)), type=self.typeDisplayName)

                    # set the ifkit last update time
                    self.phDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
                    # and now update the sensor device
                    sensorDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
                    sensorDevice.updateStateOnServer(key=stateKey, value=float(value), decimalPlaces=int(decimalPlaces))
                    # and, set the default state for visibility in the DEVICES window
                    sensorDevice.updateStateOnServer(key='state', value=float(value), decimalPlaces=int(decimalPlaces))
                    self.plugin.debugLog('Processed state %s for model %s' % (state, model))

        if self.plugin.logLevel > 2: indigo.server.log('ifKit thread run() finished sensor change handler declaration', type=self.typeDisplayName)

        def interfaceKitInputChanged(e):
            source = e.device
            #  deviceName = source.getDeviceName()
            port = str(e.index)
            serial = source.getSerialNum()
            ifKitIndex = str(serial) + '-' + port

            if self.plugin.logLevel > 1:
                indigo.server.log(u'Entered interfaceKitInputChanged for device: %s, index: %s' % (self.phDevName, port), type=self.typeDisplayName, isError=False)

            # What Indigo ifkit device are we are talking to
            # ifkitDev = indigo.devices[self.phDevId]
            if self.plugin.logLevel > 2:
                self.plugin.debugLog("InterfaceKit %i: Input %i, %i" % (source.getSerialNum(), e.index, e.state))

            if ifKitIndex in self.plugin.phIfKitInputDict:
                #ifKitDevId = self.plugin.phIfKitDict[serial]
                devId = int(self.plugin.phIfKitInputDict[ifKitIndex])
                sensorDevice = indigo.devices[devId]
                now = datetime.datetime.now()
                # set the ifkit last update time
                self.phDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
                # and now update the digital input device
                sensorDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
                value = False  # "off"
                if e.state:
                    value = True  # "on"
                sensorDevice.updateStateOnServer(key='onOffState', value=value)

        if self.plugin.logLevel > 2: indigo.server.log('ifKit thread run() finished input change handler declaration', type=self.typeDisplayName)

        def interfaceKitOutputChanged(e):
            source = e.device
            #  deviceName = source.getDeviceName()
            port = str(e.index)
            serial = source.getSerialNum()
            ifKitIndex = str(serial) + '-' + port

            if self.plugin.logLevel > 1:
                indigo.server.log(u'Entered interfaceKitOutputChanged for device: %s, index: %s' % (self.phDevName, port), type=self.typeDisplayName, isError=False)

            # What Indigo ifkit device are we are talking to
            # ifkitDev = indigo.devices[self.phDevId]

            if self.plugin.logLevel > 2:
                self.plugin.debugLog("InterfaceKit %i: Output %i, %i" % (source.getSerialNum(), e.index, e.state))
            else:
                self.plugin.debugLog("Entered output change handler")

            if ifKitIndex in self.plugin.phIfKitOutputDict:
                #ifKitDevId = self.plugin.phIfKitDict[serial]
                devId = int(self.plugin.phIfKitOutputDict[ifKitIndex])
                sensorDevice = indigo.devices[devId]
                now = datetime.datetime.now()
                # set the ifkit last update time
                self.phDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
                # and now update the digital output device
                sensorDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
                value = False
                if e.state:
                    value = True
                sensorDevice.updateStateOnServer(key='onOffState', value=value)

        if self.plugin.logLevel > 2: indigo.server.log('ifKit thread run() finished output change handler declaration', type=self.typeDisplayName)

        if self.plugin.logLevel > 2: indigo.server.log('ifKit thread run() finished handler declarations', type=self.typeDisplayName)

        # End of handlers
        #
        # Start of connection function
        if self.plugin.logLevel > 1:
            indigo.server.log(u'Start attach for device: %s' % (self.phDevName), type=self.typeDisplayName, isError=False)

        if self.plugin.phlibLogging:
            logMessage = 'Started thread for Phidgets ifKit device "' + indigo.devices[int(self.phDevId)].name + '"'

            try:
                Phidget.log(1, 'ifkit thread', logMessage)
            except NameError, e:
                self.plugin.errorLog("error message: %s" % (e))
            except:
                self.plugin.errorLog("Unexpected error:%s for device %s" % (sys.exc_info()[0], indigo.devices[int(self.phDevId)].name))

            if self.plugin.logLevel > 0:
                indigo.server.log(u'Low level phidgets libs logging started for device %s at level %s to file %s' %\
                (indigo.devices[int(self.phDevId)].name, self.plugin.phlibLogLevel, self.plugin.phlibLogFile), type="Phidgets", isError=False)

        try:
            if self.plugin.logLevel > 2: indigo.server.log("Creating interfacekit for serial: %s" % (self.phSerial), type=self.typeDisplayName)
            self.plugin.phidgetConnDict[self.phDevId] = InterfaceKit()
        except RuntimeError, e:
            self.plugin.errorLog("Runtime Exception: %s" % e.details)
            self.plugin.errorLog("Exiting....")
            exit(1)
        if self.plugin.logLevel > 2: indigo.server.log('IfKit thread run() Created the IfKit object', type=self.typeDisplayName)

        try:
            self.plugin.phidgetConnDict[self.phDevId].setOnAttachHandler(inferfaceKitAttached)
            self.plugin.phidgetConnDict[self.phDevId].setOnDetachHandler(interfaceKitDetached)
            self.plugin.phidgetConnDict[self.phDevId].setOnErrorhandler(interfaceKitError)
            self.plugin.phidgetConnDict[self.phDevId].setOnInputChangeHandler(interfaceKitInputChanged)
            self.plugin.phidgetConnDict[self.phDevId].setOnOutputChangeHandler(interfaceKitOutputChanged)
            self.plugin.phidgetConnDict[self.phDevId].setOnSensorChangeHandler(interfaceKitSensorChanged)
        except PhidgetException, e:
            indigo.server.log("IfKit Exception (Attach Handlers) from serial %s, %i: %s" % (self.phSerial, e.code, e.details), type=self.typeDisplayName, isError=True)
            self.plugin.errorLog("Exiting....")
            exit(1)
        if self.plugin.logLevel > 2: indigo.server.log('IfKit thread run() set all the handlers', type=self.typeDisplayName)

        if self.plugin.logLevel > 2: self.plugin.debugLog("Opening phidget object....")

        try:
            self.plugin.phidgetConnDict[self.phDevId].openRemoteIP(self.phIpAddr, self.phIpPort, serial=self.phSerial)
        except PhidgetException, e:
            indigo.server.log("IfKit Exception (Open IfKit) from serial %s, %i: %s" % (self.phSerial, e.code, e.details), type=self.typeDisplayName, isError=True)
            self.plugin.errorLog("Exiting....")
            exit(1)
        if self.plugin.logLevel > 2: indigo.server.log('IfKit thread run() opened the Phidget device %s' % (indigo.devices[int(self.phDevId)].name), type=self.typeDisplayName)

        # try:
        #     self.plugin.phidgetConnDict[self.phDevId].waitForAttach(10000)
        # except PhidgetException, e:
        #     self.phDevice.setErrorStateOnServer(u'offline')
        #     self.plugin.errorLog("interfaceKit: Wait for Attach time exceeded for device %s" % (indigo.devices[int(self.phDevId)].name))
        #     #### ar change from 15 min to 90 sec
        #     #self.plugin.errorLog("interfaceKit: Will continue waiting for 15 minutes")
        #     self.plugin.errorLog("interfaceKit: Will continue waiting for %i seconds" % (self.waitForAttachLimit//1000))
        #     ####

        #     try:
        #         ##### ar 8/1 change from 15 min to self.waitForAttachLimit/1000 seconds. Initially set to 90 seconds.
        #         #self.plugin.phidgetConnDict[self.phDevId].waitForAttach(900000)
        #         self.plugin.phidgetConnDict[self.phDevId].waitForAttach(self.waitForAttachLimit)
        #         #

        #     except PhidgetException, e:
        #         #### ar change from 15 min to self.waitForAttachLimit/1000 seconds. initially set to 90 seconds. 
        #         #self.plugin.errorLog("interfaceKit: Maximum 15 min wait for Attach time exceeded from device %s" % (indigo.devices[int(self.phDevId)].name))
        #         self.plugin.errorLog("interfaceKit: Maximum %i sec wait for Attach time exceeded from device %s" % (self.waitForAttachLimit/1000 , indigo.devices[int(self.phDevId)].name))
        #         #

        #         self.plugin.errorLog("interfaceKit: Please disable communications for this device")
        #         try:
        #              #### ar 8/1 added for tracing state in logs
        #              self.plugin.errorLog("interfaceKit: Pre closePhidget for this device %s"% (indigo.devices[int(self.phDevId)].name))
        #              #
        #              self.plugin.phidgetConnDict[self.phDevId].closePhidget()
        #              #### ar  8/1 added for tracing state in logs
        #              self.plugin.errorLog("interfaceKit: Post closePhidget for this device %s"% (indigo.devices[int(self.phDevId)].name))
        #              #
        #              exit(1)
        #         except PhidgetException, e:
        #             self.plugin.errorLog("interfaceKit Exception (Wait for Attach Close) from serial %s, %i: %s" % (source.getSerialNum(), e.code, e.details))
        #             self.plugin.errorLog("Exiting....")
        #             exit(1)

        startWaitAttachTime = time.time()

        while not self.isAttached:
            self.plugin.sleep(0.5)
            if time.time() - startWaitAttachTime > self.plugin.attachWaitTime:
                self.phDevice.setErrorStateOnServer(u'offline')
                self.plugin.errorLog("interfaceKit: Could not attach to device %s. It has been set to offline" % (indigo.devices[int(self.phDevId)].name))
                self.plugin.threadAvailableDict[str(self.phDevId)] = {'threadUp': False}
                self.plugin.phidgetConnDict[self.phDevId].closePhidget()
                if self.plugin.logLevel > 0: indigo.server.log(u"Exiting Thread for ifKit device %s" % sensorDevice.name, type=self.typeDisplayName, isError=False)
                exit(1)

        if self.plugin.logLevel > 2: indigo.server.log('IfKit thread run() phidget device attached', type=self.typeDisplayName)

        # Now that the ifKit is up, we need to set the change trigger and data rate settings
        self.initializeInterfaceKit()

        self.plugin.threadAvailableDict[str(self.phDevId)] = {'threadUp': True}

        if self.plugin.logLevel > 0:
            indigo.server.log('Setup for InterfaceKit "%s" complete, device Available' % indigo.devices[int(self.phDevId)].name, type=self.typeDisplayName)

        # Ok, we're running, let the world know
        self.plugin.threadAvailableDict[str(self.phDevId)] = {'threadUp': True}
        #self.phIfKitSensorDict[ifKitIndex] = {'model': model, 'id': id}

        while not self.shutdown:
            self.plugin.sleep(0.5)

        # and now let the world know we've stopped
        self.plugin.threadAvailableDict[str(self.phDevId)] = {'threadUp': False}

        if self.pluplugin.logLevel > 1: indigo.server.log('closing interfaceKit')

        self.plugin.phidgetConnDict[self.phDevId].closePhidget()

        now = datetime.datetime.now()
        sensorDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
        sensorDevice.updateStateOnServer(key='onOffState', value='offline')
        if self.plugin.logLevel > 0: indigo.server.log(u"Exiting Thread for ifKit device %s" % sensorDevice.name, type=self.typeDisplayName, isError=False)
