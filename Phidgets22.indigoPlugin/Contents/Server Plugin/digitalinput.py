# -*- coding: utf-8 -*-
import traceback

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
        ph.parent.indigoDevice.updateStateOnServer("onOffState", value=state)

    def actionControlSensor(self, action):
        if action.sensorAction == indigo.kSensorAction.RequestStatus:
            state = self.phidget.getState()
            self.indigoDevice.updateStateOnServer("onOffState", value=state)
        else:
            self.logger.error("Unexpected action: %s" % action.deviceAction) 

    def getDeviceStateList(self):
        newStatesList = indigo.List()
        # onOffState will be in the default state list for a sensor
        return newStatesList
    
    def getDeviceDisplayStateId(self):
        return "onOffState"