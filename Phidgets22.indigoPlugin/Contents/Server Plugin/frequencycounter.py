# -*- coding: utf-8 -*-
import traceback

import indigo

from Phidget22.PhidgetException import PhidgetException
from Phidget22.Devices.FrequencyCounter import FrequencyCounter
from Phidget22.ErrorCode import ErrorCode

from phidget import PhidgetBase

import phidget_util

class FrequencyCounterPhidget(PhidgetBase):
    def __init__(self, *args, **kwargs):
        super(FrequencyCounterPhidget, self).__init__(phidget=FrequencyCounter(), *args, **kwargs)

        self.dataInterval = int(self.indigoDevice.pluginProps.get("dataInterval", 0))
        self.filterType = int(self.indigoDevice.pluginProps.get("filterType", 0))
        self.frequencyCutoff = float(self.indigoDevice.pluginProps.get("frequencyCutoff", 1))
        self.displayStateName = self.indigoDevice.pluginProps.get("displayStateName", None)
        self.decimalPlaces = int(self.indigoDevice.pluginProps.get("decimalPlaces", 2))
        self.isVintDevice = bool(self.indigoDevice.pluginProps.get("isVintDevice", False))
        self.isDAQ1400 = bool(self.indigoDevice.pluginProps.get("isDAQ1400", False))
        if self.isDAQ1400:
            self.DAQ1400inputType = int(self.indigoDevice.pluginProps.get("DAQ1400inputType", 1))
            self.DAQ1400voltage = int(self.indigoDevice.pluginProps.get("DAQ1400voltage", 2))

    def addPhidgetHandlers(self):
        self.phidget.setOnErrorHandler(self.onErrorHandler)
        self.phidget.setOnAttachHandler(self.onAttachHandler)
        self.phidget.setOnDetachHandler(self.onDetachHandler)
        self.phidget.setOnFrequencyChangeHandler(self.onFrequencyChangeHandler)

    def onAttachHandler(self, ph):
        super(FrequencyCounterPhidget, self).onAttachHandler(ph)
        try:
            newDataInterval = self.checkValueRange("dataInterval", value=self.dataInterval, minValue=self.phidget.getMinDataInterval(),  maxValue=self.phidget.getMaxDataInterval())
            if newDataInterval is None:
                self.phidget.setDataInterval(PhidgetBase.PHIDGET_DEFAULT_DATA_INTERVAL)
            else:
                self.phidget.setDataInterval(newDataInterval)

            # setFrequencyCutoff() - The frequency at which zero hertz is assumed.
            newFrequencyCutoff = self.checkValueRange('frequencyCutoff', value=self.frequencyCutoff, minValue=0, maxValue=100, zero_ok=True)
            if newFrequencyCutoff is None:
                self.phidget.setFrequencyCutoff(1.0)
            else:
                self.phidget.setFrequencyCutoff(float(newFrequencyCutoff))

            if self.isDAQ1400:
                self.phidget.setInputMode(self.DAQ1400inputType)
                self.phidget.setPowerSupply(self.DAQ1400voltage)
            else:
                # rdp. this seems to be missing in the UI - not sure how necessary it even is
                self.phidget.setEnabled(True)
                self.phidget.setFilterType(self.filterType)

        except Exception as e:
            self.logger.error(traceback.format_exc())

    def onFrequencyChangeHandler(self, ph, frequency):
        self.indigoDevice.updateStateOnServer("frequency", value=frequency,  decimalPlaces=self.decimalPlaces)

    def onCountChangeHandler(self, ph, count, timeChange):
        self.indigoDevice.updateStateOnServer("count", value=count)
        self.indigoDevice.updateStateOnServer("timeChange", value=timeChange,  decimalPlaces=self.decimalPlaces)

    def getDeviceStateList(self):
        newStatesList = indigo.List()
        newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType("frequency", "frequency", "frequency"))
        newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType("count", "count", "count"))
        newStatesList.append(self.indigo_plugin.getDeviceStateDictForNumberType("timeChange", "timeChange", "timeChange"))
        return newStatesList

    def getDeviceDisplayStateId(self):
        if self.displayStateName in ["frequency", "count", "timeChange"]:
            return self.displayStateName
        else:
            return "frequency"
