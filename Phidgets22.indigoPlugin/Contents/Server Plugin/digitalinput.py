# -*- coding: utf-8 -*-
import traceback
import datetime

import indigo

from Phidget22.Devices.DigitalInput import DigitalInput
from Phidget22.PhidgetException import PhidgetException
from Phidget22.PowerSupply import PowerSupply

from phidget import PhidgetBase

import phidget_util

class DigitalInputPhidget(PhidgetBase):
    def __init__(self, isAlarm, *args, **kwargs):
        super(DigitalInputPhidget, self).__init__(phidget=DigitalInput(), *args, **kwargs)
        self.isAlarm = isAlarm

    def addPhidgetHandlers(self):
        self.phidget.setOnErrorHandler(self.onErrorHandler)
        self.phidget.setOnAttachHandler(self.onAttachHandler)
        self.phidget.setOnDetachHandler(self.onDetachHandler)
        self.phidget.setOnStateChangeHandler(self.onStateChangeHandler)

    def onAttachHandler(self, ph):
        super(DigitalInputPhidget, self).onAttachHandler(ph)

    def updateIndigoStatus(self, state):
        # Common code between onStateChangeHandler & indigo.kSensorAction.RequestStatus
        if state:
            setState = 'on'
            if self.isAlarm:
                stateImage = indigo.kStateImageSel.SensorTripped
            else:
                stateImage = indigo.kStateImageSel.Sensor
        else:
            setState = 'off'
            if self.isAlarm:
                stateImage = indigo.kStateImageSel.SensorOn
            else:
                stateImage = indigo.kStateImageSel.SensorOff

        self.indigoDevice.updateStateOnServer("onOffState", value=setState)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.indigoDevice.updateStateOnServer(key="lastUpdate", value=now)
        self.indigoDevice.updateStateImageOnServer(stateImage)

    def onStateChangeHandler(self, ph, state):
        self.updateIndigoStatus(state)

    def actionControlSensor(self, action):
        if action.sensorAction == indigo.kSensorAction.RequestStatus:
            state = self.phidget.getState()
            self.updateIndigoStatus(state)
        else:
            self.logger.error("Unexpected action: %s" % action.deviceAction)

    def getDeviceStateList(self):
        newStatesList = indigo.List()
        newStatesList.append(self.indigo_plugin.getDeviceStateDictForBoolOnOffType('onOffState', 'onOffState', 'onOffState'))
        newStatesList.append(self.indigo_plugin.getDeviceStateDictForStringType('lastUpdate', 'lastUpdate', 'lastUpdate'))
        
        return newStatesList
    
    def getDeviceDisplayStateId(self):
        return "onOffState"


