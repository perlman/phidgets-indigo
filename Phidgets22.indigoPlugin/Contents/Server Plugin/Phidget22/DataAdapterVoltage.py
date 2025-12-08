import sys
import ctypes
class DataAdapterVoltage:
	# Voltage supplied by external device
	DATAADAPTER_VOLTAGE_EXTERN = 1
	# 2.5V
	DATAADAPTER_VOLTAGE_2_5V = 3
	# 3.3V
	DATAADAPTER_VOLTAGE_3_3V = 4
	# 5.0V
	DATAADAPTER_VOLTAGE_5_0V = 5

	@classmethod
	def getName(self, val):
		if val == self.DATAADAPTER_VOLTAGE_EXTERN:
			return "DATAADAPTER_VOLTAGE_EXTERN"
		if val == self.DATAADAPTER_VOLTAGE_2_5V:
			return "DATAADAPTER_VOLTAGE_2_5V"
		if val == self.DATAADAPTER_VOLTAGE_3_3V:
			return "DATAADAPTER_VOLTAGE_3_3V"
		if val == self.DATAADAPTER_VOLTAGE_5_0V:
			return "DATAADAPTER_VOLTAGE_5_0V"
		return "<invalid enumeration value>"
