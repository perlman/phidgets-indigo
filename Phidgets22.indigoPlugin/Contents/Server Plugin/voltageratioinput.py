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
        self.voltageRatioSensorType = str(self.indigoDevice.pluginProps.get("voltageRatioSensorType", 0))
        self.customFormula = self.indigoDevice.pluginProps.get("customFormula", None)
        self.customStateName = str(self.indigoDevice.pluginProps.get("customState", ""))
        self.sensorStateName = str(self.indigoDevice.pluginProps.get("sensorUnit", None))
        if not self.customStateName:  # for some reason a cleared field still has a value and the default is not used.
            self.customStateName = 'custom'
        self.sensorUnit = None          # Last sensor unit
        # self.sensorStateName = None     # Clean name for Indigo

        if self.sensorStateName:
            self.indigoDevice.stateListOrDisplayStateIdChanged()

    def addPhidgetHandlers(self):
        self.phidget.setOnErrorHandler(self.onErrorHandler)
        self.phidget.setOnAttachHandler(self.onAttachHandler)
        self.phidget.setOnDetachHandler(self.onDetachHandler)
        self.phidget.setOnVoltageRatioChangeHandler(self.onVoltageRatioChangeHandler)
        self.phidget.setOnSensorChangeHandler(self.onSensorChangeHandler)


    def onAttachHandler(self, ph):
        super(VoltageRatioInputPhidget, self).onAttachHandler(ph)
        try:
            # self.phidget.setDataInterval(self.dataInterval)
            # self.phidget.setSensorType(self.sensorType)
            self.phidget.setVoltageRatioChangeTrigger(self.voltageRatioChangeTrigger)
            self.phidget.setSensorValueChangeTrigger(self.sensorValueChangeTrigger)

        except Exception as e:
            self.logger.error('Indigo device: %s: %s' %  (self.indigoDevice.name, traceback.format_exc()))


    def onVoltageRatioChangeHandler(self, ph, voltageRatio):
        self.indigoDevice.updateStateOnServer("voltageRatio", value=voltageRatio, decimalPlaces=3) #self.decimalPlaces)

        if self.voltageRatioSensorType == '0':  # a generic voltage ratio device
            if self.customFormula:
                try:
                    formula = lambda x: eval(self.customFormula)
                    customValue = formula(float(voltageRatio))
                except Exception as e:
                    self.logger.error('%s reveived for device: %s' %  (traceback.format_exc(), self.indigoDevice.name))
                # self.logger.debug('for %s. Received: %s, Calculated: %s for name' %  (self.indigoDevice.name, voltageRatio, customValue, self.customStateName))
                self.indigoDevice.updateStateOnServer(self.customStateName, value=customValue, decimalPlaces=self.decimalPlaces)


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


        if self.sensorStateName != None and self.sensorStateName not in self.indigoDevice.states:
            newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType(self.sensorStateName, self.sensorStateName, self.sensorStateName))
            newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType('sensorValue', 'sensorValue', 'sensorValue'))
        elif self.sensorType != VoltageRatioSensorType.SENSOR_TYPE_VOLTAGERATIO:
            newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType("sensorValue", "sensorValue", "sensorValue"))
            if self.sensorUnit and self.sensorUnit.name != "none":
                newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType(self.sensorStateName, self.sensorStateName, self.sensorStateName))

        if self.customFormula:
            newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType(self.customStateName, self.customStateName, self.customStateName))
        return newStatesList

    def getDeviceDisplayStateId(self):
        if self.sensorType != VoltageRatioSensorType.SENSOR_TYPE_VOLTAGERATIO:
            if self.sensorUnit and self.sensorUnit.name != "none":
                return self.sensorStateName
            else:
                return "sensorValue"
        elif self.customFormula:
            return self.customStateName
        else:
            return "voltageRatio"