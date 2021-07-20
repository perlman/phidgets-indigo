# -*- coding: utf-8 -*-
import traceback

import indigo

from Phidget22.PhidgetException import PhidgetException
from Phidget22.Devices.TemperatureSensor import TemperatureSensor
from Phidget22.ErrorCode import ErrorCode

from phidget import PhidgetBase

import phidget_util

class TemperatureSensorPhidget(PhidgetBase):
    def __init__(self, thermocoupleType, dataInterval, *args, **kwargs):
        super(TemperatureSensorPhidget, self).__init__(phidget=TemperatureSensor(), *args, **kwargs)
        self.thermocoupleType = thermocoupleType
        self.dataInterval = dataInterval

    def addPhidgetHandlers(self):
        self.phidget.setOnErrorHandler(self.onErrorHandler)
        self.phidget.setOnAttachHandler(self.onAttachHandler)
        self.phidget.setOnDetachHandler(self.onDetachHandler)
        self.phidget.setOnTemperatureChangeHandler(self.onTemperatureChangeHandler)

    def onAttachHandler(self, ph):
        super(TemperatureSensorPhidget, self).onAttachHandler(ph)
        try:
            self.setDataInterval(self.dataInterval)
            if self.thermocoupleType:
                ph.setThermocoupleType(self.thermocoupleType)
        except Exception as e:
            self.logger.error(traceback.format_exc())

    def onTemperatureChangeHandler(self, ph, temperature):
        self.indigoDevice.updateStateOnServer("temperature", value=temperature, uiValue="%0.2f °C" % temperature)

    def getDeviceStateList(self):
        newStatesList = indigo.List()
        newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType("temperature", "temperature", "temperature"))
        return newStatesList
    
    def getDeviceDisplayStateId(self):
        return "temperature"
