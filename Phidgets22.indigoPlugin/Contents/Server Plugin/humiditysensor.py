# -*- coding: utf-8 -*-
import traceback

import indigo

from Phidget22.PhidgetException import PhidgetException
from Phidget22.Devices.HumiditySensor import HumiditySensor
from Phidget22.ErrorCode import ErrorCode

from phidget import PhidgetBase

import phidget_util

class HumiditySensorPhidget(PhidgetBase):
    def __init__(self, *args, **kwargs):
        super(HumiditySensorPhidget, self).__init__(phidget=HumiditySensor(), *args, **kwargs)

        self.dataInterval = int(self.indigoDevice.pluginProps.get("dataInterval", 0))
        self.decimalPlaces = int(self.indigoDevice.pluginProps.get("decimalPlaces", 2))
        self.humidityChangeTrigger = float(self.indigoDevice.pluginProps.get("humidityChangeTrigger", 0))
        # self.dataInterval = dataInterval
        # self.humidityChangeTrigger = humidityChangeTrigger

    def addPhidgetHandlers(self):
        self.phidget.setOnErrorHandler(self.onErrorHandler)
        self.phidget.setOnAttachHandler(self.onAttachHandler)
        self.phidget.setOnDetachHandler(self.onDetachHandler)
        self.phidget.setOnHumidityChangeHandler(self.onHumidityChangeHandler)

    def onAttachHandler(self, ph):
        super(HumiditySensorPhidget, self).onAttachHandler(ph)
        try:
            newDataInterval = self.checkValueRange("dataInterval", value=self.dataInterval, minValue=self.phidget.getMinDataInterval(),  maxValue=self.phidget.getMaxDataInterval())
            if newDataInterval is None:
                self.phidget.setDataInterval(PhidgetBase.PHIDGET_DEFAULT_DATA_INTERVAL)
            else:
                self.phidget.setDataInterval(newDataInterval)

            newHumidityChangeTrigger = self.checkValueRange(
                fieldname="humidityChangeTrigger", value=self.humidityChangeTrigger,
                minValue=self.phidget.getHumidityChangeTrigger(),
                maxValue=self.phidget.getHumidityChangeTrigger())
            if newHumidityChangeTrigger is not None:
                self.phidget.setHumidityChangeTrigger(newHumidityChangeTrigger)

        except Exception as e:
            self.logger.error(traceback.format_exc())

    def onHumidityChangeHandler(self, ph, humidity):
        self.indigoDevice.updateStateOnServer("humidity", value=humidity, decimalPlaces=self.decimalPlaces)

    def getDeviceStateList(self):
        newStatesList = indigo.List()
        newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType("humidity", "humidity", "humidity"))
        return newStatesList

    def getDeviceDisplayStateId(self):
        return "humidity"
