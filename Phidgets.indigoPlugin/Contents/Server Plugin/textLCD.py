#! /usr/bin/env python2.5
# -*- coding: utf-8 -*-
####################
# Copyright (c) 2011, Perceptive Automation, LLC. All rights reserved.
# http://www.perceptiveautomation.com

"""Portions Copyright 2010 Phidgets Inc.
This work is licensed under the Creative Commons Attribution 2.5 Canada License.
To view a copy of this license, visit http://creativecommons.org/licenses/by/2.5/ca/
"""

import indigo
# import os
import sys
# import time
from ctypes import *
import datetime
import indigo
import threading
#Phidget specific imports
from Phidgets.Phidget import Phidget
from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException
from Phidgets.Events.Events import AttachEventArgs, DetachEventArgs, ErrorEventArgs, InputChangeEventArgs, OutputChangeEventArgs, SensorChangeEventArgs
from Phidgets.Devices.TextLCD import TextLCD, TextLCD_ScreenSize

kPrintable = "' 0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&\'()*+,-./:;<=>?@\\^_`{|}][~"

################################################################################
class textLCD(threading.Thread):
    ########################################
    def __init__(self, plugin, phDevId, phIpAddr, phIpPort, phSerial, triggerDict):
        self.plugin = plugin
        self.shutdown = False
        #if self.plugin.logLevel > 3:
        #   self.plugin.debugLog("CONNECTIONS DICT = %s" % self.plugin.connectionsDict)

        self.phDevId = phDevId
        self.phDevice = indigo.devices[self.phDevId]
        self.phDevName = self.phDevice.name
        self.phIpAddr = phIpAddr
        self.phIpPort = phIpPort
        self.phSerial = phSerial
        self.phRows = self.phDevice.pluginProps['phLcdScreenRows']
        self.phCols = self.phDevice.pluginProps['phLcdScreenCols']
        self.typeDisplayName = self.plugin.pluginDisplayName + " TextLCD"
        self.triggerDict = triggerDict
        self.startup = True
        self.isAttached  = False

        if self.plugin.logLevel > 1: indigo.server.log('Thread starting for: %s' % self.phDevName, type=self.typeDisplayName)

        threading.Thread.__init__(self)

        if self.plugin.logLevel > 1: indigo.server.log('Thread init finished for: %s' % self.phDevName, type=self.typeDisplayName)

    def __del__(self):
        pass

    ######################
    def initializeTextLcd(self):
        logMsg = "Setting textLCD Options"
        if self.plugin.logLevel > 1: indigo.server.log(logMsg, type=self.typeDisplayName)

        # Set the device options
        if self.phDevice.pluginProps['phLcdScreenIndex'] != 'na':
            try:
                self.plugin.phidgetConnDict[self.phDevId].setScreenIndex(int(self.phDevice.pluginProps['phLcdScreenIndex']))
            except:
                self.plugin.errorLog('%s: Init. Failed to set screen index' % self.typeDisplayName)
                pass

        if self.phDevice.pluginProps['phLcdScreenContrast'] != 'na':
            try:
                self.plugin.phidgetConnDict[self.phDevId].setContrast(int(self.phDevice.pluginProps['phLcdScreenContrast']))
            except:
                self.plugin.errorLog('%s: Init. Failed to set screen contrast' % self.typeDisplayName)
                pass

        if self.phDevice.pluginProps['phLcdScreenBacklight'] != 'na':
            try:
                self.plugin.phidgetConnDict[self.phDevId].setBacklight(self.phDevice.pluginProps['phLcdScreenBacklight'])
            except:
                self.plugin.errorLog('%s: Init. Failed to set screen backlight' % self.typeDisplayName)
                pass

        if self.phDevice.pluginProps['phLcdScreenCursorVisible'] != 'na':
            try:
                self.plugin.phidgetConnDict[self.phDevId].setCursor(self.phDevice.pluginProps['phLcdScreenCursorVisible'])
            except:
                self.plugin.errorLog('%s: Init. Failed to set screen cursor visibility' % self.typeDisplayName)
                pass

        if self.phDevice.pluginProps['phLcdScreenCursorBlink'] != 'na':
            try:
                self.plugin.phidgetConnDict[self.phDevId].setCursorBlink(self.phDevice.pluginProps['phLcdScreenCursorBlink'])
            except:
                self.plugin.errorLog('%s: Init. Failed to set screen cursor blink' % self.typeDisplayName)
                pass

        if self.phDevice.pluginProps['phLcdAdapter'] == '1204':
            try:
                if self.phDevice.pluginProps['phLcdScreen'] == '2x20':
                    self.plugin.phidgetConnDict[self.phDevId].setScreenSize(7)
                elif self.phDevice.pluginProps['phLcdScreen'] == '2x40':
                    self.plugin.phidgetConnDict[self.phDevId].setScreenSize(11)
                elif self.phDevice.pluginProps['phLcdScreen'] == '4x20':
                    self.plugin.phidgetConnDict[self.phDevId].setScreenSize(8)
                elif self.phDevice.pluginProps['phLcdScreen'] == '4x40':
                    self.plugin.phidgetConnDict[self.phDevId].setScreenSize(12)
                elif self.phDevice.pluginProps['phLcdScreen'] == '1x16':
                    self.plugin.phidgetConnDict[self.phDevId].setScreenSize(4)
                elif self.phDevice.pluginProps['phLcdScreen'] == '1x40':
                    self.plugin.phidgetConnDict[self.phDevId].setScreenSize(10)
                elif self.phDevice.pluginProps['phLcdScreen'] == '1x8':
                    self.plugin.phidgetConnDict[self.phDevId].setScreenSize(2)
                elif self.phDevice.pluginProps['phLcdScreen'] == '2x16':
                    self.plugin.phidgetConnDict[self.phDevId].setScreenSize(5)
                elif self.phDevice.pluginProps['phLcdScreen'] == '2x24':
                    self.plugin.phidgetConnDict[self.phDevId].setScreenSize(9)
                elif self.phDevice.pluginProps['phLcdScreen'] == '2x8':
                    self.plugin.phidgetConnDict[self.phDevId].setScreenSize(3)
                elif self.phDevice.pluginProps['phLcdScreen'] == '4x16':
                    self.plugin.phidgetConnDict[self.phDevId].setScreenSize(6)
            except:
                self.plugin.errorLog('%s: Init. Failed to set screen size'  % self.typeDisplayName)

            if self.phDevice.pluginProps['phLcdScreenBrightness'] != 'na':
                try:
                    self.plugin.phidgetConnDict[self.phDevId].setBrightness(int(self.phDevice.pluginProps['phLcdScreenBrightness']))
                except Exception, e:
                    self.plugin.errorLog('%s: Init. Failed to set screen brightness' % (self.typeDisplayName))
                    pass

        if self.phDevice.pluginProps['useCustChars']:
            try:
                suffix = 0
                while suffix < 8:
                    character = self.phDevice.pluginProps['lcdCustChar_' + str(suffix)].replace(' ','')
                    self.plugin.debugLog('Character suffix %s = "%s"' % (suffix, character))
                    if len(character) > 1:
                        # Make sure we have somethng to work with, then split it into two numbers
                        (upper, lower) = character.split(',')
                        self.plugin.debugLog('Upper  "%s" Lower "%s" ' % (upper, lower))
                        self.plugin.phidgetConnDict[self.phDevId].setCustomCharacter(int(suffix), int(upper), int(lower))

                        # custChar = self.plugin.phidgetConnDict[self.phDevId].getCustomCharacter(int(suffix))
      
                        # indigo.server.log("Got cust char %s" % custChar.encode("hex"), type=self.typeDisplayName)
                    suffix += 1
            except Exception, e:
                self.plugin.errorLog('%s: Cust char error:%s' % (self.typeDisplayName, e))


                #  {14670, 0} -- degree symbol
                #  {606796, 12} -- C for celsius
                #  {598162, 0} -- small percent
                #  {680600, 171168} -- R/H     
                #     textLCD.setCustomCharacter(0, 949247, 536)
                #     textLCD.setCustomCharacter(1, 1015791, 17180)
                #     textLCD.setCustomCharacter(2, 1048039, 549790)
                #     textLCD.setCustomCharacter(3, 1031395, 816095)
                #     textLCD.setCustomCharacter(4, 498785, 949247)
                #     textLCD.setCustomCharacter(5, 232480, 1015791)
                #     textLCD.setCustomCharacter(6, 99328, 1048039)
                #     textLCD.setCustomCharacter(7, 99328, 1048039)
                #     print("Display the custom chars....")
                #     textLCD.setDisplayString(0, "Custom..")
                #     customString = textLCD.getCustomCharacter(0)
                #     customString += textLCD.getCustomCharacter(1)
                #     customString += textLCD.getCustomCharacter(2)
                #     customString += textLCD.getCustomCharacter(3)
                #     customString += textLCD.getCustomCharacter(4)
                #     customString += textLCD.getCustomCharacter(5)
                #     customString += textLCD.getCustomCharacter(6)
                #     customString += textLCD.getCustomCharacter(7)
                #     textLCD.setDisplayString(1, customString)


    ######################
    def getCustomChar(self, custCharNum):
        if self.plugin.logLevel > 1:
            indigo.server.log("Entered getCustomChar: character number:%s" % (custCharNum), type=self.typeDisplayName)

        custChar = self.plugin.phidgetConnDict[self.phDevId].getCustomCharacter(int(custCharNum))

        if self.plugin.logLevel > 2:
            indigo.server.log("getCustomChar: returned character ref:%s" % (custChar.encode("hex")), type=self.typeDisplayName)
        return  custChar

    ######################
    def writeDigitalOutput(self, index, state):
        state = str(state)[0:int(self.phCols)]

        if self.plugin.logLevel > 1:
            indigo.server.log("Entered writeDigitalOutput: Set index:%s to %s" % (index, state), type=self.typeDisplayName)

        try:
            self.plugin.phidgetConnDict[self.phDevId].setDisplayString(index, state)
        except PhidgetException, e:
            if int(e.code) == 5:
                retryTime = 5
                self.retryFlag = True
                if self.plugin.logLevel > 1:
                    indigo.server.log("textLCD: not yet available for write. Will retry in %s seconds." % (retryTime), type=self.typeDisplayName, isError=True)
                if self.retryFlag:
                    self.retryFlag = False
                    self.plugin.sleep(retryTime)
                    self.writeDigitalOutput(index, state)
            else:
                indigo.server.log("writeDigitalOutput (Phidgets Error) s%i: %s" % (e.code, e.details), type=self.typeDisplayName, isError=True)
        except:
            indigo.server.log('writeDigitalOutput (general error): %s' % str(sys.exc_info()), type=self.typeDisplayName, isError=True)

        now = datetime.datetime.now()
        self.phDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
        state = ''.join(char for char in state if char in kPrintable)  # get rid of any non-printable chars
        self.phDevice.updateStateOnServer(key='textLine_' + str(index), value=repr(state))

        if self.plugin.logLevel > 2: indigo.server.log("textLCD: write digital out Set index:%s to %s" % (index, state))

 ######################
    def controlDisplaySettings(self, setting, value):

        if self.isAttached:
            if self.plugin.logLevel > 1:
                indigo.server.log("Entered controlDisplaySettings: Setting:%s, value:%s" % (setting, value), type=self.typeDisplayName)

            if setting == 'phLcdScreenContrast':
                try:
                    self.plugin.phidgetConnDict[self.phDevId].setContrast(int(value))
                except:
                    self.plugin.errorLog('%s: Failed to set screen contrast' % self.typeDisplayName)
                    pass

            elif setting == 'phLcdScreenBacklight':
                try:
                    if value == 'on':
                        self.plugin.phidgetConnDict[self.phDevId].setBacklight(True)
                    else:
                        self.plugin.phidgetConnDict[self.phDevId].setBacklight(False)
                except:
                    self.plugin.errorLog('%s: Failed to set screen backlight' % self.typeDisplayName)
                    pass

            if self.phDevice.pluginProps['phLcdAdapter'] == '1204':
                if setting == 'phLcdScreenBrightness':
                    try:
                        self.plugin.phidgetConnDict[self.phDevId].setBrightness(int(value))
                    except Exception, e:
                        self.plugin.errorLog('%s: Failed to set screen brightness' % (self.typeDisplayName))
                        pass

       # if self.plugin.logLevel > 2: indigo.server.log("textLCD: controlDisplaySettings Set index:%s to %s" % (index, state))

    ######################
    def stop(self):
        if self.plugin.logLevel > 1: indigo.server.log('Thread init killed for: %s' % self.phDevName, type=self.typeDisplayName)
        self.shutdown = True

    ######################
    def run(self):
        if self.plugin.logLevel > 1: indigo.server.log('Thread run() called', type=self.typeDisplayName)
        # DEFINE HANDLERS

        def textLCDAttached(e):
            if self.plugin.logLevel > 1:
                indigo.server.log(u'Entered textLCD Attached for device: %s' % (self.phDevName), type=self.typeDisplayName, isError=False)
            if self.plugin.logLevel > 0 and not self.startup:
                indigo.server.log(u'TextLCD %s is now attached' % (self.phDevName), type=self.typeDisplayName, isError=False)

            if not self.startup: self.initializeTextLcd()
            self.isAttached  = True
            
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

        def textLCDDetached(e):
            if self.plugin.logLevel > 1:
                indigo.server.log(u'Entered textLCD Detached for device: %s' % (self.phDevName), type=self.typeDisplayName, isError=False)
            if self.plugin.logLevel > 0:
                indigo.server.log(u'TextLCD %s has been detached' % (self.phDevName), type=self.typeDisplayName, isError=True)
            self.phDevice.setErrorStateOnServer(u'offline')

            self.isAttached  = False

            for trigger in self.triggerDict:
                if self.plugin.logLevel > 2:
                    indigo.server.log(u'DEBUG: %s::%s::%s' % (trigger, self.triggerDict[trigger]['devid'],self.triggerDict[trigger]['event']), type=self.typeDisplayName, isError=False)
                if self.triggerDict[trigger]['devid'] == int(self.phDevId) and self.triggerDict[trigger]['event'] == 'detach':
                    self.plugin.triggerEvent(trigger, self.phDevId)

        def textLCDError(e):
            if self.plugin.logLevel > 1:
                indigo.server.log(u'Entered textLCD Error for device: %s' % (self.phDevName), type=self.typeDisplayName, isError=False)
            try:
                source = e.device
                self.plugin.errorLog("textLCD %i: Phidget Error %i: %s" % (source.getSerialNum(), e.eCode, e.description))
            except PhidgetException, e:
                self.plugin.errorLog("textLCD Exception (textLCD Error) %i: %s" % (e.code, e.details))
                self.plugin.sleep(5)

        def setDisplayString(self, index, string):
            if self.plugin.logLevel > 1:
                indigo.server.log(u'Entered setDisplayString for device: %s' % (self.phDevName), type=self.typeDisplayName, isError=False)

            self.plugin.phidgetConnDict[self.phDevId].setDisplayString(index, state)
            if self.plugin.logLevel > 2: self.plugin.debugLog("textLCD: Set index:%s to %s" % (index, state))

        if self.plugin.logLevel > 2: indigo.server.log('textLCD thread run() finished handler declarations', type=self.typeDisplayName)

        """
        END OF HANDLERS
        self.plugin.errorLog("textLCD: Create an textLCD object")
        Create an textLCD object
        """

        if self.plugin.logLevel > 1:
            indigo.server.log(u'Start attach for device: %s' % (self.phDevName), type=self.typeDisplayName, isError=False)

        if self.plugin.phlibLogging:
            logMessage = 'Started thread for Phidgets TextLCD device "' + indigo.devices[int(self.phDevId)].name + '"'

            try:
                Phidget.log(1, 'textLCD thread', logMessage)
            except:
                self.plugin.errorLog("textLCD Unexpected error:%s" % sys.exc_info()[0])

            if self.plugin.logLevel > 1:
                indigo.server.log(u'Low level phidgets libs logging started for device %s at level %s to file %s' %\
                (indigo.devices[int(self.phDevId)].name, self.plugin.phlibLogLevel, self.plugin.phlibLogFile), type=self.typeDisplayName, isError=False)
        try:
            self.plugin.phidgetConnDict[self.phDevId] = TextLCD()
        except RuntimeError, e:
            self.plugin.errorLog("Runtime Exception: %s" % e.details)
            self.plugin.errorLog("Exiting....")
            exit(1)

        if self.plugin.logLevel > 2: indigo.server.log('textLCD thread run() Created the textLCD object', type=self.typeDisplayName)

        #Main Program Code
        try:
            self.plugin.phidgetConnDict[self.phDevId].setOnAttachHandler(textLCDAttached)
            self.plugin.phidgetConnDict[self.phDevId].setOnDetachHandler(textLCDDetached)
            self.plugin.phidgetConnDict[self.phDevId].setOnErrorhandler(textLCDError)
        except PhidgetException, e:
            self.plugin.errorLog("textLCD Exception (attach Handlers) %i: %s" % (e.code, e.details))
            self.plugin.errorLog("Exiting....")
            exit(1)
        except:
            indigo.server.log('main program run (general error): %s' % str(sys.exc_info()), type=self.typeDisplayName, isError=True)

        if self.plugin.logLevel > 2: indigo.server.log('textLCD thread run() set all the handlers', type=self.typeDisplayName)

        #self.plugin.errorLog("textLCD: Ready to open Phidget")
        try:
            self.plugin.phidgetConnDict[self.phDevId].openRemoteIP(self.phIpAddr, self.phIpPort, serial=self.phSerial)
        except PhidgetException, e:
            self.plugin.errorLog("textLCD Exception (Open Phidget) %i: %s" % (e.code, e.details))
            self.plugin.errorLog("Exiting....")
            exit(1)
        if self.plugin.logLevel > 2: indigo.server.log('textLCD thread run() opened the Phidget device', type=self.typeDisplayName)
        self.plugin.debugLog("Waiting for attach....")

        # try:
        #     self.plugin.phidgetConnDict[self.phDevId].waitForAttach(20000)
        # except PhidgetException, e:
        #     self.phDevice.setErrorStateOnServer(u'offline')
        #     self.plugin.errorLog("TextLCD Exception (Wait for Attach) from serial %s, %i: %s" % (self.phSerial, e.code, e.details))
        #     try:
        #         iself.plugin.phidgetConnDict[self.phDevId].closePhidget()
        #         exit(1)
        #     except PhidgetException, e:
        #         self.plugin.errorLog("TextLCD Exception (Wait for Attach Close) from serial %s, %i: %s" % (source.getSerialNum(), e.code, e.details))
        #         self.plugin.errorLog("Exiting....")
        #         exit(1)

        startWaitAttachTime = time.time()

        while not self.isAttached:
            self.plugin.sleep(0.5)
            if time.time() - startWaitAttachTime > self.plugin.attachWaitTime:
                self.phDevice.setErrorStateOnServer(u'offline')
                self.plugin.errorLog("TextLCD: Could not attach to device %s. It has been set to offline" % (indigo.devices[int(self.phDevId)].name))
                self.plugin.threadAvailableDict[str(self.phDevId)] = {'threadUp': False}
                self.plugin.phidgetConnDict[self.phDevId].closePhidget()
                if self.plugin.logLevel > 0: indigo.server.log(u"Exiting Thread for ifKit device %s" % sensorDevice.name, type=self.typeDisplayName, isError=False)
                exit(1)
    
        if self.plugin.logLevel > 2: indigo.server.log('textLCD thread run() phidget device attached', type=self.typeDisplayName)

        self.initializeTextLcd()

        # now = datetime.datetime.now()
        # self.phDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
        # self.phDevice.updateStateOnServer(key='onOffState', value='online')

        self.plugin.debugLog("The result:%s" % self.plugin.phidgetConnDict[self.phDevId].getDeviceName())
        self.plugin.debugLog(u"Connection was successful")

        if self.plugin.logLevel > 0:
            indigo.server.log('Setup for device \"%s\"" complete, Display Available' % indigo.devices[int(self.phDevId)].name, type=self.typeDisplayName)

        #####
        # Finally, everything is setup and we can start
        #####
        while not self.shutdown:
            self.plugin.sleep(0.5)

        if self.plugin.logLevel > 1: indigo.server.log('textLCD thread exiting')

        try:
            self.plugin.phidgetConnDict[self.phDevId].closePhidget()
        except PhidgetException, e:
            self.plugin.errorLog("textLCD Exception (Close Phidget) %i: %s" % (e.code, e.details))
            self.plugin.errorLog("Exiting....")

        now = datetime.datetime.now()
        self.phDevice.updateStateOnServer(key="lastUpdate", value=now.strftime("%Y-%m-%d %H:%M:%S"))
        self.phDevice.updateStateOnServer(key='onOffState', value='offline')
        self.plugin.debugLog(u"Exiting Run Concurrent Thread")

        exit(0)
