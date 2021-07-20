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
        ph.parent.indigoDevice.updateStateOnServer("sensorState", value=state)

    def getDeviceStateList(self):
        newStatesList = indigo.List()
        newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType("sensorState", "sensorState", "sensorState"))
        return newStatesList
    
    def getDeviceDisplayStateId(self):
        return "sensorState"