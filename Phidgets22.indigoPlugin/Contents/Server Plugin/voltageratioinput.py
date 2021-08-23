# -*- coding: utf-8 -*-
import string
import traceback

import indigo

from Phidget22.Devices.VoltageRatioInput import VoltageRatioInput
from Phidget22.PhidgetException import PhidgetException
from Phidget22.VoltageRatioSensorType import VoltageRatioSensorType

from phidget import PhidgetBase

import phidget_util

class VoltageRatioInputPhidget(PhidgetBase):
    def __init__(self, sensorType, dataInterval, voltageRatioChangeTrigger, sensorValueChangeTrigger, customState, customFormula, *args, **kwargs):
        super(VoltageRatioInputPhidget, self).__init__(phidget=VoltageRatioInput(), *args, **kwargs)
        self.sensorType = sensorType
        self.dataInterval = dataInterval
        self.voltageRatioChangeTrigger = voltageRatioChangeTrigger
        self.sensorValueChangeTrigger = sensorValueChangeTrigger
        self.customState = customState
        self.customFormula = customFormula
        self.sensorUnit = None          # Last sensor unit
        self.sensorStateName = None     # Clean name for Indigo

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
        self.indigoDevice.updateStateOnServer("voltageRatio", value=voltageRatio, decimalPlaces=self.decimalPlaces)
        if self.sensorType == VoltageRatioSensorType.SENSOR_TYPE_VOLTAGERATIO and self.customState and self.customFormula:
            try:
                formula = lambda x: eval(self.customFormula)
                customValue = formula(float(voltageRatio))
                self.indigoDevice.updateStateOnServer(self.customState, value=customValue, decimalPlaces=self.decimalPlaces)
            except Exception as e:
                self.logger.error('onVoltageRatioChangeHandler: %s received for device: %s' %  (traceback.format_exc(), self.indigoDevice.name))

    def onSensorChangeHandler(self, ph, sensorValue, sensorUnit):
        self.indigoDevice.updateStateOnServer("sensorValue", value=sensorValue, decimalPlaces=self.decimalPlaces)
        if self.sensorUnit is None or self.sensorUnit.name != sensorUnit.name:
            # First update with a new sensorUnit. Trigger an Indigo refresh of getDeviceStateList()
            self.sensorUnit = sensorUnit
            self.sensorStateName = filter(lambda x: x in string.ascii_letters, self.sensorUnit.name)
            self.indigoDevice.stateListOrDisplayStateIdChanged()
        elif self.sensorUnit and self.sensorUnit.name != "none":
            self.indigoDevice.updateStateOnServer(self.sensorStateName, value=sensorValue, decimalPlaces=self.decimalPlaces)

    def getDeviceStateList(self):
        newStatesList = indigo.List()
        newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType("voltageRatio", "voltageRatio", "voltageRatio"))
        if self.sensorType != VoltageRatioSensorType.SENSOR_TYPE_VOLTAGERATIO:
            newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType("sensorValue", "sensorValue", "sensorValue"))
            if self.sensorUnit and self.sensorUnit.name != "none":
                newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType(self.sensorStateName, self.sensorStateName, self.sensorStateName))
        elif self.customState and self.customFormula:
            newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType(self.customState, self.customState, self.customState))
        return newStatesList
    
    def getDeviceDisplayStateId(self):
        if self.sensorType != VoltageRatioSensorType.SENSOR_TYPE_VOLTAGERATIO:
            if self.sensorUnit and self.sensorUnit.name != "none":
                return self.sensorStateName
            else:
                return "sensorValue"
        elif self.customState and self.customFormula:
            return self.customState
        else:
            return "voltageRatio"