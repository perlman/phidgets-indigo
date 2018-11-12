#! /usr/bin/env python2.5
# -*- coding: utf-8 -*-
####################
# Copyright (c) 2013, Berkinet - Richard Perlman

""" Change log 
8/1 ar - notes...   
    The following behavior was observed and attempted to be addressed by these updates:
        Attempting to Comm enable a remote device that either does not exist or is unreachable  was locking other activities in Indigo console.
        other activities that were locked out include 
             1) attaching other devices, 
             2) reading the ifKit of other devices, 
             3) toggling the Comm Enable of other devices
             4) the configure widgets interface kit window being a modal window with it's own set of timers 
                appears to cause additional behavioral problems as exception timers were potentailly triggered in multiple areas causing odd behaviors in the UI.
        Richard Perlman noted that the appropriate fix was to ensure that each configuration of new devices happen in 
        separate threads and thus ensuring that no single thread is locking other activites from completion and subsequent behaviors.

        The short term fix employed in this release really reduces the max timeout for attaching or re-attaching devices.  
        It also enhances some of the logging and error messaging to provide enough information to identify locking triggers and release triggers.
        This allows such locking situations to resolve reasonably quickly.

8/1 ar - added log messages to capture locking on OpenRemoteIP calls 
8/1 ar - updated errorlog message to capture IP and Port of current devicefor tracking in an event code model
8/1 ar - added messaging for tracking WaitForAttach calls
8/1 ar - added try/exception clause around interfacekit.get... services as such calls made against an unattached device will cause exception
         currently calls to exit upon triggering of this exception. Perhaps should be reviewed for better flow

"""
from ctypes import *
import inspect
import sys
import re
import threading
import Queue
from berkinet import setLogLevel, versionCheck, logger
import indigo
# Phidget specific imports
from Phidgets.Phidget import Phidget
from Phidgets.PhidgetException import PhidgetException
from Phidgets.Devices.InterfaceKit import InterfaceKit
from Phidgets.Devices.TextLCD import TextLCD, TextLCD_ScreenSize
from ifkit import ifkit
from rfid import rfid
from tempsensor import tempsensor
from frequencycounter import frequencycounter
from circulartouch import circulartouch
from textLCD import textLCD


################################################################################
class Plugin(indigo.PluginBase):
    ########################################
    ########################################
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)

        (self.logLevel, self.debug) = setLogLevel(self, pluginDisplayName, pluginPrefs.get("showDebugInfo1", "1"))
        self.log = logger(self)
        self.logName = pluginDisplayName

        if 'pl0' in pluginPrefs:
            if pluginPrefs.get('pl0', 'false'):
                self.phlibLogging = True
                self.phlibLogLevel = self.pluginPrefs['pl1']
                self.phlibLogFile = self.pluginPrefs['pl2']
            else:
                self.phlibLogging = False
        else:
            self.phlibLogging = False
            # if self.logLevel > 0: indigo.server.log(u'Startup warning. Please re-configure the Phidgets plugin and then reload.', type=self.pluginDisplayName, isError=True)
            self.log.logError('Startup warning. Please re-configure the Phidgets plugin and then reload.', type=self.logName)

        if 'at0' in pluginPrefs:
            self.attachWaitTime = int(self.pluginPrefs['at0'])
        else:
            self.attachWaitTime = 10
            self.log.logError('Startup warning. Attact wait time not set. Using the default of 10 seconds. Re-configure the Phidgets plugin to change.', type=self.logName)

        if self.logLevel > 2: 
            indigo.server.log(u"Plugin attach wait time = %s." % self.attachWaitTime, type=self.pluginDisplayName)

        self.shutdown = False
        self.phIfKitSensorDict = {}
        self.phIfKitOutputDict = {}
        self.phIfKitInputDict = {}
        self.phidgetsDict = {}
        self.phidgetsDict = eval(open("../Resources/phidgets.dict").read())
        self.interfaceKit = ""
        self.ifKitSensorNum = 2
        self.ifKitDiNum = 2
        self.ifKitDoNum = 2
        self.phThreadDict = {}
        self.commQueue = {}
        self.threadAvailableDict = {}
        self.phidgetConnDict = {}  # holds instances of phidget connections() for the individual threads
        self.ifKitPseudoDevDict = {} #  cross ref for pseudo devices attached to an ifkit
        self.triggerList = []
        self.triggerDict = {}

    ########################################
    def __del__(self):
        indigo.PluginBase.__del__(self)

    ########################################
    ########################################
    def startup(self):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        # if self.logLevel > 0: indigo.server.log(u"Plugin startup.", type=self.pluginDisplayName)
        self.log.log(0, dbFlg, "Plugin Startup.", self.logName)

        versionCheck(self, self.pluginDisplayName, self.logLevel, self.pluginId, self.pluginVersion)

        # Time to set the low level logging options... If we have then turned on
        if self.phlibLogging:
            self.phidgetsLibLoggingControl(self.pluginPrefs['pl0'], int(self.pluginPrefs['pl1']), self.pluginPrefs['pl2'])

        self.log.log(3, dbFlg, "%s: pluginId:%s, pluginDisplayName:%s, pluginVersion:%s, pluginPrefs:%s" % \
            (funcName, self.pluginId, self.pluginDisplayName, self.pluginVersion, self.pluginPrefs), self.logName)
        # if self.logLevel > 3:
        #     indigo.server.log("pluginId:%s, pluginDisplayName:%s, pluginVersion:%s, pluginPrefs:%s" % \
        #     (self.pluginId, self.pluginDisplayName, self.pluginVersion, self.pluginPrefs), type=self.pluginDisplayName)

    ########################################
    def shutdown(self):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "%s called" % funcName, self.logName)
        # if self.logLevel > 2: indigo.server.log(u"shutdown called")

    ########################################
    # Start a thread for each Standalone, TextLCD and InterfaceKit device
    ########################################
    def runConcurrentThread(self):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "Entering %s" % funcName, self.logName)
        # if self.logLevel > 1: indigo.server.log(u"Entering runConcurrentThread", type=self.pluginDisplayName)

        while not self.shutdown:
            self.sleep(0.5)

        # Give the threads a moment to quit
        self.sleep(2)

    ########################################
    def stopConcurrentThread(self):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "Entering %s" % funcName, self.logName)
        # if self.logLevel > 1: indigo.server.log(u"Entering stopConcurrentThread", type=self.pluginDisplayName)

        self.shutdown = True
        # if self.logLevel > 2: indigo.server.log(u"Exiting stopConcurrentThread")
        self.log.log(2, dbFlg, "Exiting %s" % funcName, self.logName)

    ########################################
    # start trhreads and build xref from ifkit I/O and sensors
    ########################################
    def deviceStartComm(self, dev):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "Entering %s for device: %s (%d - %s)" % (funcName, dev.name, dev.id, dev.deviceTypeId), self.logName)
        self.log.log(3, dbFlg, "%s: Read device:\n%s" % (funcName, dev), self.logName)

        #if self.logLevel > 1:      indigo.server.log(u"Entering deviceStartComm for device: %s (%d - %s)" % (dev.name, dev.id, dev.deviceTypeId))
        #if self.logLevel > 3: indigo.server.log("Read device:\n%s" % (dev))


        if int(dev.id) in self.phThreadDict:   #  Work around problem with deviceStartComm() being called every time a device is operated
            self.log.log(1, dbFlg, "%s: Quiting for device: %s: Thread already exists" % (funcName, dev.name), self.logName)
            # if self.logLevel > 1:   indigo.server.log(u"Quiting deviceStartComm for device: %s: Thread already exists" % (dev.name))
            return
        else:
            # Each device type requires a slightly different start routine
            if dev.deviceTypeId == 'ifKit':
                self.log.log(2, dbFlg, '%s: Found %s device %s' % (funcName, dev.deviceTypeId, dev.name), self.logName)
                # indigo.server.log('Found ifkit device:%s' % (dev.name))

                phIpAddr = str(dev.pluginProps['ifKitIpAddress'])
                phIpPort = int(dev.pluginProps['ifKitIpPort'])
                phSerial = int(dev.pluginProps['ifKitSerial'])
                phDevId = int(dev.id)

                try:
                    self.phThreadDict[phDevId] = ifkit(self, phDevId, phIpAddr, phIpPort, phSerial, self.triggerDict)
                    self.phThreadDict[phDevId].start()
                except Exception, e:
                    self.log.logError('%s: error %s starting thread for device %s.' % (funcName, str(e), dev.name), self.logName)
                    # indigo.server.log("ERROR: %s" % str(e), type=self.pluginDisplayName, isError=False)

                self.log.log(2, dbFlg, '%s: Created %s thread: device: %s, serial:%s' % (funcName, dev.deviceTypeId, phDevId, phSerial), self.logName)

                # indigo.server.log('Added %s: %s' % (dev.deviceTypeId, dev.name))
                # indigo.server.log('Created %s thread: serial:%s, phidget Is:%s' % (dev.deviceTypeId, phDevId, phSerial))
                self.sleep(0.25)

            elif dev.deviceTypeId == 'phStandalonePhidget':
                self.log.log(2, dbFlg, '%s: Found %s device %s' % (funcName, dev.deviceTypeId, dev.name), self.logName)
                # if self.logLevel > 1: indigo.server.log('Found standalone device:%s' % (dev.name))

                phIpAddr = str(dev.pluginProps['phStandaloneIpAddress'])
                phIpPort = int(dev.pluginProps['phStandaloneIpPort'])
                phSerial = int(dev.pluginProps['phStandaloneSerial'])
                phModel = str(dev.pluginProps['phStandalonePhidgetModel'])
                phDevId = int(dev.id)

                rfidList = ['1022', '1023']
                tempSensorList = ['1045', '1048', '1051']
                freqCounterList = ['1054']
                circularTouchList = ['1016']

                if phModel in rfidList:
                    try:
                        self.phThreadDict[phDevId] = rfid(self, phDevId, phIpAddr, phIpPort, phSerial, self.triggerDict)
                        self.phThreadDict[phDevId].start()
                    except Exception, e:
                        self.log.logError('%s: error %s starting thread for device %s.' % (funcName, str(e), dev.name), self.logName)
                        # indigo.server.log("ERROR: %s" % str(e), type=self.pluginDisplayName, isError=False)
                elif phModel in tempSensorList:
                    try:
                        self.phThreadDict[phDevId] = tempsensor(self, phDevId, phIpAddr, phIpPort, phSerial, self.triggerDict)
                        self.phThreadDict[phDevId].start()
                    except Exception, e:
                        self.log.logError('%s: error %s starting thread for device %s.' % (funcName, str(e), dev.name), self.logName)
                        # indigo.server.log("ERROR: %s" % str(e), type=self.pluginDisplayName, isError=False)
                elif phModel in freqCounterList:
                    try:
                        self.phThreadDict[phDevId] = frequencycounter(self, phDevId, phIpAddr, phIpPort, phSerial, self.triggerDict)
                        self.phThreadDict[phDevId].start()
                    except Exception, e:
                        self.log.logError('%s: error %s starting thread for device %s.' % (funcName, str(e), dev.name), self.logName)
                        # indigo.server.log("ERROR: %s" % str(e), type=self.pluginDisplayName, isError=False)
                elif phModel in circularTouchList:
                    try:
                        self.phThreadDict[phDevId] = circulartouch(self, phDevId, phIpAddr, phIpPort, phSerial, self.triggerDict)
                        self.phThreadDict[phDevId].start()
                    except Exception, e:
                        self.log.logError('%s: error %s starting thread for device %s.' % (funcName, str(e), dev.name), self.logName)
                        # indigo.server.log("ERROR: %s" % str(e), type=self.pluginDisplayName, isError=False)

                self.log.log(2, dbFlg, '%s: Created %s thread: device: %s, serial:%s' % (funcName, dev.deviceTypeId, phDevId, phSerial), self.logName)
                self.sleep(0.25)

                # if self.logLevel > 1: indigo.server.log('Added %s: %s' % (dev.deviceTypeId, dev.name))
                # if self.logLevel > 2: indigo.server.log('Created %s thread: serial:%s, phidget Is:%s' % (dev.deviceTypeId, phDevId, phSerial))

            elif dev.deviceTypeId == 'phLcdScreen':
                self.log.log(2, dbFlg, '%s: Found %s device %s' % (funcName, dev.deviceTypeId, dev.name), self.logName)
                # if self.logLevel > 1: indigo.server.log('Found standalone device:%s' % (dev.name))

                phIpAddr = str(dev.pluginProps['phLcdScreenIpAddress'])
                phIpPort = int(dev.pluginProps['phLcdScreenIpPort'])
                phSerial = int(dev.pluginProps['phLcdScreenSerial'])
                phModel = str(dev.pluginProps['phLcdScreenModel'])
                phDevId = int(dev.id)

                # lcdScreenList = ['1018', '1202', '1023', '1204']
                try:
                    self.phThreadDict[phDevId] = textLCD(self, phDevId, phIpAddr, phIpPort, phSerial, self.triggerDict)
                    self.phThreadDict[phDevId].start()
                except Exception, e:
                    self.log.logError('%s: error %s starting thread for device %s.' % (funcName, str(e), dev.name), self.logName)
                    # indigo.server.log("ERROR: %s" % str(e), type=self.pluginDisplayName, isError=False)

                self.log.log(2, dbFlg, '%s: Created %s thread: device: %s, serial:%s' % (funcName, dev.deviceTypeId, phDevId, phSerial), self.logName)
                self.sleep(0.25)
                # if self.logLevel > 1: indigo.server.log('Added %s: %s' % (dev.deviceTypeId, dev.name))
                # if self.logLevel > 2: indigo.server.log('Created %s thread: serial:%s, phidget Is:%s' % (dev.deviceTypeId, phDevId, phSerial))

            # ...then setup ifKit sensors, Digital Inputs & Digital Outputs.
            elif dev.deviceTypeId == 'phIfKitSensor':
                # What do we know about this device
                model = dev.pluginProps['phIfKitSensorModel']
                port = str(dev.pluginProps['phSensorIfKitAnalogInput'])
                phDevId = dev.id

                # Now, we need to know which interface kit this sensor device is attached to...
                ifKitSerial = str(dev.pluginProps['phSensorIfKitSerial'])
                ifKitDevId = int(dev.pluginProps['phSensorIfKitId'])
                ifKitIndex = ifKitSerial + '-' + port
                phSerial = 'Analog Sensor on ' + ifKitSerial + ' index ' + port

                # If the ifKit's thread is running, we do an update
                try:
                    if ifKitIndex in self.phIfKitSensorDict:
                        self.phThreadDict[ifKitDevId].readSensorInput(int(port))
                        if self.logLevel > 0: indigo.server.log('Started and updated: %s' % (dev.name))
                except:
                        pass

                # Now we store the model and device id in an array entry
                # indexed by the ifkit device id and port number
                if ifKitIndex in self.phIfKitSensorDict:
                    self.phIfKitSensorDict[ifKitIndex] = {'model': model, 'id': phDevId}
                else:
                    self.phIfKitSensorDict[ifKitIndex] = {}
                    self.phIfKitSensorDict[ifKitIndex] = {'model': model, 'id': phDevId}

                # Add this device to the cross reference
                if str(ifKitDevId) in self.ifKitPseudoDevDict:
                    self.ifKitPseudoDevDict[str(ifKitDevId)] = self.ifKitPseudoDevDict[str(ifKitDevId)] + ',' + str(dev.id)
                else:
                    self.ifKitPseudoDevDict[str(ifKitDevId)] = str(dev.id)

                if self.logLevel > 1: indigo.server.log('Added Sensor: %s' % dev.name)
                if self.logLevel > 2: indigo.server.log('Added sensor entry: ifKitDevice:%s, port:%s, = %s' % (ifKitSerial, port, str(self.phIfKitSensorDict[ifKitIndex])))

            elif dev.deviceTypeId == 'phDiIfKit':
                model = dev.pluginProps['phDiIfKitModel']
                port = str(dev.pluginProps['phDiIfKitInput'])
                phDevId = dev.id

                ifKitSerial = str(dev.pluginProps['phDiIfKitSerial'])
                ifKitDevId = int(dev.pluginProps['phDiIfKitId'])
                ifKitIndex = ifKitSerial + '-' + port
                phSerial = 'Digital Output on ' + ifKitSerial + ' index ' + port

                # If the ifKit's thread is running, we do an update
                try:
                    if ifKitIndex in self.phIfKitInputDict:
                        self.phThreadDict[ifKitDevId].readDigitalInput(int(port))
                        if self.logLevel > 1: indigo.server.log('Started and updated: %s' % (dev.name))
                except:
                        pass

                if ifKitIndex in self.phIfKitInputDict:

                    self.phIfKitInputDict[ifKitIndex] = phDevId
                else:
                    self.phIfKitInputDict[ifKitIndex] = {}
                    self.phIfKitInputDict[ifKitIndex] = phDevId

                # Add this device to the cross reference
                if str(ifKitDevId) in self.ifKitPseudoDevDict:
                    self.ifKitPseudoDevDict[str(ifKitDevId)] = self.ifKitPseudoDevDict[str(ifKitDevId)] + ',' + str(dev.id)
                else:
                    self.ifKitPseudoDevDict[str(ifKitDevId)] = str(dev.id)

                if self.logLevel > 1: indigo.server.log('Added Digital Input: %s' % dev.name)
                if self.logLevel > 2: indigo.server.log('Added Input entry: ifKitDevice:%s, port:%s, = %s' % (ifKitSerial, port, str(self.phIfKitInputDict[ifKitIndex])))

            elif dev.deviceTypeId == 'phDoIfKit':
                ifKitSerial = str(dev.pluginProps['phDoIfKitSerial'])
                model = dev.pluginProps['phDoIfKitModel']
                port = str(dev.pluginProps['phDoIfKitOutput'])
                phDevId = dev.id

                ifKitSerial = str(dev.pluginProps['phDoIfKitSerial'])
                ifKitDevId = int(dev.pluginProps['phDoIfKitId'])
                ifKitIndex = ifKitSerial + '-' + port
                phSerial = 'Digital Input on ' + ifKitSerial + ' index ' + port

                # If the ifKit's thread is running, we do an update
                try:
                    if ifKitIndex in self.phIfKitOutputDict:
                        self.phThreadDict[ifKitDevId].readDigitalOutput(int(port))
                        if self.logLevel > 0: indigo.server.log('Started and updated: %s' % (dev.name))
                except:
                        pass

                if ifKitIndex in self.phIfKitOutputDict:
                    self.phIfKitOutputDict[ifKitIndex] = phDevId
                else:
                    self.phIfKitOutputDict[ifKitIndex] = {}
                    self.phIfKitOutputDict[ifKitIndex] = phDevId

                # Add this device to the cross reference
                if str(ifKitDevId) in self.ifKitPseudoDevDict:
                    self.ifKitPseudoDevDict[str(ifKitDevId)] = self.ifKitPseudoDevDict[str(ifKitDevId)] + ',' + str(dev.id)
                else:
                    self.ifKitPseudoDevDict[str(ifKitDevId)] = str(dev.id)

                if self.logLevel > 1: indigo.server.log('Added Digital Output: %s' % dev.name)
                if self.logLevel > 2: indigo.server.log('Added Output entry: ifKitDevice:%s, port:%s, = %s' % (ifKitSerial, port, str(self.phIfKitOutputDict[ifKitIndex])))

            self.log.log(2, dbFlg, '%s: Added type:%s, name:%s, serial:%s' % (funcName, dev.deviceTypeId, dev.name, phSerial), self.logName)
            self.log.log(2, dbFlg, 'exiting %s with:%s' % (funcName, threading.enumerate()), self.logName)

    ########################################
    def deviceStopComm(self, dev):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "Entering %s for device: %s (%d - %s)" % (funcName, dev.name, dev.id, dev.deviceTypeId), self.logName)

        # if self.logLevel > 1:  indigo.server.log(u"Entering deviceStopComm for device: %s (%d - %s)" % (dev.name, dev.id, dev.deviceTypeId), type=self.pluginDisplayName, isError=False)
        # return

        # if dev.deviceTypeId == "ifKit" or dev.deviceTypeId == "phStandalonePhidget" or dev.deviceTypeId == "phLcdScreen":
        if dev.deviceTypeId in ['ifKit', 'phStandalonePhidget', 'phLcdScreen']:
            try:
                self.phThreadDict[int(dev.id)].stop()
                del self.phThreadDict[int(dev.id)]
                self.sleep(.5)
                # remove ifkit from self.phThreadDict
                # self.sleep(1)
                # if self.logLevel > 1: indigo.server.log(u"deviceStopComm: deviceStopComm: stopped thread for: %s" % (dev.name), type=self.pluginDisplayName, isError=False)
                self.log.log(2, dbFlg, '%s: stopped thread for: %s' % (funcName, dev.name), type=self.pluginDisplayName)

            except Exception, e:
                    indigo.server.log("deviceStopComm: ERROR: %s" % e, type=self.pluginDisplayName, isError=True)
        elif dev.deviceTypeId == 'phIfKitSensor':
            port = str(dev.pluginProps['phSensorIfKitAnalogInput'])
            ifKitSerial = str(dev.pluginProps['phSensorIfKitSerial'])
            ifKitIndex = ifKitSerial + '-' + port

            try:
                del self.phIfKitSensorDict[ifKitIndex]
            except:
                self.log.log(0, dbFlg, '%s: attempted to delete analog sensor %s, but it had not yet been fully configured.' % (funcName, dev.name), type=self.pluginDisplayName)

            # if self.logLevel > 1: indigo.server.log('deviceStopComm: Deleted sensor: %s' % (dev.name), type=self.pluginDisplayName, isError=False)
            self.log.log(2, dbFlg, '%s: deleted sensor: %s' % (funcName, dev.name), type=self.pluginDisplayName)

        elif dev.deviceTypeId == 'phDiIfKit':
            port = str(dev.pluginProps['phDiIfKitInput'])
            ifKitSerial = str(dev.pluginProps['phDiIfKitSerial'])
            ifKitIndex = ifKitSerial + '-' + port

            try:
                del self.phIfKitInputDict[ifKitIndex]
            except:
                self.log.log(0, dbFlg, '%s: attempted to delete digital input %s, but it had not yet been fully configured.' % (funcName, dev.name), type=self.pluginDisplayName)

            # if self.logLevel > 1: indigo.server.log('deviceStopComm: Deleted Digital input: %s' % (dev.name), type=self.pluginDisplayName, isError=False)
            self.log.log(2, dbFlg, '%s: deleted digital input: %s' % (funcName, dev.name), type=self.pluginDisplayName)

        elif dev.deviceTypeId == 'phDoIfKit':
            port = str(dev.pluginProps['phDoIfKitOutput'])
            ifKitSerial = str(dev.pluginProps['phDoIfKitSerial'])
            ifKitIndex = ifKitSerial + '-' + port

            try:
                del self.phIfKitOutputDict[ifKitIndex]
            except:
                self.log.log(0, dbFlg, '%s: attempted to delete digital output %s, but it had not yet been fully configured.' % (funcName, dev.name), type=self.pluginDisplayName)

            # if self.logLevel > 1: indigo.server.log('deviceStopComm: Deleted Digital output: %s' % (dev.name), type=self.pluginDisplayName, isError=False)
            self.log.log(2, dbFlg, '%s: deleted digital output: %s' % (funcName, dev.name), type=self.pluginDisplayName)
        
        # if self.logLevel > 2: indigo.server.log(u"exiting deviceStopComm -->>", type=self.pluginDisplayName, isError=False)
        self.log.log(2, dbFlg, 'exiting %s' % funcName, self.logName)

    ########################################
    def didDeviceCommPropertyChange(self, origDev, newDev):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        if self.log.logLevel >= 2 or dbFlg: 
            self.log.log(2, dbFlg, "Entering %s for device: %s (%d - %s)" % (funcName, newDev.name, newDev.id, newDev.deviceTypeId), self.logName)

        # if self.logLevel > 1: indigo.server.log(u"Entering didDeviceCommPropertyChange for device: %s (%d - %s)" % (newDev.name, newDev.id, newDev.deviceTypeId), type=self.pluginDisplayName, isError=False)

        if origDev.pluginProps != newDev.pluginProps:
            self.log.log(2, dbFlg, '%s: plugin properties have changed for device: %s' % (funcName, newDev.name), self.logName)
            # if self.logLevel > 1: indigo.server.log(u"didDeviceCommPropertyChange: plugin properties have changed for device: %s" % (newDev.name), type=self.pluginDisplayName, isError=False)

            if newDev.deviceTypeId == "ifKit" or newDev.deviceTypeId == "phStandalonePhidget" or newDev.deviceTypeId == "phLcdScreen":
                self.log.log(2, dbFlg, '%s: Restarting device: %s' % (funcName, newDev.name), self.logName)
                # if self.logLevel > 1: indigo.server.log(u"didDeviceCommPropertyChange: Restarting device: %s" % (newDev.name), type=self.pluginDisplayName, isError=False)
                # If this is a standalone device, make sure it gets restarted on any changes
                return True
            elif newDev.deviceTypeId == 'phIfKitSensor':
                # This is an analog sensor -- Nothing to restart, but we should re-read the index value
                ifKitDevId = int(newDev.pluginProps['phSensorIfKitId'])
                ifKitDevIndex = int(newDev.pluginProps['phSensorIfKitAnalogInput'])
                # if self.logLevel > 1:indigo.server.log(u"didDeviceCommPropertyChange: Sensor attached to dev num: %s" % ifKitDevId, type=self.pluginDisplayName, isError=False)
                self.phThreadDict[ifKitDevId].readSensorInput(ifKitDevIndex)
            elif newDev.deviceTypeId == 'phDiIfKit':
              # This is a digital input -- Nothing to restart, but we should re-read the index state
                ifKitDevId = int(newDev.pluginProps['phDiIfKitId'])
                ifKitDevIndex = int(newDev.pluginProps['phDiIfKitInput'])
                # if self.logLevel > 1: indigo.server.log(u"didDeviceCommPropertyChange: Digital Input on dev num: %s" % ifKitDevId, type=self.pluginDisplayName, isError=False)
                self.phThreadDict[ifKitDevId].readDigitalInput(ifKitDevIndex)
            elif newDev.deviceTypeId == 'phDoIfKit':
              # This is a digital input -- Nothing to restart, but we should re-read the index state
                ifKitDevId = int(newDev.pluginProps['phDoIfKitId'])
                ifKitDevIndex = int(newDev.pluginProps['phDoIfKitOutput'])
                # if self.logLevel > 1: indigo.server.log(u"didDeviceCommPropertyChange: Digital Output on dev num: %s" % ifKitDevId, type=self.pluginDisplayName, isError=False)
                self.phThreadDict[ifKitDevId].readDigitalOutput(ifKitDevIndex)

            self.log.log(2, dbFlg, '%s: Saved change for: %s %s' % (funcName, newDev.deviceTypeId, newDev.name), self.logName) 
        else:
            # if self.logLevel > 2: indigo.server.log(u"didDeviceCommPropertyChange: No plugin property changes for device: %s" % (newDev.name), type=self.pluginDisplayName, isError=False)
            if self.log.logLevel >= 2 or dbFlg: self.log.log(0, dbFlg, '%s: No plugin property changes for: %s %s' % (funcName, newDev.deviceTypeId, newDev.name), self.logName) 

        return False

    ########################################
    def closedPrefsConfigUi(self, valuesDict, UserCancelled):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "Entering %s" % (funcName), self.logName)

        # if self.logLevel > 1: indigo.server.log(u"Entering closedPrefsConfigUi", type=self.pluginDisplayName)
        if UserCancelled is False:
            (self.logLevel, self.debug) = setLogLevel(self, self.pluginDisplayName, valuesDict["showDebugInfo1"])

        if self.logLevel > 0: indigo.server.log("Phidgets plugin preferences have been updated.")
        self.log.log(2, dbFlg, '%s: Phidgets plugin preferences have been updated.' % (funcName), self.logName)

    ########################################
    # Most plugins do not need to subclass getDeviceStateList() because by default
    # it returns the <States> list as defined in Devices.xml. However, we allow
    # individual device instance overrides of state label names, which we want
    # to use here. We need to dynamically change the device states list provided based
    # on specific device instance data (not just device types).
    # http://www.perceptiveautomation.com/wiki/doku.php?id=indigo_6_documentation:device_class#about_custom_device_states
    ########################################
    def getDeviceStateList(self, dev):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, 'Entering %s for device: %s (%d - %s)' % (funcName, dev.name, dev.id, dev.deviceTypeId), self.logName)
        
        #indigo.server.log('Entering getDeviceStateList with: %s' % dev, type="Phidgets DEBUG")
        # if self.logLevel > 1: indigo.server.log(u"Entering getDeviceStateList for: %s" % dev.name, type=self.pluginDisplayName)

        typeId = dev.deviceTypeId

        self.log.log(2, dbFlg, '%s: Found TYPE ID:%s in DICT:\n%s' % (funcName, typeId, self.devicesTypeDict[typeId][u'States']), self.logName)
        # if self.logLevel > 2: indigo.server.log("Found TYPE ID:%s in DICT:\n%s" % (typeId, self.devicesTypeDict[typeId][u'States']))
        statesList = self.devicesTypeDict[typeId][u'States']

        # Make sure we have a valid typeId 'phIfKitSensor'
        if typeId not in self.devicesTypeDict:
            return statesList

        # If we did not get a states list, this is a new device, so just return whatever we got and quit
        if "lastUpdate" in dev.states.keys():
            pass
        else:
            #indigo.server.log('Is in List, but not ready', type="Phidgets TESTING")
            return statesList

        propsIdx = typeId + 'Model'
        self.log.log(3, dbFlg, '%s: propsIdx was:%s' % (funcName, propsIdx), self.logName)
        devType = dev.pluginProps[propsIdx]
        self.log.log(3, dbFlg, '%s: states list was:%s' % (funcName, statesList), self.logName)

        try:  # Interface Kits do not have states defined in the dict
            states = self.phidgetsDict[devType]['states']
            for state in range(1, states + 1):
                self.log.log(3, dbFlg, '%s: FOUND state:%s\n%s' % (funcName, state, self.phidgetsDict[devType][state]), self.logName)
                #{'Disabled':'false', 'Key':'position', 'StateLabel':'Position', 'TriggerLabel':'Position', 'Type':100

                stateDisabled = self.phidgetsDict[devType][state]['Disabled']
                stateKey = self.phidgetsDict[devType][state]['Key']
                stateStateLabel = self.phidgetsDict[devType][state]['StateLabel']
                stateTriggerLabel = self.phidgetsDict[devType][state]['TriggerLabel']
                stateType = self.phidgetsDict[devType][state]['Type']

                stateDict = {'Disabled': stateDisabled, 'Key': stateKey, 'StateLabel': stateStateLabel, 'TriggerLabel': stateTriggerLabel, 'Type': stateType}
                statesList.append(stateDict)
        except:
            pass

        # create extra states for displays
        if typeId == 'phLcdScreen': # and (dev.pluginProps['phLcdScreen'] == "4x20"  or dev.pluginProps['phLcdScreen'] == "4x40"):
            for textLine in range(1, int(dev.pluginProps['phLcdScreenRows'])):
                stateKey = 'textLine_' + str(textLine)
                stateDict = {'Disabled': False, 'Key': stateKey, 'StateLabel': stateKey, 'TriggerLabel': stateKey, 'Type': 100}
                statesList.append(stateDict)

        # manage states for the frequency counter
        if dev.deviceTypeId == "phStandalonePhidget"  and dev.pluginProps['phStandalonePhidgetModel'] == '1054': 
            if dev.pluginProps['fcUseCustom']:
                stateKey = dev.pluginProps['fcCustomName']
                stateDict = {'Disabled': False, 'Key': stateKey, 'StateLabel': stateKey, 'TriggerLabel': stateKey, 'Type': 100}
                statesList.append(stateDict)

        # manage states for the Circular Touch Sensor
        if dev.deviceTypeId == "phStandalonePhidget"  and dev.pluginProps['phStandalonePhidgetModel'] == '1016': 
            stateDict = {'Disabled': False, 'Key': 'state', 'StateLabel': 'status', 'TriggerLabel': 'status', 'Type': 100}
            statesList.remove(stateDict)
         
        self.log.log(3, dbFlg, '%s: FINISHED STATE' % funcName, self.logName)
        self.log.log(3, dbFlg, '%s: new states list is:%s' % (funcName, statesList), self.logName)

        return statesList

    ########################################
    def getDeviceDisplayStateId(self, dev):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, 'Entering %s for device: %s (%d - %s)' % (funcName, dev.name, dev.id, dev.deviceTypeId), self.logName)
        self.log.log(4, dbFlg, '%s: Received device:\n%s' % (funcName, dev), self.logName)

        try:  # Maybe this device hasn't been configured yet
            if dev.deviceTypeId == "phStandalonePhidget"  and dev.pluginProps['phStandalonePhidgetModel'] == '1054': 
                displayState = dev.pluginProps['fcDisplay']

                if displayState == 'custom':
                    displayState = dev.pluginProps['fcCustomName']

                return displayState
        except:
            pass

        return self.devicesTypeDict[dev.deviceTypeId][u'DisplayStateId']
    
    ########################################
    # Relay device (Digital Outputs) Callbacks
    # and Action Callbacks
    ########################################

    ########################################
    def actionControlDimmerRelay(self, action, dev):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, 'Entering %s for device: %s (%d - %s)' % (funcName, dev.name, dev.id, dev.deviceTypeId), self.logName)
        
        # if self.logLevel > 1: indigo.server.log(u"Entering actionControlDimmerRelay", type=self.pluginDisplayName)

        ifKitDev = int(dev.pluginProps['phDoIfKitId'])
        #  ifKitSerial = int(dev.pluginProps['phDoIfKitSerial'])
        digitalOut = int(dev.pluginProps['phDoIfKitOutput'])

        if self.logLevel > 2:
            indigo.server.log(u"metaMode:%s" % (action.deviceAction), type=self.pluginDisplayName)

        ###### TURN ON ######
        if action.deviceAction == indigo.kDeviceAction.TurnOn:
            # Command hardware module (dev) to turn ON here:
            if self.logLevel > 3: indigo.server.log('device on:\n%s' % action, type=self.pluginDisplayName)

            self.phThreadDict[ifKitDev].writeDigitalOutput(digitalOut, True, 0)
            sendSuccess = True        # Set to False if it failed.

            if sendSuccess:
                # If success then log that the command was successfully sent.
                if self.logLevel > 2: indigo.server.log(u"sent \"%s\" %s" % (dev.name, "on"), type=self.pluginDisplayName)

                # And then tell the Indigo Server to update the state.
                dev.updateStateOnServer("onOffState", True)
            else:
                # Else log failure but do NOT update state on Indigo Server.
                indigo.server.log(u"send \"%s\" %s failed" % (dev.name, "on"), type=self.pluginDisplayName, isError=True)

        ###### TURN OFF ######
        elif action.deviceAction == indigo.kDeviceAction.TurnOff:
            # Command hardware module (dev) to turn OFF here:
            if self.logLevel > 3: indigo.server.log('device off:\n%s' % action, type=self.pluginDisplayName)

            self.phThreadDict[ifKitDev].writeDigitalOutput(digitalOut, False, 0)

            sendSuccess = True        # Set to False if it failed.

            if sendSuccess:
                # If success then log that the command was successfully sent.
                if self.logLevel > 2: indigo.server.log(u"sent \"%s\" %s" % (dev.name, "off"), type=self.pluginDisplayName)

                # And then tell the Indigo Server to update the state:
                dev.updateStateOnServer("onOffState", False)
            else:
                # Else log failure but do NOT update state on Indigo Server.
                indigo.server.log(u"send \"%s\" %s failed" % (dev.name, "off"), type=self.pluginDisplayName, isError=True)

        ###### TOGGLE ######
        elif action.deviceAction == indigo.kDeviceAction.Toggle:
            # Command hardware module (dev) to toggle here:
            newOnState = not dev.onState
            newState = 'On'
            if dev.onState:
                newState = 'Off'
                self.phThreadDict[ifKitDev].writeDigitalOutput(digitalOut, False, 0)
            else:
                self.phThreadDict[ifKitDev].writeDigitalOutput(digitalOut, True, 0)

            sendSuccess = True        # Set to False if it failed.

            if sendSuccess:
                # If success then log that the command was successfully sent.
                if self.logLevel > 2: indigo.server.log(u"sent \"%s\" has been toggled and is now %s" % (dev.name, newState), type=self.pluginDisplayName)

                # And then tell the Indigo Server to update the state:
                dev.updateStateOnServer("onOffState", newOnState)
            else:
                # Else log failure but do NOT update state on Indigo Server.
                indigo.server.log(u"send \"%s\" %s failed" % (dev.name, "toggle"), type=self.pluginDisplayName, isError=True)

   ########################################
    def phidgetOutputControl(self, action):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        
        if self.logLevel > 1:
            indigo.server.log(u"Entering phidgetOutputControl", type=self.pluginDisplayName)

        """ Output control for Standalone Phidgets """
        # self.errorLog('Action:\n%s\n\nDevice:\n%s\n\n' % (action, dev))
        if self.logLevel > 2: self.errorLog('Action:\n%s\n' % (action), type=self.pluginDisplayName)
        phFunction = action.props['phFunction']
        phDevice = int(action.props['phDevice'])
        digitalOut = int(action.props['outputNum'])
        if self.logLevel > 0: indigo.server.log('Action:%s Device:%s Index:%s' % (phFunction, phDevice, digitalOut))

        if phDevice in self.phThreadDict:
            if phFunction == 'turnOn':
                self.phThreadDict[phDevice].writeDigitalOutput(digitalOut, True)
            elif phFunction == 'turnOff':
                self.phThreadDict[phDevice].writeDigitalOutput(digitalOut, False)
            elif phFunction == 'toggle':
                phOutput = 'output' + str(digitalOut)

                if dev.states[phOutput] == 'True':
                    self.phThreadDict[phDevice].writeDigitalOutput(digitalOut, False)
                else:
                    self.phThreadDict[phDevice].writeDigitalOutput(digitalOut, True)
            else:
                if self.logLevel > 0: indigo.server.log('Unexpected action call', type=self.pluginDisplayName, isError=True)
        else:
            if self.logLevel > 0: indigo.server.log('Device "%s" not available. Check that communications are enabled foor this device.' % indigo.devices[phDevice].name, type=self.pluginDisplayName, isError=True)

    # ########################################
    def phidgetIfkitOutputControl(self, action, dev):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        
        if self.logLevel > 1:
            indigo.server.log(u"Entering phidgetIfkitOutputControl", type=self.pluginDisplayName)
        if self.logLevel > 2: indigo.server.log('Action:\n%s\n' % (action), type=self.pluginDisplayName)
        #if self.logLevel > 2: indigo.server.log('dev: %s' % (dev), type=self.pluginDisplayName)

        phFunction = action.props['phFunction']
        digitalOut = int(indigo.devices[int(action.props['phDevice'])].pluginProps['phDoIfKitOutput'])
        ifKitDevId = int(indigo.devices[int(action.props['phDevice'])].pluginProps['phDoIfKitId'])
        pulseLength = int(action.props['pulseLength'])
        if self.logLevel > 2: indigo.server.log('Action:%s Device:%s Pulse Length:%s' % (phFunction, digitalOut, pulseLength))

        if phFunction == 'pulseOnOff' or phFunction == 'pulseOffOn':
            try:
                self.phThreadDict[ifKitDevId].writeDigitalOutput(digitalOut, phFunction, pulseLength)
            except:
                indigo.server.log('The devce "%s" is not available to be pulsed.' % indigo.devices[int(action.props['phDevice'])].name, type=self.pluginDisplayName, isError=True)
        else:
            if self.logLevel > 2: indigo.server.log('Unexpected action call', type=self.pluginDisplayName)

   ########################################
    def textLcdWrite(self, action, dev):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        
        if self.logLevel > 1:
            indigo.server.log(u"Entering textLcdWrite", type=self.pluginDisplayName)
        if self.logLevel > 2: indigo.server.log('Action:\n%s\n\nDevice:\n%s\n\n' % (action, dev.id), type=self.pluginDisplayName)

        writeDelay = float(dev.pluginProps['writeDelay'])
        if writeDelay > 0:
            writeDelay = writeDelay/1000

        # Loop through up to 4 lines of display
        for textLine in range(0, int(action.props['displayLinesNum'])):
            try:
                if action.props['displayLine_' + str(textLine)]:
                    lcdMessage = action.props['lcdMessage_' + str(textLine)]
                    self.log.log(2, dbFlg, '%s: Found input message to write:%s' % (funcName, lcdMessage), self.logName)
                    lcdMessage = self.substitute(lcdMessage, validateOnly=False)
                    if dev.pluginProps['useCustChars']:
                        lcdMessage = self.substituteCustomChar(lcdMessage, dev.id)

                    self.log.log(2, dbFlg, '%s: Final output message to write:%s:%s' % (funcName, lcdMessage, repr(lcdMessage)), self.logName)
                    self.phThreadDict[dev.id].writeDigitalOutput(textLine, lcdMessage)
                    self.sleep(writeDelay)
            except Exception, e:
                self.errorLog('Error %s' % e)

    # This call has been replaced by a a similar call, above, that uses a method provided by the API
        # # Loop through up to 4 lines of display
        # for textLine in range(0, int(action.props['displayLinesNum'])):
        #     try:
        #         if action.props['displayLine_' + str(textLine)]:
        #             lcdMessage = self.substituteDeviceState(action.props['lcdMessage_' + str(textLine)])
        #             lcdMessage = self.substituteVariable(lcdMessage)
        #             if dev.pluginProps['useCustChars']:
        #                 lcdMessage = self.substituteCustomChar(lcdMessage, dev.id)

        #             self.log.log(2, dbFlg, '%s: Final message to write:%s' % (funcName, lcdMessage), self.logName)
        #             self.phThreadDict[dev.id].writeDigitalOutput(textLine, lcdMessage)
        #     except Exception, e:
        #         self.errorLog('Error %s' % e)

 ########################################
    def textLcdSettings(self, action, dev):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        
        self.log.log(2, dbFlg, 'Entering %s for action: %s, value:%s for device:%s' % (funcName, action.pluginTypeId, action.props['phLcdControlValue'], dev.name), self.logName)

        try:
            self.phThreadDict[dev.id].controlDisplaySettings(action.pluginTypeId, action.props['phLcdControlValue'])
        except Exception, e:
                self.errorLog('Error %s' % e)

    ########################################
    # Device UI methods (works with Devices.xml):
    ######################
    def validateDeviceConfigUi(self, valuesDict, typeId, devId):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(3, dbFlg, '%s: Received valuesDict:\n%s' % (funcName, valuesDict), self.logName)
        
        if self.logLevel > 1:
            indigo.server.log(u"Entering validateDeviceConfigUi", type=self.pluginDisplayName)

        if self.logLevel > 2: indigo.server.log(">> ValuesDict:\n%s\n" % valuesDict, type=self.pluginDisplayName)
        if self.logLevel > 2: indigo.server.log(">> typeId: %s" % typeId, type=self.pluginDisplayName)
        if self.logLevel > 2: indigo.server.log(">> devId:%s" % devId, type=self.pluginDisplayName)

        if typeId == 'phIfKitSensor':
            addressCol = indigo.devices[int(valuesDict['phSensorIfKitId'])].name + " |a " + valuesDict['phSensorIfKitAnalogInput']
        elif typeId == 'phDoIfKit':
            addressCol = indigo.devices[int(valuesDict['phDoIfKitId'])].name + " |do " + valuesDict['phDoIfKitOutput']
        elif typeId == 'phDiIfKit':
            addressCol = indigo.devices[int(valuesDict['phDiIfKitId'])].name + " |di " + valuesDict['phDiIfKitInput']
        elif typeId == 'phInterfaceKit' or typeId == 'ifKit':
            addressCol = valuesDict['ifKitIpAddress']
        elif typeId == 'phStandalonePhidget':
            if valuesDict['phStandaloneCommType'] == "IP":
                addressCol = valuesDict['phStandaloneIpAddress']
            else:
                addressCol = valuesDict['phStandaloneCommType']

            if valuesDict['phStandalonePhidgetModel'] == '1054': # Cleanup unwanted props and add others
                # indigo.server.log(">> ValuesDict:\n%s\n" % valuesDict, type=self.pluginDisplayName, isError=True)
                del valuesDict['tCouple0']
                del valuesDict['tCouple1']
                del valuesDict['tCouple2']
                del valuesDict['tCouple3']
                del valuesDict['tSens0']
                del valuesDict['tSens1']
                del valuesDict['tSens2']
                del valuesDict['tSens3']

                if valuesDict['fcUseCustom']:
                    valuesDict['fcDisplay'] = valuesDict['fcDisplay1']
                else:
                    valuesDict['fcDisplay'] = valuesDict['fcDisplay2']

                if self.logLevel > 2: indigo.server.log(">> ValuesDict:\n%s\n" % valuesDict, type=self.pluginDisplayName, isError=True)

        elif typeId == 'phLcdScreen':
            if valuesDict['phLcdScreenCommType'] == "IP":
                addressCol = valuesDict['phLcdScreenIpAddress']
            else:
                addressCol = valuesDict['phLcdScreenSerialPort']  

            if valuesDict['phLcdAdapter'] == "1203":
                valuesDict['phLcdScreen'] = "2x20"

            valuesDict['phLcdScreenRows'],valuesDict['phLcdScreenCols'] = valuesDict['phLcdScreen'].split('x')  

        else:
            if self.logLevel > 0: indigo.server.log(u'Phidget type: %s not recognized' % (typeId), type="Phidgets warning", isError=True)
            addressCol = "- n/a -"

        valuesDict['address'] = addressCol
        if self.logLevel > 2: indigo.server.log("ValuesDict:\n%s\n" % valuesDict, type=self.pluginDisplayName)

        return (True, valuesDict)

    ########################################
    def phidgetsLibLoggingControl(self, logging, logLevel, logFile):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        
        if self.logLevel > 1:
            indigo.server.log(u"Entering phidgetsLibLoggingControl", type=self.pluginDisplayName)

        if self.logLevel > 2: indigo.server.log('logging: %s, logLevel: %s, logFile: %s' % (logging, logLevel, logFile), type=self.pluginDisplayName)

        if logging:
            try:
                Phidget.disableLogging()
                Phidget.enableLogging(int(logLevel), logFile)
                Phidget.log(logLevel, 'Indigo Phidgets Plugin', 'Phidgets low level libs logging started')
            except:
                indigo.server.log("Unexpected error:%s for phidgets service" % (sys.exc_info()), type=self.pluginDisplayName, isError=True)

            if self.logLevel > 0:
                indigo.server.log(u'Low level phidgets libs logging started at level %s to file %s' % \
                (logLevel, logFile), type=self.pluginDisplayName, isError=False)
        else:
            try:
                Phidget.log(logLevel, 'Indigo Phidgets Plugin', 'Phidgets low level libs logging stopped')
                Phidget.disableLogging()
            except:
                indigo.server.log("Unexpected error:%s" % str(sys.exc_info()), type=self.pluginDisplayName, isError=True)

            if self.logLevel > 0:
                indigo.server.log(u'Low level phidgets libs logging stopped', type=self.pluginDisplayName, isError=False)

        return

    ########################################
    def validatePrefsConfigUi(self, valuesDict):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        
        # We'll just pass everything to phidgetsLibLoggingControl, just like happens as startup.
        if self.logLevel > 1:
            indigo.server.log(u"Entering validatePrefsConfigUi", type=self.pluginDisplayName)

        if self.logLevel > 2: indigo.server.log("ValuesDict:\n%s\n" % valuesDict, type=self.pluginDisplayName)
        self.phidgetsLibLoggingControl(valuesDict['pl0'], int(valuesDict['pl1']), valuesDict['pl2'])

        return (True, valuesDict)

    ########################################
    # ConfigUI supporting methods
    ########################################
    def getIfKitList(self, filter="", valuesDict=None, typeId="", targetId=0):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        
        if self.logLevel > 1:
            indigo.server.log(u'Entered getIfKitList: %s', type=self.pluginDisplayName)

        myArray = []

        for ifKit in sorted(self.phidgetsDict.iterkeys()):
            if self.logLevel > 1: indigo.server.log(u'getIfKitList found ifKit: %s' % (ifKit), type=self.pluginDisplayName, isError=False)
            if self.phidgetsDict[ifKit]['model'] == 'phInterfaceKit':
                descr = ifKit + " - " + self.phidgetsDict[ifKit]['descr']
                if self.logLevel > 2: indigo.server.log("ifKit:%s, descr:%s" % (ifKit, descr), type=self.pluginDisplayName)
                myArray.append((ifKit, descr))

        return myArray

    ########################################
    def getIfKitIOList(self, filter="", valuesDict=None, typeId="", targetId=0):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        
        if self.logLevel > 1:
            indigo.server.log(u"Entering getIfKitIOList", type=self.pluginDisplayName)
        if self.logLevel > 2: indigo.server.log("ValuesDict:typeId=%s, targetId=%s\n%s\n" % (typeId, targetId, valuesDict), type=self.pluginDisplayName)

        myArray = []
        if valuesDict:
            if self.logLevel > 2: indigo.server.log("Dictionary exists", type=self.pluginDisplayName)

            # Use the device id of the ifkit to get the correct number of entries for the port list
            if typeId == 'phIfKitSensor':
                numPorts = indigo.devices[int(valuesDict['phSensorIfKitId'])].pluginProps['ifKitSensors']
            elif typeId == 'phDoIfKit':
                numPorts = indigo.devices[int(valuesDict['phDoIfKitId'])].pluginProps['ifKitDigitalOutputs']
            elif typeId == 'phDiIfKit':
                numPorts = indigo.devices[int(valuesDict['phDiIfKitId'])].pluginProps['ifKitDigitalInputs']
            else:
                numPorts = 16

            port = 0
            try:
                while port < int(numPorts):
                    myArray.append((str(port), str(port)))
                    port += 1
            except:
                if self.logLevel > 0: indigo.server.log(u'Error reading ifKit config for device: %s. Verify the ifKit was completely configured' % (dev.name), type=self.pluginDisplayName, isError=False)
            
        return myArray

    ########################################
    def getIfKitSensorList(self, filter="", valuesDict=None, typeId="", targetId=0):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        
        if self.logLevel > 1:
            indigo.server.log(u"Entering getIfKitSensorList", type=self.pluginDisplayName)
        myArray = []

        for sensor in sorted(self.phidgetsDict.iterkeys()):
            if self.phidgetsDict[sensor]['model'] == 'phIfKitSensor':
                descr = sensor + " - " + self.phidgetsDict[sensor]['descr']
                if self.logLevel > 2: indigo.server.log("sensor:%s, descr:%s" % (sensor, descr), type=self.pluginDisplayName)
                myArray.append((sensor, descr))

        if self.logLevel > 2: indigo.server.log('Selection List=\n%s\n' % myArray, type=self.pluginDisplayName)
        return myArray

    ########################################
    def getIfKitAnalogList(self, filter="", valuesDict=None, typeId="", targetId=0):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        
        if self.logLevel > 1:
            indigo.server.log(u"Entering getIfKitAnalogList", type=self.pluginDisplayName)
        myArray = []

        for dev in indigo.devices:
            try:
                modelNum = dev.pluginProps['ifKitModel']
                if self.logLevel > 2: indigo.server.log("modelNum:%s" % (modelNum), type=self.pluginDisplayName)
                if self.logLevel > 2: indigo.server.log("dict:%s" % (self.phidgetsDict[modelNum]['model']), type=self.pluginDisplayName)
                if dev.model == 'Phidget Interface Kit' and self.phidgetsDict[modelNum]['type'] == 'ADiDo':
                    myArray.append((dev.id, dev.name))
                else:
                    if self.logLevel > 2: indigo.server.log("model:%s" % (self.phidgetsDict[modelNum]['model']), type=self.pluginDisplayName)
            except:
                pass
        return myArray

    ########################################
    def getIfKitDigitalInList(self, filter="", valuesDict=None, typeId="", targetId=0):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        
        if self.logLevel > 1:
            indigo.server.log(u"Entering getIfKitList", type=self.pluginDisplayName)

        myArray = []

        for dev in indigo.devices:
            if self.logLevel > 1: indigo.server.log(u'getIfKitDigitalInList read dev: %s' % (dev.name), type=self.pluginDisplayName, isError=False)
            try:
                modelNum = dev.pluginProps['ifKitModel']
                ifKitType = self.phidgetsDict[modelNum]['type']
                if self.logLevel > 1: indigo.server.log(u'getIfKitDigitalInList found type: %s' % (ifKitType), type=self.pluginDisplayName, isError=False)
                if dev.model == 'Phidget Interface Kit' and (ifKitType == 'ADiDo' or ifKitType == 'DiDo'):
                    if self.logLevel > 2: indigo.server.log(u'getIfKitDigitalInList found ifKit: %s' % (dev), type=self.pluginDisplayName, isError=False)
                    myArray.append((dev.id, dev.name))
                else:
                    if self.logLevel > 2: indigo.server.log("model:%s" % (self.phidgetsDict[modelNum]['type']), type=self.pluginDisplayName)
            except:
                pass
        return myArray

    ########################################
    def getIfKitDigitalOutList(self, filter="", valuesDict=None, typeId="", targetId=0):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        
        if self.logLevel > 1:
            indigo.server.log(u"Entering getIfKitDigitalOutList", type=self.pluginDisplayName)

        if self.logLevel > 2: indigo.server.log(u'getIfKitDigitalOutList received valuesDict: %s' % (valuesDict), type=self.pluginDisplayName, isError=False)
        myArray = []

        for dev in indigo.devices:
            try:
                modelNum = dev.pluginProps['ifKitModel']
                if self.logLevel > 2: indigo.server.log("modelNum:%s" % (modelNum), type=self.pluginDisplayName)
                ifKitType = self.phidgetsDict[modelNum]['type']
                if self.logLevel > 2: indigo.server.log("dict:%s" % (self.phidgetsDict[modelNum]['model']), type=self.pluginDisplayName)
                if dev.model == 'Phidget Interface Kit' and (ifKitType == 'ADiDo' or ifKitType == 'DiDo' or ifKitType == 'Do'):
                    myArray.append((dev.id, dev.name))
                else:
                    if self.logLevel > 2: indigo.server.log("model:%s" % (self.phidgetsDict[modelNum]['type']), type=self.pluginDisplayName)
            except:
                pass

        return myArray

   ########################################
    def getEventCapableList(self, filter="", valuesDict=None, typeId="", targetId=0):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        
        if self.logLevel > 1:
            indigo.server.log(u"Entering getIfKitStandaloneList", type=self.pluginDisplayName)

        myArray = []

        for device in sorted(indigo.devices):
            if device.deviceTypeId == 'ifKit' or device.deviceTypeId == 'phStandalonePhidget' or device.deviceTypeId == 'phLcdScreen':
                if self.logLevel > 1: indigo.server.log(u'device list found: %s - %s' % (device.name, device.deviceTypeId), type=self.pluginDisplayName, isError=False)
                myArray.append((device.id, device.name))

        return myArray

    ########################################
    def getIfKitStandaloneList(self, filter="", valuesDict=None, typeId="", targetId=0):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        
        if self.logLevel > 1:
            indigo.server.log(u"Entering getIfKitStandaloneList", type=self.pluginDisplayName)

        myArray = []

        for modelNum in self.phidgetsDict:
            try:
                if self.phidgetsDict[modelNum]['model'] == 'phStandalonePhidget':
                    myArray.append((modelNum, self.phidgetsDict[modelNum]['descr']))
            except:
                pass
        return myArray

    ########################################
    def ifKitSetIOSize(self, valuesDict, typeId, devId):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        
        if self.logLevel > 1:
            indigo.server.log(u"Entering ifKitSetIOSize", type=self.pluginDisplayName)

        # Callback from config ifkit device type config button
        # Sets the size (number of input, output, or analog inputs) for the dynamic selection field

        if self.logLevel > 2: indigo.server.log("ifKitSetIOSize valuesDict:\n%s" % valuesDict, type=self.pluginDisplayName)
        if self.logLevel > 2: indigo.server.log("ifKitSetIOSize typeId:\n%s" % typeId, type=self.pluginDisplayName)
        if self.logLevel > 2: indigo.server.log("ifKitSetIOSize devId:\n%s" % devId, type=self.pluginDisplayName)

        if 'phIfKitSensorModel' in valuesDict:
            phKey1 = 'phSensor'
            phKey2 = 'Sensors'
            buttonFlag = 'buttonFlagSensor'
        elif 'phDiIfKitModel' in valuesDict:
            phKey1 = 'phDi'
            phKey2 = 'DigitalInputs'
            buttonFlag = 'buttonFlagDi'
        elif 'phDoIfKitModel' in valuesDict:
            phKey1 = 'phDo'
            phKey2 = 'DigitalOutputs'
            buttonFlag = 'buttonFlagDo'

        ifKitDevId = int(valuesDict[phKey1 + 'IfKitId'])
        if self.logLevel > 2: indigo.server.log('Index:%s, devid:%s' % (phKey1 + 'IfKitId', ifKitDevId), type=self.pluginDisplayName)

        ifKitDev = indigo.devices[ifKitDevId]
        self.ifKitSensorNum = int(ifKitDev.pluginProps['ifKit' + phKey2])
        ifKitSerial = ifKitDev.pluginProps['ifKitSerial']
        if self.logLevel > 2:
            if self.logLevel > 2: indigo.server.log('Sensors:%s, serial:%s' % (self.ifKitSensorNum, ifKitSerial), type=self.pluginDisplayName)

        valuesDict[phKey1 + 'IfKitSerial'] = ifKitSerial
        valuesDict[buttonFlag] = False

        if self.logLevel > 3:
            if self.logLevel > 2: indigo.server.log('DEBUG... ifKitDevId:%s, serial num:%s, ifKitDev:%s' % (ifKitDevId, ifKitSerial, str(ifKitDev)), type=self.pluginDisplayName)
        if self.logLevel > 2: indigo.server.log("Finished button handler", type=self.pluginDisplayName)

        return valuesDict

    ########################################
    def readLcdScreenConfig(self, valuesDict, typeId, devId):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        
        if self.logLevel > 1:
            indigo.server.log(u"Entering readLcdScreenConfig", type=self.pluginDisplayName)

        # Callback from config LCD Screen configuration
        if self.logLevel > 1: indigo.server.log(u'readLcdScreenConfig valuesDict received: %s' % (valuesDict), type="Phidgets", isError=False)
        if self.logLevel > 2: indigo.server.log("readLcdScreenConfig typeId:\n%s" % typeId, type=self.pluginDisplayName)
        if self.logLevel > 2: indigo.server.log("readLcdScreenConfig devId:\n%s" % devId, type=self.pluginDisplayName)

        if not devId in self.phThreadDict:
            if self.logLevel > 1: indigo.server.log(u'readLcdScreenConfig: no existing thread, creating new TextLCD', type="Phidgets", isError=False)
        wasAlreadyAttached = False

        # need to fix all of this to actually use the existing thread if it exists
        if 1 > 0:  # not self.textLCD.isAttached():
            if self.logLevel > 2: indigo.server.log(u"No existing screen found. Creating new textLCD", type=self.pluginDisplayName)

            try:
                textlcd = TextLCD()
            except RuntimeError, e:
                self.errorLog("Runtime Exception: %s" % e.details)
                self.errorLog("Exiting....")
                exit(1)

            if self.logLevel > 2: indigo.server.log("Opening TextLCD....", type=self.pluginDisplayName)

            try:
                textlcd.openRemoteIP(valuesDict['phLcdScreenIpAddress'], int(valuesDict['phLcdScreenIpPort']), serial=int(valuesDict['phLcdScreenSerial']))
                #self.textlcd.openRemoteIP("192.168.4.2",5001)
                #textlcd.openPhidget()
            except PhidgetException, e:
                self.errorLog("Phidget Exception a %i: %s" % (e.code, e.details))
                self.errorLog("Exiting....")
                exit(1)

            try:
                textlcd.waitForAttach(10000)
                if self.logLevel > 0: indigo.server.log(u'readLcdScreenConfig: new LCD Screen created', type="Phidgets", isError=False)
            except PhidgetException, e:
                self.errorLog("Phidget Exception b %i: %s" % (e.code, e.details))
                try:
                    textlcd.closePhidget()
                except PhidgetException, e:
                    self.errorLog("Phidget Exception c %i: %s" % (e.code, e.details))
                    self.errorLog("Exiting....")
                    exit(1)
                    self.errorLog("Exiting....")
                    exit(1)
        else:
            wasAlreadyAttached = True

        valuesDict['buttonFlagSensor'] = "true"

        if not wasAlreadyAttached:
            if self.logLevel > 2: indigo.server.log(u"New ifkit closed", type=self.pluginDisplayName)
            textlcd.closePhidget()

        if self.logLevel > 2: indigo.server.log(u"ifkit read was successful", type=self.pluginDisplayName)
        if self.logLevel > 2: indigo.server.log(u'readLcdScreenConfig valuesDict returned: %s' % (valuesDict), type="Phidgets", isError=False)
        return valuesDict

    ########################################
    def readIfKitConfig(self, valuesDict, typeId, devId):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        
        if self.logLevel > 1:
            indigo.server.log(u"Entering readIfKitConfig", type=self.pluginDisplayName)

        # Callback from config ifkit device type
        if self.logLevel > 2: indigo.server.log(u'readIfKitConfig valuesDict received: %s' % (valuesDict), type="Phidgets", isError=False)
        if self.logLevel > 2: indigo.server.log("readIfKitConfig typeId:\n%s" % typeId, type=self.pluginDisplayName)
        if self.logLevel > 2: indigo.server.log("readIfKitConfig devId:\n%s" % devId, type=self.pluginDisplayName)

        if not devId in self.phThreadDict:
            if self.logLevel > 1: indigo.server.log(u'readIfKitConfig: no existing thread, creating new ifkit', type="Phidgets", isError=False)
        wasAlreadyAttached = False
        if 1 > 0:  # not self.interfaceKit.isAttached():
            if self.logLevel > 2: indigo.server.log(u"No existing ifkit found. Creating new ifkit", type=self.pluginDisplayName)
            try:
                interfaceKit = InterfaceKit()
            except RuntimeError, e:
                self.errorLog("Runtime Exception: %s" % e.details)
                self.errorLog("Exiting....")
                exit(1)

            if self.logLevel > 2: indigo.server.log("Opening ifkit....", type=self.pluginDisplayName)

            try:
                phSerialNum = int(valuesDict['ifKitSerial'])
            except:
                phSerialNum = ""

            try:
                #### ar 8/1 adding log messages to capture locking on OpenRemoteIP
                if self.logLevel > 2: indigo.server.log("calling openRemoteIP (ip=%s , port=%s)" \
                   % (valuesDict['ifKitIpAddress'],valuesDict['ifKitIpPort']) , type=self.pluginDisplayName)
                ### end
                interfaceKit.openRemoteIP(valuesDict['ifKitIpAddress'], int(valuesDict['ifKitIpPort']), serial=phSerialNum)
                
                #### ar 8/1 adding log messages to capture locking on OpenRemoteIP
                if self.logLevel > 2: indigo.server.log("calling openRemoteIP completed (ip=%s , port=%s)" \
                   % (valuesDict['ifKitIpAddress'],valuesDict['ifKitIpPort']) , type=self.pluginDisplayName)
                #### end


            except PhidgetException, e:
                
                #### ar 8/1 updated errorlog message to include IP and Port of current device 
                # to help in tracking specific device errors in an Event code model
                self.errorLog("Phidget Exception a (ip=%s , port=%s) %i: %s" \
                   % (valuesDict['ifKitIpAddress'],valuesDict['ifKitIpPort']) ,(e.code, e.details))
                #### end

                self.errorLog("Exiting....")
                exit(1)

            try:
                ## ar 8/1 added server log message to track devices endering a waitForAttach call 
                if self.logLevel > 1: indigo.server.log(u'pre waitForAttach (ip=%s , port=%s) ' \
                   % (valuesDict['ifKitIpAddress'],valuesDict['ifKitIpPort']), type="Phidgets", isError=False)
                ## end

                interfaceKit.waitForAttach(10000)

                ## ar 8/1 added serverlog message to track devices returning from a waitForAttach call
                if self.logLevel > 1: indigo.server.log(u'post waitForAttach (ip=%s , port=%s) ' \
                   % (valuesDict['ifKitIpAddress'],valuesDict['ifKitIpPort']), type="Phidgets", isError=False)
                ## end
                
                if self.logLevel > 1: indigo.server.log(u'readIfKitConfig: new ifkit created. post waitForAttach', type="Phidgets", isError=False)

            except PhidgetException, e:
                ## ar log message mod
                if self.logLevel > 1: indigo.server.log(u'Execption raised on waitForAttach (ip=%s , port=%s) ' \
                   % (valuesDict['ifKitIpAddress'],valuesDict['ifKitIpPort']), type="Phidgets", isError=False)
                self.errorLog("Phidget Exception b (ip=%s , port=%s) %i: %s" % (valuesDict['ifKitIpAddress'],valuesDict['ifKitIpPort'],e.code, e.details))
                try:
                    interfaceKit.closePhidget()
                except PhidgetException, e:
                    self.errorLog("Phidget Exception c (ip=%s , port=%s) %i: %s" % (valuesDict['ifKitIpAddress'],valuesDict['ifKitIpPort'],e.code, e.details))
                    self.errorLog("Exiting....")
                    exit(1)
        else:
            wasAlreadyAttached = True

        ########################
        # ### ar 7/25 to catch exceptions caused by unreachable devices. exit if such an exception occurrs
        #sensorCount = interfaceKit.getSensorCount()
        #inputCount = interfaceKit.getInputCount()
        #ouputCount = interfaceKit.getOutputCount()
        try:
            sensorCount = interfaceKit.getSensorCount()
            inputCount = interfaceKit.getInputCount()
            ouputCount = interfaceKit.getOutputCount()
        except PhidgetException, e:
            self.errorLog("Phidget Exception d (ip=%s , port=%s) %i: %s" % (valuesDict['ifKitIpAddress'],valuesDict['ifKitIpPort'],e.code,e.details) )
            sensorCount=0
            inputCount=0
            ouputCount=0
            #ar try exiting...
            #exit(1)

        #########################    

        if self.logLevel > 1: indigo.server.log(u"Sensors:%s, inputs:%s, outputs:%s" % (sensorCount, inputCount, ouputCount), type="Phidgets", isError=False)
        valuesDict['ifKitSensors'] = sensorCount
        valuesDict['ifKitDigitalInputs'] = inputCount
        valuesDict['ifKitDigitalOutputs'] = ouputCount

        for sensor in range(0, sensorCount):
            dataRateMin = interfaceKit.getDataRateMin(sensor)
            dataRateMax = interfaceKit.getDataRateMax(sensor)
            changeTrigger = interfaceKit.getSensorChangeTrigger(sensor)
            if self.logLevel > 2: indigo.server.log("Sensor %s, trigger:%s, min:%s, max:%s" % (sensor, changeTrigger, dataRateMin, dataRateMax), type=self.pluginDisplayName)
            fieldId = 'ifKitSensorTrigger_' + str(sensor)
            valuesDict[fieldId] = changeTrigger
            fieldId = 'ifKitSensorRateMin_' + str(sensor)
            valuesDict[fieldId] = dataRateMin
            fieldId = 'ifKitSensorRateMax_' + str(sensor)
            valuesDict[fieldId] = dataRateMax

        if not wasAlreadyAttached:
            if self.logLevel > 2: indigo.server.log(u"New ifkit closed", type=self.pluginDisplayName)
            interfaceKit.closePhidget()

        if self.logLevel > 2: indigo.server.log(u"ifkit read was successful", type=self.pluginDisplayName)
        if self.logLevel > 2: indigo.server.log(u'readIfKitConfig valuesDict returned: %s' % (valuesDict), type=self.pluginDisplayName, isError=False)
        return valuesDict

    ########################################
    def substituteCustomChar(self, inString, deviceId):
        funcName = inspect.stack()[0][3]
        dbFlg = False

        self.log.log(2, dbFlg, 'Entering %s for device ID: %s' % (funcName, deviceId), self.logName)
        self.log.log(3, dbFlg, '%s: input string:\n%s\ninput string hex\n%s' % (funcName, inString, inString.encode("hex")), self.logName)

        validated = False
        stringParts = inString.split("%%")

        for substr in stringParts:
            if substr[0:2] == "c:":
                custCharNum = int(substr.split(":")[1])
                if custCharNum >= 0 and  custCharNum < 8:
                    try:
                        custChar = self.phThreadDict[deviceId].getCustomChar(custCharNum)
                        validated = True
                        self.log.log(3, dbFlg, '%s: sent:%s, received hex:%s\n' % (funcName, custCharNum, custChar.encode("hex")), self.logName)
                    except Exception, e:
                        validated = False
                        self.errorLog(u'Error %s encountered looking up custom character (%s) in "%s"' % (e, custCharNum, inString))

        if validated:
            p = re.compile("\%%c:([0-9:a-zA-Z]*)%%")
            newString = p.sub(custChar, inString)
        else:
            newString = inString 

        self.log.log(3, dbFlg, '%s: returned string:\n%s\nreturned string hex\n%s' % (funcName, newString, newString.encode("hex")), self.logName)

        return newString

    # This method has been replaced by a identical method provided by the API
    # ########################################
    # def substituteDeviceState(self, inString, validateOnly=False):
    #     funcName = inspect.stack()[0][3]
    #     dbFlg = False
        
    #     # Called for TextLCD message formatting
    #     if self.logLevel > 1:
    #         indigo.server.log(u"Entering substituteDeviceState", type=self.pluginDisplayName)

    #     validated = True
    #     errorStrings = []
    #     stringParts = inString.split("%%")
    #     stateValue = ""
    #     for substr in stringParts:
    #         if substr[0:2] == "s:":
    #             devNameTuple = substr.split(":")
    #             deviceIdString = devNameTuple[1]
    #             stateId = devNameTuple[2]

    #             if deviceIdString.find(" ") < 0:
    #                 try:
    #                     deviceId = int(deviceIdString)
    #                     if stateId in indigo.devices[deviceId].states:
    #                         stateValue = indigo.devices[deviceId].states[stateId]

    #                         # we need to be a bit careful with the type of the state - if it's a boolean we'll insert
    #                         # true or false since that's what the built-in variable compares like, if it's a number
    #                         # we just turn it into a string. Everything else should be a string.
    #                         if stateValue.__class__ == bool:
    #                             if stateValue:
    #                                 stateValue = "true"
    #                             else:
    #                                 stateValue = "false"
    #                             validated = True
    #                         elif (stateValue.__class__ == int) or (stateValue.__class__ == float):
    #                             stateValue = str(stateValue)
    #                             indigo.variable.updateValue(variableId, value=stateValue)
    #                             validated = True
    #                         else:
    #                             self.errorLog(u"State id (%s) isn't available for device model %s - action not configured correctly" % (stateId, indigo.devices[action.deviceId].model))
    #                 except:
    #                     validated = False
    #                     errorStrings.append(u"Substitution format incorrect in string: " + inString)
    #             else:
    #                 validated = False
    #                 errorStrings.append(u"Substitution format incorrect in string: " + inString)
    #     if validateOnly:
    #         if validated:
    #             return (validated,)
    #         else:
    #             return (validated, u"Either a variable ID doesn't exist or there's a substitution format error")
    #     else:
    #         p = re.compile("\%%s:([0-9:a-zA-Z]*)%%")
    #         newString = p.sub(stateValue, inString)
    #         if self.logLevel > 2: indigo.server.log("inString = %s, newString = %s" % (inString, newString), type=self.pluginDisplayName)
    #         return newString

    # def getActionConfigUiXml(self, typeId, devId): # Well use getActionConfigUiValues instead
    #     funcName = inspect.stack()[0][3]
    #     dbFlg = False
        
    #     if self.logLevel > 1: indigo.server.log('Entered: %s' % 'getActionConfigUiXml', type=self.pluginDisplayName)
    #     if self.logLevel > 2: indigo.server.log('with: typeId-%s, devId-%s' % ('getActionConfigUiXml', typeId, devId), type=self.pluginDisplayName)
    #
    #     if typeId == 'phLcdScreenWrite':
    #         # Dynamically set the number of rows available in the write to textlcd action
    #         # <Field defaultValue="1" hidden="false" id="displayLinesNum" type="textfield">
    #         textDisplayDev = indigo.devices[int(devId)]
    #         displayRows = textDisplayDev.pluginProps['phLcdScreenRows']
    #         newXML = 'defaultValue="' + displayRows + '"'
    #
    #         inConfigUIXML = self.actionsTypeDict[typeId][u"ConfigUIRawXml"]
    #         p = re.compile('defaultValue="1"')
    #         outConfigUIXML = p.sub(newXML, inConfigUIXML)
    #         if typeId in self.actionsTypeDict:
    #             if self.logLevel > 2: indigo.server.log('Returned: %s' % outConfigUIXML, type=self.pluginDisplayName, isError=False)
    #             return outConfigUIXML
    #     elif typeId in self.actionsTypeDict:
    #         if self.logLevel > 2: indigo.server.log('Returned: %s' % self.actionsTypeDict[typeId][u"ConfigUIRawXml"], type=self.pluginDisplayName, isError=True)
    #         return self.actionsTypeDict[typeId][u"ConfigUIRawXml"]
    #     else:
    #         self.errorLog('Returned: %s' % 'nothing')
    #         return None

    def getActionConfigUiValues(self, valuesDict, typeId, devId):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        
        if self.logLevel > 1: indigo.server.log('Entered: %s' % 'getActionConfigUiValues', type=self.pluginDisplayName)
        if self.logLevel > 2: indigo.server.log('with: typeId-%s, devId-%s' % ('getActionConfigUiValues', typeId, devId), type=self.pluginDisplayName)

        if typeId == 'phLcdScreenWrite':
            # Dynamically set the number of rows available in the write to textlcd action
            # <Field defaultValue="1" hidden="false" id="displayLinesNum" type="textfield">
            textDisplayDev = indigo.devices[int(devId)]
            displayRows = textDisplayDev.pluginProps['phLcdScreenRows']
            valuesDict['displayLinesNum'] = displayRows

        errorMsgDict = indigo.Dict()
        if self.logLevel > 2: indigo.server.log('getActionConfigUiValues returned: %s' % valuesDict, type=self.pluginDisplayName, isError=True)

        return (valuesDict, errorMsgDict)

    ########################################
    # Indigo Triggers
    #
 
    ########################################
    def triggerStartProcessing(self, trigger):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "Entering %s" % funcName, self.logName)
        # if self.logLevel > 0: indigo.server.log("triggerStartProcessing: triggerId %s for deviceID %s" % (trigger.id, trigger.pluginProps["indigoDevice"]), type=self.pluginDisplayName)
        if self.logLevel > 1: indigo.server.log("triggerStartProcessing: received  trigger:\n%s\n " % (trigger), type=self.pluginDisplayName)

        phDevId = int(trigger.pluginProps["indigoDevice"])
        self.triggerDict[trigger.id] = {'devid' : phDevId, 'event' : trigger.pluginTypeId}

        if self.logLevel > 2: indigo.server.log("triggerStartProcessing: added to triggerDict:\n%s\n " % (self.triggerDict), type=self.pluginDisplayName)
 
    ########################################
    def triggerStopProcessing(self, trigger):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "Entering %s" % funcName, self.logName)
        if self.logLevel > 1: indigo.server.log("triggerStopProcessing: entered for trigger %s(%s)" % (trigger.name, trigger.id), type=self.pluginDisplayName)

        if trigger.id in self.triggerDict:
            if self.logLevel > 1: indigo.server.log("triggerStartProcessing: trgger found", type=self.pluginDisplayName)
            del self.triggerDict[trigger.id]
        if self.logLevel > 1: indigo.server.log("triggerStopProcessing: ended processing for trigger %s(%s)" % (trigger.name, trigger.id), type=self.pluginDisplayName)
 
    ########################################
    def triggerUpdated(self, origDev, newDev):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "Entering %s" % funcName, self.logName)

        self.triggerStopProcessing(origDev)
        self.triggerStartProcessing(newDev)

    ########################################
    def triggerEvent(self, triggerId, devId):
        funcName = inspect.stack()[0][3]
        dbFlg = False
        self.log.log(2, dbFlg, "Entering %s" % funcName, self.logName)

        self.log.log(3, dbFlg, "%sReceived trigger %s for device %s" % (funcName, triggerId, devId), self.logName)
   
        indigo.trigger.execute(triggerId)
        return

    # def didDeviceCommPropertyChange(self, origDev, newDev):
    #     funcName = inspect.stack()[0][3]
    #     dbFlg = False
    #  
    #     # Return True if a plugin related property changed from
    #     # origDev to newDev. Examples would be serial port,
    #     # IP address, etc. By default we assume all properties
    #     # are comm related, but plugin can subclass to provide
    #     # more specific/optimized testing. The return val of
    #     # this method will effect when deviceStartComm() and
    #     # deviceStopComm() are called.
    #     if origDev.pluginProps != newDev.pluginProps:
    #         return True
    #     return False
