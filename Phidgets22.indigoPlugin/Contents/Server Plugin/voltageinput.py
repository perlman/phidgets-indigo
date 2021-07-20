# -*- coding: utf-8 -*-
import traceback

import indigo

from Phidget22.Devices.VoltageInput import VoltageInput
from Phidget22.PhidgetException import PhidgetException
from Phidget22.VoltageSensorType import VoltageSensorType

from phidget import PhidgetBase

import phidget_util

class VoltageInputPhidget(PhidgetBase):
    def __init__(self, sensorType, *args, **kwargs):
        super(VoltageInputPhidget, self).__init__(phidget=VoltageInput(), *args, **kwargs)
        self.sensorType = sensorType

    def addPhidgetHandlers(self):
        self.phidget.setOnErrorHandler(self.onErrorHandler)
        self.phidget.setOnAttachHandler(self.onAttachHandler)
        self.phidget.setOnVoltageChangeHandler(self.onVoltageChangeHandler)
        self.phidget.setOnSensorChangeHandler(self.onSensorChangeHandler)

    def onAttachHandler(self, ph):
        super(VoltageInputPhidget, self).onAttachHandler(self)
        try:
            ph.setDataInterval(PhidgetBase.PHIDGET_DATA_INTERVAL)
            ph.setSensorType(self.sensorType)
        except Exception as e:
            self.logger.error(traceback.format_exc())

    def onVoltageChangeHandler(self, ph, voltage):
        ph.parent.indigoDevice.updateStateOnServer("voltage", value=voltage, uiValue="%f V" % voltage)

    def onSensorChangeHandler(self, ph, sensorValue, sensorUnit):
        ph.parent.indigoDevice.updateStateOnServer("sensorValue", value=sensorValue, uiValue="%f %s" % (sensorValue, sensorUnit.symbol))

    def getDeviceStateList(self):
        newStatesList = indigo.List()
        newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType("voltage", "voltage", "voltage"))
        if self.sensorType != VoltageSensorType.SENSOR_TYPE_VOLTAGE:
            newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType("sensorValue", "sensorValue", "sensorValue"))
        return newStatesList
    
    def getDeviceDisplayStateId(self):
        if self.sensorType != VoltageSensorType.SENSOR_TYPE_VOLTAGE:
            return "sensorValue"
        else:
            return "voltage"
