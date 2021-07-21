# -*- coding: utf-8 -*-
import traceback

import indigo

from Phidget22.Devices.VoltageInput import VoltageInput
from Phidget22.PhidgetException import PhidgetException
from Phidget22.VoltageSensorType import VoltageSensorType

from phidget import PhidgetBase

import phidget_util


# TODO: How do we figure out which VoltageInput devices support sensors and which do not?
#       We need to add the sensor features for certain devices (e.g. interface kits)
#       but not others (e.g. temperature sensor used in voltage mode.)

class VoltageInputPhidget(PhidgetBase):
    def __init__(self, sensorType, dataInterval, voltageChangeTrigger, sensorValueChangeTrigger, *args, **kwargs):
        super(VoltageInputPhidget, self).__init__(phidget=VoltageInput(), *args, **kwargs)
        self.sensorType = sensorType
        self.dataInterval = dataInterval
        self.voltageChangeTrigger = voltageChangeTrigger
        self.sensorValueChangeTrigger = sensorValueChangeTrigger

    def addPhidgetHandlers(self):
        self.phidget.setOnErrorHandler(self.onErrorHandler)
        self.phidget.setOnAttachHandler(self.onAttachHandler)
        self.phidget.setOnDetachHandler(self.onDetachHandler)
        self.phidget.setOnVoltageChangeHandler(self.onVoltageChangeHandler)
        self.phidget.setOnSensorChangeHandler(self.onSensorChangeHandler)

    def onAttachHandler(self, ph):
        super(VoltageInputPhidget, self).onAttachHandler(ph)
        try:
            newDataInterval = self.checkValueRange("dataInterval", value=self.dataInterval, minValue=self.phidget.getMinDataInterval(),  maxValue=self.phidget.getMaxDataInterval())
            if newDataInterval is None:
                self.phidget.setDataInterval(PhidgetBase.PHIDGET_DEFAULT_DATA_INTERVAL)
            else:
                self.phidget.setDataInterval(newDataInterval)

            self.phidget.setSensorType(self.sensorType)

            newVoltageChangeTrigger = self.checkValueRange(
                fieldname="voltageChangeTrigger", value=self.voltageChangeTrigger,
                minValue=self.phidget.getMinVoltageChangeTrigger(), 
                maxValue=self.phidget.getMaxVoltageChangeTrigger())
            if newVoltageChangeTrigger is not None:
                self.phidget.setVoltageChangeTrigger(newVoltageChangeTrigger)

            if self.sensorType != VoltageSensorType.SENSOR_TYPE_VOLTAGE:
                self.phidget.setSensorValueChangeTrigger(self.sensorValueChangeTrigger)

        except Exception as e:
            self.logger.error(traceback.format_exc())

    def onVoltageChangeHandler(self, ph, voltage):
        self.indigoDevice.updateStateOnServer("voltage", value=voltage, uiValue="%.2f V" % voltage)

    def onSensorChangeHandler(self, ph, sensorValue, sensorUnit):
        self.indigoDevice.updateStateOnServer("sensorValue", value=sensorValue, uiValue="%.2f %s" % (sensorValue, sensorUnit.symbol))

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
