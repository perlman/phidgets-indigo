# -*- coding: utf-8 -*-
import string
import traceback
import indigo

from Phidget22.Devices.VoltageInput import VoltageInput
from Phidget22.PhidgetException import PhidgetException
from Phidget22.VoltageSensorType import VoltageSensorType
import phidget_util
from phidget import PhidgetBase


# TODO: How do we figure out which VoltageInput devices support sensors and which do not?
#       We need to add the sensor features for certain devices (e.g. interface kits)
#       but not others (e.g. temperature sensor used in voltage mode.)

class VoltageInputPhidget(PhidgetBase):
    def __init__(self, sensorType, dataInterval, voltageChangeTrigger, sensorValueChangeTrigger, *args, **kwargs):
        super(VoltageInputPhidget, self).__init__(phidget=VoltageInput(), *args, **kwargs)

        self.sensorType = sensorType # int(self.indigoDevice.pluginProps.get("voltageRatioSensorType", 0))
        self.dataInterval = dataInterval # int(self.indigoDevice.pluginProps.get("dataInterval", 0))
        self.voltageChangeTrigger = voltageChangeTrigger
        self.sensorValueChangeTrigger = sensorValueChangeTrigger
        self.decimalPlaces = int(self.indigoDevice.pluginProps.get("decimalPlaces", 2))
        self.voltageSensorType = str(self.indigoDevice.pluginProps.get("voltageSensorType", 0))
        self.customFormula = self.indigoDevice.pluginProps.get("customFormula", None)
        self.customStateName = str(self.indigoDevice.pluginProps.get("customState", ""))
        self.sensorStateName = str(self.indigoDevice.pluginProps.get("sensorUnit", None))
        if not self.customStateName:  # for some reason a cleared field still has a value and the default is not used.
            self.customStateName = 'custom'
        self.sensorUnit = None          # Last sensor unit

        # Create the appropriate state for this device
        if self.sensorStateName:
            self.indigoDevice.stateListOrDisplayStateIdChanged()
            self.logger.debug('__init__: device: %s found state name %s' %  (self.indigoDevice.name, self.sensorStateName))


    def addPhidgetHandlers(self):
        self.phidget.setOnErrorHandler(self.onErrorHandler)
        self.phidget.setOnAttachHandler(self.onAttachHandler)
        self.phidget.setOnDetachHandler(self.onDetachHandler)
        self.phidget.setOnVoltageChangeHandler(self.onVoltageChangeHandler)
        self.phidget.setOnSensorChangeHandler(self.onSensorChangeHandler)

    def onAttachHandler(self, ph):
        super(VoltageInputPhidget, self).onAttachHandler(ph)
        self.logger.debug('onAttachHandler: device: %s, sensorType: %s' %  (self.indigoDevice.name, self.sensorType))

        try:
            self.phidget.openWaitForAttachment(1000)
            self.phidget.setSensorType(self.sensorType)
            self.phidget.setVoltageChangeTrigger(self.voltageChangeTrigger)
            self.phidget.setSensorValueChangeTrigger(self.sensorValueChangeTrigger)

            # newDataInterval = self.checkValueRange("dataInterval", value=self.dataInterval, minValue=self.phidget.getMinDataInterval(),  maxValue=self.phidget.getMaxDataInterval())
            # if newDataInterval is None:
            #     self.phidget.setDataInterval(PhidgetBase.PHIDGET_DEFAULT_DATA_INTERVAL)
            # else:
            #     self.phidget.setDataInterval(newDataInterval)

            # self.phidget.setSensorType(self.sensorType)

            # newVoltageChangeTrigger = self.checkValueRange(
            #     fieldname="voltageChangeTrigger", value=self.voltageChangeTrigger,
            #     minValue=self.phidget.getMinVoltageChangeTrigger(),
            #     maxValue=self.phidget.getMaxVoltageChangeTrigger())
            # if newVoltageChangeTrigger is not None:
            #     self.phidget.setVoltageChangeTrigger(newVoltageChangeTrigger)

            # if self.sensorType != VoltageSensorType.SENSOR_TYPE_VOLTAGE:
            #     self.phidget.setSensorValueChangeTrigger(self.sensorValueChangeTrigger)

        except Exception as e:
            self.logger.error('onAttachHandler: Indigo device: %s failed to attach' %  (self.indigoDevice.name))
            self.logger.error('onAttachHandler: Indigo device: %s: %s' %  (self.indigoDevice.name, traceback.format_exc()))


    def onVoltageChangeHandler(self, ph, voltage):
        self.logger.debug('voltageRatioChangeHandler: dev %s. voltageRatio: %s' % (self.indigoDevice.name, voltageRatio))

        self.indigoDevice.updateStateOnServer("voltage", value=voltage, decimalPlaces=3) #self.decimalPlaces)

        if self.voltageSensorType == '0':  # a generic voltage ratio device
            if self.customFormula:
                try:
                    formula = lambda x: eval(self.customFormula)
                    customValue = formula(float(voltage))
                except Exception as e:
                    self.logger.error('onVoltageChangeHandler: %s reveived for device: %s' %  (traceback.format_exc(), self.indigoDevice.name))
                # self.logger.debug('for %s. Received: %s, Calculated: %s for name %s' %  (self.indigoDevice.name, voltage, customValue, self.customStateName))

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

        # self.indigoDevice.updateStateOnServer("sensorValue", value=sensorValue, decimalPlaces=self.decimalPlaces)


        # try:
        #     if sensorState not in self.indigoDevice.states:
        #         self.indigoDevice.stateListOrDisplayStateIdChanged()
        #     self.indigoDevice.updateStateOnServer(sensorState, value=sensorValue, decimalPlaces=self.decimalPlaces)
        # except Exception as e:
        #     self.logger.error('%s reveived for device: %s, state name: %s' %  (traceback.format_exc(), self.indigoDevice.name, sensorState))
        # self.indigoDevice.updateStateOnServer("sensorValue", value=sensorValue, decimalPlaces=self.decimalPlaces)
        # if self.sensorUnit is None or self.sensorUnit.name != sensorUnit.name:
        #     # First update with a new sensorUnit. Trigger an Indigo refresh of getDeviceStateList()
        #     self.sensorUnit = sensorUnit
        #     self.sensorStateName = filter(lambda x: x in string.ascii_letters, self.sensorUnit.name)
        #     self.indigoDevice.stateListOrDisplayStateIdChanged()
        # elif self.sensorUnit and self.sensorUnit.name != "none":
        #     self.indigoDevice.updateStateOnServer(self.sensorStateName, value=sensorValue, decimalPlaces=self.decimalPlaces)

    def getDeviceStateList(self):
        self.logger.debug('getDeviceStateList: called for %s with state name %s' %  (self.indigoDevice.name, self.sensorStateName))
        newStatesList = indigo.List()
        newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType("voltage", "voltage", "voltage"))

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
        elif self.sensorType != VoltageSensorType.SENSOR_TYPE_VOLTAGE:
            if self.sensorUnit and self.sensorUnit.name != "none":
                return self.sensorStateName
            else:
                return "sensorValue"
        else:
            return "voltage"

        # if self.sensorType != VoltageSensorType.SENSOR_TYPE_VOLTAGE:
        #     if self.sensorUnit and self.sensorUnit.name != "none":
        #         return self.sensorStateName
        #     else:
        #         return "sensorValue"
        # elif self.customFormula:
        #     return self.customStateName
        # else:
        #     return "voltage"
