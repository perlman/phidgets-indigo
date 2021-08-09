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
    def __init__(self, *args, **kwargs):
        super(DigitalInputPhidget, self).__init__(phidget=DigitalInput(), *args, **kwargs)

    def addPhidgetHandlers(self):
        self.phidget.setOnErrorHandler(self.onErrorHandler)
        self.phidget.setOnAttachHandler(self.onAttachHandler)
        self.phidget.setOnDetachHandler(self.onDetachHandler)
        self.phidget.setOnStateChangeHandler(self.onStateChangeHandler)

    def onAttachHandler(self, ph):
        super(DigitalInputPhidget, self).onAttachHandler(ph)

    def onStateChangeHandler(self, ph, state):
        isAlarm = bool(self.indigoDevice.pluginProps.get("isAlarm", False))
        setState = 'off'
        if isAlarm:
            stateImage = indigo.kStateImageSel.SensorOn
        else:
            stateImage = indigo.kStateImageSel.SensorOff

        if state:
            setState = 'on'
            if isAlarm:
                stateImage = indigo.kStateImageSel.SensorTripped
            else:
                stateImage = indigo.kStateImageSel.SensorOn
    
        self.indigoDevice.updateStateOnServer("onOffState", value=setState)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.indigoDevice.updateStateOnServer(key="lastUpdate", value=now)
        self.indigoDevice.updateStateImageOnServer(stateImage)

    def actionControlSensor(self, action):
        isAlarm = bool(self.indigoDevice.pluginProps.get("isAlarm", False))
        if action.sensorAction == indigo.kSensorAction.RequestStatus:
            setState = 'off'
            if isAlarm:
                stateImage = indigo.kStateImageSel.SensorOn
            else:
                stateImage = indigo.kStateImageSel.SensorOff

            if state:
                setState = 'on'
                if isAlarm:
                    stateImage = indigo.kStateImageSel.SensorTripped
                else:
                    stateImage = indigo.kStateImageSel.SensorOn
            self.indigoDevice.updateStateOnServer("onOffState", value=state)
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.logger.error("Unexpected action: %s" % now) 
            self.indigoDevice.updateStateOnServer("lastUpdate", value=now)
            self.indigoDevice.updateStateImageOnServer(stateImage)
        else:
            self.logger.error("Unexpected action: %s" % action.deviceAction) 

    def getDeviceStateList(self):
        newStatesList = indigo.List()
        newStatesList.append(self.indigo_plugin.getDeviceStateDictForBoolOnOffType('onOffState', 'onOffState', 'onOffState'))
        newStatesList.append(self.indigo_plugin.getDeviceStateDictForStringType('lastUpdate', 'lastUpdate', 'lastUpdate'))
        
        return newStatesList
    
    def getDeviceDisplayStateId(self):
        return "onOffState"