# -*- coding: utf-8 -*-
import traceback

import indigo

from Phidget22.Devices.VoltageRatioInput import VoltageRatioInput
from Phidget22.PhidgetException import PhidgetException
from Phidget22.VoltageRatioSensorType import VoltageRatioSensorType

from phidget import PhidgetBase

import phidget_util

class VoltageRatioInputPhidget(PhidgetBase):
    def __init__(self, sensorType, dataInterval, voltageRatioChangeTrigger, sensorValueChangeTrigger, *args, **kwargs):
        super(VoltageRatioInputPhidget, self).__init__(phidget=VoltageRatioInput(), *args, **kwargs)
        self.sensorType = sensorType
        self.dataInterval = dataInterval
        self.voltageRatioChangeTrigger = voltageRatioChangeTrigger
        self.sensorValueChangeTrigger = sensorValueChangeTrigger

    def addPhidgetHandlers(self):
        self.phidget.setOnErrorHandler(self.onErrorHandler)
        self.phidget.setOnAttachHandler(self.onAttachHandler)
        self.phidget.setOnDetachHandler(self.onDetachHandler)
        self.phidget.setOnVoltageRatioChangeHandler(self.setOnVoltageRatioChangeHandler)
        self.phidget.setOnSensorChangeHandler(self.onSensorChangeHandler)

    def onAttachHandler(self, ph):
        super(VoltageRatioInputPhidget, self).onAttachHandler(ph)
        try:
            newDataInterval = self.checkValueRange("dataInterval", value=self.dataInterval, minValue=self.phidget.getMinDataInterval(),  maxValue=self.phidget.getMaxDataInterval())
            if newDataInterval is None:
                self.phidget.setDataInterval(PhidgetBase.PHIDGET_DEFAULT_DATA_INTERVAL)
            else:
                self.phidget.setDataInterval(newDataInterval)

            self.phidget.setSensorType(self.sensorType)

            newVoltageRatioChangeTrigger = self.checkValueRange(
                fieldname="voltageRatioChangeTrigger", value=self.voltageRatioChangeTrigger,
                minValue=self.phidget.getMinVoltageRatioChangeTrigger(), 
                maxValue=self.phidget.getMaxVoltageRatioChangeTrigger())
            if newVoltageRatioChangeTrigger is not None:
                self.phidget.setVoltageRatioChangeTrigger(newVoltageRatioChangeTrigger)

            if self.sensorType != VoltageRatioSensorType.SENSOR_TYPE_VOLTAGERATIO:
                self.phidget.setSensorValueChangeTrigger(self.sensorValueChangeTrigger)

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
