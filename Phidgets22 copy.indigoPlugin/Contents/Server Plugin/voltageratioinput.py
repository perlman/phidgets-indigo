# -*- coding: utf-8 -*-
import string
import traceback
# from time import sleep

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
        self.customStateName = str(self.indigoDevice.pluginProps.get("customState", None))
        self.sensorStateName = str(self.indigoDevice.pluginProps.get("sensorUnit", None))
        if self.customStateName == '':  # for some reason a cleared field still has a value and the default is not used.
            self.customStateName = None
        self.sensorUnit = None          # Last sensor unit

        # Create the appropriate state for this device
        if self.sensorStateName:
            self.indigoDevice.stateListOrDisplayStateIdChanged()
            self.logger.debug('__init__: device: %s found state name %s' %  (self.indigoDevice.name, self.sensorStateName))

        # Now wait until the phidget is attached
        try:
            self.phidget.openWaitForAttachment(5000)
            # self.phidget.setDataInterval(self.dataInterval)
            self.phidget.setSensorType(self.sensorType)
            self.phidget.setVoltageRatioChangeTrigger(self.voltageRatioChangeTrigger)
            self.phidget.setSensorValueChangeTrigger(self.sensorValueChangeTrigger)

            # Get a current measurement from the device
            try:
                sensorValue = self.phidget.getSensorValue()
                # self.logger.error('-->> Attached %s: updated: %s, x with: %s' % (self.indigoDevice.name, self.sensorStateName, int(sensorValue)))
                if self.customStateName is not None:
                    self.logger.debug('-> Attached %s: custom formula updated: %s, with: %s' % (self.indigoDevice.name, self.customStateName, sensorValue))
                    self.onSensorChangeHandler(None, self.phidget.getSensorValue(), self.customStateName)
                elif self.sensorStateName is not None:
                    self.logger.debug('-> Attached %s: updated: %s, with: %s' % (self.indigoDevice.name, self.sensorStateName, sensorValue))
                    self.onSensorChangeHandler(None, self.phidget.getSensorValue(), self.sensorStateName)
                else:
                    self.logger.debug('-> Attached %s: unable to update: %s, with: %s' % (self.indigoDevice.name, self.customStateName, sensorValue))
            except:
                self.logger.warning('Attached %s: unable to update sensor reading' % (self.indigoDevice.name))
                # self.logger.error('Indigo device: %s: %s' %  (self.indigoDevice.name, traceback.format_exc()))
        except Exception as e:
            self.logger.error('Indigo device: %s failed to attach' %  (self.indigoDevice.name))
            # self.logger.error('Indigo device: %s: %s' %  (self.indigoDevice.name, traceback.format_exc()))

    def addPhidgetHandlers(self):
        self.phidget.setOnErrorHandler(self.onErrorHandler)
        self.phidget.setOnAttachHandler(self.onAttachHandler)
        self.phidget.setOnDetachHandler(self.onDetachHandler)
        self.phidget.setOnVoltageRatioChangeHandler(self.onVoltageRatioChangeHandler)
        self.phidget.setOnSensorChangeHandler(self.onSensorChangeHandler)


    def onAttachHandler(self, ph):
        super(VoltageRatioInputPhidget, self).onAttachHandler(ph)
        self.logger.error('onAttachHandler: device: %s, sensorType: %s' %  (self.indigoDevice.name, self.sensorType))


    def onVoltageRatioChangeHandler(self, ph, voltageRatio):
        self.logger.debug('voltageRatioChangeHandler: dev %s. voltageRatio: %s' % (self.indigoDevice.name, voltageRatio))

        self.indigoDevice.updateStateOnServer("voltageRatio", value=voltageRatio, decimalPlaces=3) #self.decimalPlaces)

        if self.voltageRatioSensorType == '0':  # a generic voltage ratio device
            if self.customFormula:
                try:
                    formula = lambda x: eval(self.customFormula)
                    customValue = formula(float(voltageRatio))
                except Exception as e:
                    self.logger.error('%s reveived for device: %s' %  (traceback.format_exc(), self.indigoDevice.name))
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

        # Should we deal with states we receive that are not altready instantianted for the device?
        # try:
        #     if sensorState not in self.indigoDevice.states:
        #         self.indigoDevice.stateListOrDisplayStateIdChanged()
        #     self.indigoDevice.updateStateOnServer(sensorState, value=sensorValue, decimalPlaces=self.decimalPlaces)
        # except Exception as e:
        #     self.logger.error('%s reveived for device: %s, state name: %s' %  (traceback.format_exc(), self.indigoDevice.name, sensorState))

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