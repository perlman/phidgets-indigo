# -*- coding: utf-8 -*-
import traceback

import indigo

from Phidget22.Devices.VoltageRatioInput import VoltageRatioInput
from Phidget22.PhidgetException import PhidgetException
from Phidget22.VoltageRatioSensorType import VoltageRatioSensorType

from phidget import PhidgetBase

import phidget_util

class VoltageRatioInputPhidget(PhidgetBase):
    def __init__(self, sensorType, dataInterval, *args, **kwargs):
        super(VoltageRatioInputPhidget, self).__init__(phidget=VoltageRatioInput(), *args, **kwargs)
        self.sensorType = sensorType
        self.dataInterval = dataInterval

    def addPhidgetHandlers(self):
        self.phidget.setOnErrorHandler(self.onErrorHandler)
        self.phidget.setOnAttachHandler(self.onAttachHandler)
        self.phidget.setOnDetachHandler(self.onDetachHandler)
        self.phidget.setOnVoltageRatioChangeHandler(self.setOnVoltageRatioChangeHandler)
        self.phidget.setOnSensorChangeHandler(self.onSensorChangeHandler)

    def onAttachHandler(self, ph):
        super(VoltageRatioInputPhidget, self).onAttachHandler(ph)
        try:
            self.setDataInterval(self.dataInterval)
            ph.setSensorType(self.sensorType)
        except Exception as e:
            self.logger.error(traceback.format_exc())

    def setOnVoltageRatioChangeHandler(self, ph, voltageRatio):
        self.indigoDevice.updateStateOnServer("voltageRatio", value=voltageRatio, uiValue="%.2f V/V" % voltageRatio)

    def onSensorChangeHandler(self, ph, sensorValue, sensorUnit):
        self.indigoDevice.updateStateOnServer("sensorValue", value=sensorValue, uiValue="%.2f %s" % (sensorValue, sensorUnit.symbol))

    def getDeviceStateList(self):
        newStatesList = indigo.List()
        newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType("voltageRatio", "voltageRatio", "voltageRatio"))
        if self.sensorType != VoltageRatioSensorType.SENSOR_TYPE_VOLTAGERATIO:
            newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType("sensorValue", "sensorValue", "sensorValue"))
        return newStatesList
    
    def getDeviceDisplayStateId(self):
        if self.sensorType != VoltageRatioSensorType.SENSOR_TYPE_VOLTAGERATIO:
            return "sensorValue"
        else:
            return "voltageRatio"
