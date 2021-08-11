# -*- coding: utf-8 -*-
import string
import traceback
import indigo

from Phidget22.Devices.VoltageRatioInput import VoltageRatioInput
from Phidget22.PhidgetException import PhidgetException
from Phidget22.VoltageRatioSensorType import VoltageRatioSensorType
import phidget_util
from phidget import PhidgetBase


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
        self.customStateName = str(self.indigoDevice.pluginProps.get("customState", None))
        self.sensorStateName = str(self.indigoDevice.pluginProps.get("sensorUnit", None))
        if self.customStateName == '':  # for some reason a cleared field still has a value and the default is not used.
            self.customStateName = None
        self.sensorUnit = None          # Last sensor unit

        # Create the appropriate state for this device
        if self.sensorStateName:
            self.indigoDevice.stateListOrDisplayStateIdChanged()
            self.logger.debug('__init__: device: %s found state name %s' %  (self.indigoDevice.name, self.sensorStateName))


    def addPhidgetHandlers(self):
        self.phidget.setOnErrorHandler(self.onErrorHandler)
        self.phidget.setOnAttachHandler(self.onAttachHandler)
        self.phidget.setOnDetachHandler(self.onDetachHandler)
        self.phidget.setOnVoltageRatioChangeHandler(self.onVoltageRatioChangeHandler)
        self.phidget.setOnSensorChangeHandler(self.onSensorChangeHandler)


    def onAttachHandler(self, ph):
        super(VoltageRatioInputPhidget, self).onAttachHandler(ph)
        self.logger.debug('onAttachHandler: device: %s, sensorType: %s' %  (self.indigoDevice.name, self.sensorType))

        try:
            self.phidget.openWaitForAttachment(1000)
            self.phidget.setSensorType(self.sensorType)
            self.phidget.setVoltageRatioChangeTrigger(self.voltageRatioChangeTrigger)
            self.phidget.setSensorValueChangeTrigger(self.sensorValueChangeTrigger)
        except Exception as e:
            self.logger.error('onAttachHandler: Indigo device: %s failed to attach' %  (self.indigoDevice.name))
            self.logger.error('onAttachHandler: Indigo device: %s: %s' %  (self.indigoDevice.name, traceback.format_exc()))


    def onVoltageRatioChangeHandler(self, ph, voltageRatio):
        self.logger.debug('voltageRatioChangeHandler: dev %s. voltageRatio: %s' % (self.indigoDevice.name, voltageRatio))

        self.indigoDevice.updateStateOnServer("voltageRatio", value=voltageRatio, decimalPlaces=3) #self.decimalPlaces)

        if self.voltageRatioSensorType == '0':  # a generic voltage ratio device
            if self.customFormula:
                try:
                    formula = lambda x: eval(self.customFormula)
                    customValue = formula(float(voltageRatio))
                except Exception as e:
                    self.logger.error('onVoltageChangeHandler: %s reveived for device: %s' %  (traceback.format_exc(), self.indigoDevice.name))
                # self.logger.error('for %s. Received: %s, Calculated: %s for name' %  (self.indigoDevice.name, voltageRatio, customValue, self.customStateName))

                self.indigoDevice.updateStateOnServer(self.customStateName, value=customValue, decimalPlaces=self.decimalPlaces)


    def onSensorChangeHandler(self, ph, sensorValue, sensorUnit):
        self.logger.debug('sensorChangeHandler: dev %s. value: %s, State name: %s' % (self.indigoDevice.name, str(sensorValue), str(sensorUnit)))

        try:
            sensorState = str(sensorUnit.name).replace(' ', '')
        except:
            sensorState = sensorUnit  # We were probably called from the onAttachHandler

        if sensorState in self.indigoDevice.states:
            self.indigoDevice.updateStateOnServer(sensorState, value=sensorValue, decimalPlaces=self.decimalPlaces)
        else:
            self.indigoDevice.stateListOrDisplayStateIdChanged()
            self.logger.warning('onSensorChangeHandler: unrecognizewd state \"%s\" received for device %s\n>>> Found: %s' % (sensorState, self.indigoDevice.name, self.indigoDevice.states))

        if 'sensorValue' in self.indigoDevice.states:
            self.indigoDevice.updateStateOnServer('sensorValue', value=sensorValue, decimalPlaces=self.decimalPlaces)


    def getDeviceStateList(self):
        self.logger.debug('getDeviceStateList: called for %s with state name %s' %  (self.indigoDevice.name, self.sensorStateName))
        newStatesList = indigo.List()
        newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType("voltageRatio", "voltageRatio", "voltageRatio"))

        if self.customFormula:
            newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType(self.customStateName, self.customStateName, self.customStateName))
        if self.sensorStateName != None and self.sensorStateName : # not in self.indigoDevice.states:
            newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType(self.sensorStateName, self.sensorStateName, self.sensorStateName))
            newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType('sensorValue', 'sensorValue', 'sensorValue'))
        elif self.sensorType != VoltageRatioSensorType.SENSOR_TYPE_VOLTAGERATIO:
            newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType("sensorValue", "sensorValue", "sensorValue"))
            if self.sensorUnit and self.sensorUnit.name != "none":
                newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType(self.sensorStateName, self.sensorStateName, self.sensorStateName))

        self.logger.debug('getDeviceStateList: %s returned %s' %  (self.indigoDevice.name, str(newStatesList)))
        return newStatesList


    def getDeviceDisplayStateId(self):
        if self.customFormula:
            return self.customStateName
        elif self.sensorStateName:
            return self.sensorStateName
        elif self.sensorType != VoltageRatioSensorType.SENSOR_TYPE_VOLTAGERATIO:
            if self.sensorUnit and self.sensorUnit.name != "none":
                return self.sensorStateName
            else:
                return "sensorValue"
        else:
            return "voltageRatio"