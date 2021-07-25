# -*- coding: utf-8 -*-
import traceback

import indigo

from Phidget22.PhidgetException import PhidgetException
from Phidget22.Devices.FrequencyCounter import FrequencyCounter
from Phidget22.ErrorCode import ErrorCode

from phidget import PhidgetBase

import phidget_util

class FrequencyCounterPhidget(PhidgetBase):
    def __init__(self, filterType, dataInterval, displayStateName, *args, **kwargs):
        super(FrequencyCounterPhidget, self).__init__(phidget=FrequencyCounter(), *args, **kwargs)
        self.filterType = filterType
        self.dataInterval = dataInterval
        self.displayStateName = displayStateName

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

            self.phidget.setFilterType(self.filterType)
            # rdp. this seems to be missing in the UI - not sure how necessary it enev is
            # we should also look at: setFrequencyCutoff() - (self.phidget.frequencyCutoff). The frequency at which zero hertz is assumed.
            self.phidget.setEnabled(True)
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
