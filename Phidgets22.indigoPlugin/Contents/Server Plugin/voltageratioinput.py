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
    def __init__(self, *args, **kwargs):
        super(VoltageRatioInputPhidget, self).__init__(phidget=VoltageRatioInput(), *args, **kwargs)
 
        self.sensorType = int(self.indigoDevice.pluginProps.get("voltageRatioSensorType", 0))   
        self.dataInterval = int(self.indigoDevice.pluginProps.get("dataInterval", 0))
        self.voltageRatioChangeTrigger = float(self.indigoDevice.pluginProps.get("voltageRatioChangeTrigger", 0))
        self.sensorValueChangeTrigger = float(self.indigoDevice.pluginProps.get("sensorValueChangeTrigger", 0))
        self.decimalPlaces = int(self.indigoDevice.pluginProps.get("decimalPlaces", 2))
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
            self.phidget.setDataInterval(self.dataInterval)
            self.phidget.setSensorType(self.sensorType)
            self.phidget.setVoltageRatioChangeTrigger(self.voltageRatioChangeTrigger)
            self.phidget.setSensorValueChangeTrigger(self.sensorValueChangeTrigger)

        except Exception as e:
            self.logger.error('%s reveived for device: %s' %  (traceback.format_exc(), self.indigoDevice.name))
        

    def setOnVoltageRatioChangeHandler(self, ph, voltageRatio):
        self.indigoDevice.updateStateOnServer("voltageRatio", value=voltageRatio, decimalPlaces=self.decimalPlaces)

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
        return newStatesList
    
    def getDeviceDisplayStateId(self):
        if self.sensorType != VoltageRatioSensorType.SENSOR_TYPE_VOLTAGERATIO:
            if self.sensorUnit and self.sensorUnit.name != "none":
                return self.sensorStateName
            else:
                return "sensorValue"
        else:
            return "voltageRatio"