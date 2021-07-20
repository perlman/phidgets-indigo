# -*- coding: utf-8 -*-
import traceback

import indigo

from Phidget22.Devices.VoltageRatioInput import VoltageRatioInput
from Phidget22.PhidgetException import PhidgetException
from Phidget22.VoltageRatioSensorType import VoltageRatioSensorType

from phidget import PhidgetBase

import phidget_util

class VoltageRatioInputPhidget(PhidgetBase):
    def __init__(self, sensorType, *args, **kwargs):
        super(VoltageRatioInputPhidget, self).__init__(phidget=VoltageRatioInput(), *args, **kwargs)
        self.sensorType = sensorType

    def addPhidgetHandlers(self):
        self.phidget.setOnErrorHandler(self.onErrorHandler)
        self.phidget.setOnAttachHandler(self.onAttachHandler)
        self.phidget.setOnDetachHandler(self.onDetachHandler)
        self.phidget.setOnVoltageRatioChangeHandler(self.setOnVoltageRatioChangeHandler)
        self.phidget.setOnSensorChangeHandler(self.onSensorChangeHandler)

    def onAttachHandler(self, ph):
        super(VoltageRatioInputPhidget, self).onAttachHandler(ph)
        try:
            ph.setDataInterval(PhidgetBase.PHIDGET_DATA_INTERVAL)
            ph.setSensorType(self.sensorType)
        except Exception as e:
            self.logger.error(traceback.format_exc())

    def setOnVoltageRatioChangeHandler(self, ph, voltageRatio):
        ph.parent.indigoDevice.updateStateOnServer("voltageRatio", value=voltageRatio, uiValue="%.2f V/V" % voltageRatio)

    def onSensorChangeHandler(self, ph, sensorValue, sensorUnit):
        ph.parent.indigoDevice.updateStateOnServer("sensorValue", value=sensorValue, uiValue="%.2f %s" % (sensorValue, sensorUnit.symbol))

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
