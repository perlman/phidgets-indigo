# -*- coding: utf-8 -*-
import traceback

import indigo

from Phidget22.PhidgetException import PhidgetException
from Phidget22.Devices.TemperatureSensor import TemperatureSensor
from Phidget22.ErrorCode import ErrorCode

from phidget import PhidgetBase

import phidget_util

class TemperatureSensorPhidget(PhidgetBase):
    def __init__(self, thermocoupleType, dataInterval, temperatureChangeTrigger, *args, **kwargs):
        super(TemperatureSensorPhidget, self).__init__(phidget=TemperatureSensor(), *args, **kwargs)
        self.thermocoupleType = thermocoupleType
        self.dataInterval = dataInterval
        self.temperatureChangeTrigger = temperatureChangeTrigger

    def addPhidgetHandlers(self):
        self.phidget.setOnErrorHandler(self.onErrorHandler)
        self.phidget.setOnAttachHandler(self.onAttachHandler)
        self.phidget.setOnDetachHandler(self.onDetachHandler)
        self.phidget.setOnTemperatureChangeHandler(self.onTemperatureChangeHandler)

    def onAttachHandler(self, ph):
        super(TemperatureSensorPhidget, self).onAttachHandler(ph)
        try:
            newDataInterval = self.checkValueRange("dataInterval", value=self.dataInterval, minValue=self.phidget.getMinDataInterval(),  maxValue=self.phidget.getMaxDataInterval())
            if newDataInterval is None:
                self.phidget.setDataInterval(PhidgetBase.PHIDGET_DEFAULT_DATA_INTERVAL)
            else:
                self.phidget.setDataInterval(newDataInterval)

            if self.thermocoupleType:
                ph.setThermocoupleType(self.thermocoupleType)

            newTemperatureChangeTrigger = self.checkValueRange(
                fieldname="temperatureChangeTrigger", value=self.temperatureChangeTrigger,
                minValue=self.phidget.getMinTemperatureChangeTrigger(), 
                maxValue=self.phidget.getMaxTemperatureChangeTrigger())
            if newTemperatureChangeTrigger is not None:
                self.phidget.setTemperatureChangeTrigger(newTemperatureChangeTrigger)

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
