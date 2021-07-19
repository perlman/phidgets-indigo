# -*- coding: utf-8 -*-
import traceback

import indigo

from Phidget22.PhidgetException import PhidgetException
from Phidget22.Devices.TemperatureSensor import TemperatureSensor
from Phidget22.ErrorCode import ErrorCode

from phidget import PhidgetBase

import phidget_util

class TemperatureSensorPhidget(PhidgetBase):
    def __init__(self, thermocoupleType, *args, **kwargs):
        super(TemperatureSensorPhidget, self).__init__(phidget=TemperatureSensor(), *args, **kwargs)
        self.thermocoupleType = thermocoupleType

    def addPhidgetHandlers(self):
        self.phidget.setOnErrorHandler(self.onErrorHandler)
        self.phidget.setOnAttachHandler(self.onAttachHandler)
        self.phidget.setOnTemperatureChangeHandler(self.onTemperatureChangeHandler)

    def onAttachHandler(self, ph):
        try:
            phidget_util.logPhidgetEvent(ph, self.logger.info, "Attach")
            ph.setDataInterval(PhidgetBase.PHIDGET_DATA_INTERVAL)
            if self.thermocoupleType:
                ph.setThermocoupleType(self.thermocoupleType)
        except Exception as e:
            self.logger.error(traceback.format_exc())

    def onTemperatureChangeHandler(self, ph, temperature):
        ph.parent.indigoDevice.updateStateOnServer("temperature", value=temperature, uiValue="%f °C" % temperature)

    def getDeviceStateList(self):
        newStatesList = indigo.List()
        newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType("temperature", "temperature", "temperature"))
        return newStatesList
    
    def getDeviceDisplayStateId(self):
        return "temperature"
