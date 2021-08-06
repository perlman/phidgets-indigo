#  For reference from constants.h
#  #define PUNK_BOOL       0x02                    /* Unknown Boolean */
#  #define PUNK_INT8       INT8_MAX                /* Unknown Short   (8-bit) */
#  #define PUNK_UINT8      UINT8_MAX               /* Unknown Short   (8-bit unsigned) */
#  #define PUNK_INT16      INT16_MAX               /* Unknown Short   (16-bit) */
#  #define PUNK_UINT16     UINT16_MAX              /* Unknown Short   (16-bit unsigned) */
#  #define PUNK_INT32      INT32_MAX               /* Unknown Integer (32-bit) */
#  #define PUNK_UINT32     UINT32_MAX              /* Unknown Integer (32-bit unsigned) */
#  #define PUNK_INT64      INT64_MAX               /* Unknown Integer (64-bit) */
#  #define PUNK_UINT64     UINT64_MAX              /* Unknown Integer (64-bit unsigned) */
#  #define PUNK_DBL        1e300                   /* Unknown Double */
#  #define PUNK_FLT        1e30                    /* Unknown Float */
#  #define PUNK_ENUM       INT32_MAX               /* Unknown Enum */
#  #define PUNK_SIZE       SIZE_MAX                /* Unknown size_t */
#  #define PFALSE          0x00                    /* False. Used for boolean values. */
#  #define PTRUE           0x01                    /* True. Used for boolean values. */
#  #define PRIphid         "P"                     /* mos_printf format string for printing a PhidgetHandle */



class PhidgetSensorInfo(object):
    def __init__(self):
        self.stateNames = {}
        # [0] = unit name, [1] = unit short name
        self.stateNames['PHIDUNIT_NONE'] = ["none",""]
        self.stateNames['PHIDUNIT_BOOLEAN'] = ["boolean",""]
        self.stateNames['PHIDUNIT_PERCENT'] = ["percent","%"]
        self.stateNames['PHIDUNIT_DECIBEL'] = ["decibel","dB"]
        self.stateNames['PHIDUNIT_MILLIMETER'] = ["millimeter","mm"]
        self.stateNames['PHIDUNIT_CENTIMETER'] = ["centimeter","cm"]
        self.stateNames['PHIDUNIT_METER'] = ["meter","m"]
        self.stateNames['PHIDUNIT_GRAM'] = ["gram","g"]
        self.stateNames['PHIDUNIT_KILOGRAM'] = ["kilogram","kg"]
        self.stateNames['PHIDUNIT_MILLIAMPERE'] = ["milliampere","mA"]
        self.stateNames['PHIDUNIT_AMPERE'] = ["ampere","A"]
        self.stateNames['PHIDUNIT_KILOPASCAL'] = ["kilopascal","kPa"]
        self.stateNames['PHIDUNIT_VOLT'] = ["volt","V"]
        self.stateNames['PHIDUNIT_DEGREE_CELCIUS'] = ["degree Celsius","C"]
        #self.stateNames['PHIDUNIT_DEGREE_CELCIUS'] = ["degree Celsius","\xC2\xB0""C"]
        self.stateNames['PHIDUNIT_LUX'] = ["lux","lx"]
        self.stateNames['PHIDUNIT_GAUSS'] = ["gauss","G"]
        self.stateNames['PHIDUNIT_PH'] = ["pH",""]
        self.stateNames['PHIDUNIT_WATT'] = ["watt","W"]

        self.phDict = {}
        # [0] = formula,
        # [1] = input range, &
        # [2] = unit name
        self.phDict['SENSOR_TYPE_1101_SHARP_2D120X'] = ['(voltageRatio - 0.011), 2); // cm',
        '(sensorValue < 30.0)); // cm',
        self.stateNames['PHIDUNIT_CENTIMETER']]

        self.phDict['SENSOR_TYPE_1101_SHARP_2Y0A02'] = ['(voltageRatio - 0.01692), 2); // cm',
        '(sensorValue < 150.0)); // cm',
        self.stateNames['PHIDUNIT_CENTIMETER']]

        self.phDict['SENSOR_TYPE_1101_SHARP_2Y0A21'] = ['(voltageRatio - 0.02), 2); // cm',
        '(sensorValue < 80.0)); // cm',
        self.stateNames['PHIDUNIT_CENTIMETER']]

        self.phDict['SENSOR_TYPE_1102'] = ['voltageRatio < 0.4; // true/false', '(PTRUE); // true/false',
        self.stateNames['PHIDUNIT_BOOLEAN']]

        self.phDict['SENSOR_TYPE_1103'] = ['voltageRatio < 0.1; // true/false',
        '(PTRUE); // true/false',
        self.stateNames['PHIDUNIT_BOOLEAN']]

        self.phDict['SENSOR_TYPE_1104'] = ['(voltageRatio * 2 - 1, 5); // +- 1',
        '(PTRUE); // +- 1',
        self.stateNames['PHIDUNIT_NONE']]

        self.phDict['SENSOR_TYPE_1105'] = ['voltageRatio; // 0-1',
        '(PTRUE); // 0-1',
        self.stateNames['PHIDUNIT_NONE']]

        self.phDict['SENSOR_TYPE_1106'] = ['voltageRatio; // 0-1',
        '(PTRUE); // 0-1',
        self.stateNames['PHIDUNIT_NONE']]

        self.phDict['SENSOR_TYPE_1107'] = ['(voltageRatio * 190.6) - 40.2, 3); // %RH',
        '(sensorValue < 100.0)); // %RH',
        self.stateNames['PHIDUNIT_PERCENT']]

        self.phDict['SENSOR_TYPE_1108'] = ['(0.5 - voltageRatio) * 1000, 2); // Gauss',
        '(sensorValue < 500.0)); // Gauss',
        self.stateNames['PHIDUNIT_GAUSS']]

        self.phDict['SENSOR_TYPE_1109'] = ['voltageRatio; // 0-1',
        '(PTRUE); // 0-1',
        self.stateNames['PHIDUNIT_NONE']]

        self.phDict['SENSOR_TYPE_1110'] = ['voltageRatio < 0.5; // true/false',
        '(PTRUE); // true/false',
        self.stateNames['PHIDUNIT_BOOLEAN']]

        self.phDict['SENSOR_TYPE_1111'] = ['(voltageRatio * 2 - 1, 5); // +- 1',
        '(PTRUE); // +- 1',
        self.stateNames['PHIDUNIT_NONE']]

        self.phDict['SENSOR_TYPE_1112'] = ['voltageRatio; // 0-1',
        '(PTRUE); // 0-1',
        self.stateNames['PHIDUNIT_NONE']]

        self.phDict['SENSOR_TYPE_1113'] = ['(voltageRatio * 2 - 1, 5); // +- 1',
        '(sensorValue < 1.0)); // +- 1',
        self.stateNames['PHIDUNIT_NONE']]

        self.phDict['SENSOR_TYPE_1114'] = ['(voltage / 0.02 - 50, 3); // Degrees Celcius',
        '(sensorValue < 125.0)); // Degrees Celcius',
        self.stateNames['PHIDUNIT_DEGREE_CELCIUS']]

        self.phDict['SENSOR_TYPE_1115'] = ['(voltageRatio / 0.004 + 10, 3); // kPa',
        '(sensorValue < 250.0)); // kPa',
        self.stateNames['PHIDUNIT_KILOPASCAL']]

        self.phDict['SENSOR_TYPE_1116'] = ['voltageRatio; // 0-1',
        '(PTRUE); // 0-1',
        self.stateNames['PHIDUNIT_NONE']]

        self.phDict['SENSOR_TYPE_1117'] = ['(voltage * 12 - 30, 3); // V',
        '(sensorValue < 30.0)); // V',
        self.stateNames['PHIDUNIT_VOLT']]

        self.phDict['SENSOR_TYPE_1118_AC'] = ['(voltageRatio * 69.38, 3); // RMS Amps',
        '(sensorValue < 50.0)); // RMS Amps',
        self.stateNames['PHIDUNIT_AMPERE']]

        self.phDict['SENSOR_TYPE_1118_DC'] = ['(voltageRatio / 0.008 - 62.5, 3); //DC Amps',
        '(sensorValue < 50.0)); //DC Amps',
        self.stateNames['PHIDUNIT_AMPERE']]

        self.phDict['SENSOR_TYPE_1119_AC'] = ['(voltageRatio * 27.75, 4); // RMS Amps',
        '(sensorValue < 20.0)); // RMS Amps',
        self.stateNames['PHIDUNIT_AMPERE']]

        self.phDict['SENSOR_TYPE_1119_DC'] = ['(voltageRatio / 0.02 - 25, 4); //DC Amps',
        '(sensorValue < 20.0)); //DC Amps',
        self.stateNames['PHIDUNIT_AMPERE']]

        self.phDict['SENSOR_TYPE_1120'] = ['voltageRatio; // 0-1',
        '(PTRUE); // 0-1',
        self.stateNames['PHIDUNIT_NONE']]

        self.phDict['SENSOR_TYPE_1121'] = ['voltageRatio; // 0-1',
        '(PTRUE); // 0-1',
        self.stateNames['PHIDUNIT_NONE']]

        self.phDict['SENSOR_TYPE_1122_AC'] = ['(voltageRatio * 42.04, 3); // RMS Amps',
        '(sensorValue < 30.0)); // RMS Amps',
        self.stateNames['PHIDUNIT_AMPERE']]

        self.phDict['SENSOR_TYPE_1122_DC'] = ['(voltageRatio / 0.0132 - 37.8787, 3); // DC Amps',
        '(sensorValue < 30.0)); // DC Amps',
        self.stateNames['PHIDUNIT_AMPERE']]

        self.phDict['SENSOR_TYPE_1123'] = ['(voltage * 12 - 30, 3); // V',
        '(sensorValue < 30.0)); // V',
        self.stateNames['PHIDUNIT_VOLT']]

        self.phDict['SENSOR_TYPE_1124'] = ['(voltageRatio * 222.2 - 61.111, 3); // Degrees Celcius',
        '(sensorValue < 80.0)); // Degrees Celcius',
        self.stateNames['PHIDUNIT_DEGREE_CELCIUS']]

        self.phDict['SENSOR_TYPE_1125_HUMIDITY'] = ['(voltageRatio * 190.6 - 40.2, 3); // %RH',
        '(sensorValue < 100.0)); // %RH',
        self.stateNames['PHIDUNIT_PERCENT']]

        self.phDict['SENSOR_TYPE_1125_TEMPERATURE'] = ['(voltageRatio * 222.2 - 61.111, 3); // Degrees Celcius',
        '(sensorValue < 80.0)); // Degrees Celcius',
        self.stateNames['PHIDUNIT_DEGREE_CELCIUS']]

        self.phDict['SENSOR_TYPE_1126'] = ['(voltageRatio / 0.018 - 27.7777, 3); // kPa',
        '(sensorValue < 25.0)); // kPa',
        self.stateNames['PHIDUNIT_KILOPASCAL']]

        self.phDict['SENSOR_TYPE_1127'] = ['(voltage * 200, 2); // lux',
        '(sensorValue < 1000.0)); // lux',
        self.stateNames['PHIDUNIT_LUX']]

        self.phDict['SENSOR_TYPE_1128'] = ['(voltageRatio * 1296, 2); // cm',
        '(sensorValue < 6500.0)); // cm',
        self.stateNames['PHIDUNIT_CENTIMETER']]

        self.phDict['SENSOR_TYPE_1129'] = ['voltageRatio > 0.5; // true/false',
        '(PTRUE); // true/false',
        self.stateNames['PHIDUNIT_BOOLEAN']]

        self.phDict['SENSOR_TYPE_1130_ORP'] = ['(V)',
        '(V)',
        self.stateNames['PHIDUNIT_VOLT']]

        self.phDict['SENSOR_TYPE_1130_PH'] = ['(voltage * 3.56 - 1.889, 4); // pH',
        '((sensorValue > 0.0) && (sensorValue < 14.0)); // pH',
        self.stateNames['PHIDUNIT_PH']]

        self.phDict['SENSOR_TYPE_1131'] = ['(voltageRatio * 5.199), 2); // grams',
        '(sensorValue < 2000.0)); // grams',
        self.stateNames['PHIDUNIT_GRAM']]

        self.phDict['SENSOR_TYPE_1132'] = ['(voltage / 0.225, 4); // mA',
        '(sensorValue < 20.0)); // mA',
        self.stateNames['PHIDUNIT_MILLIAMPERE']]

        self.phDict['SENSOR_TYPE_1133'] = ['(voltage * 200) + 9.872, 4); // dB',
        '(sensorValue < 100.0)); // dB',
        self.stateNames['PHIDUNIT_DECIBEL']]

        self.phDict['SENSOR_TYPE_1134'] = ['voltageRatio; // 0-1',
        '(PTRUE); // 0-1',
        self.stateNames['PHIDUNIT_NONE']]

        self.phDict['SENSOR_TYPE_1135'] = ['(voltage - 2.5) / 0.0681, 3); // V',
        '(sensorValue < 30.0)); // V',
        self.stateNames['PHIDUNIT_VOLT']]

        self.phDict['SENSOR_TYPE_1136'] = ['(voltageRatio / 0.2 - 2.5, 4); // kPa',
        '(sensorValue < 2.0)); // kPa',
        self.stateNames['PHIDUNIT_KILOPASCAL']]

        self.phDict['SENSOR_TYPE_1137'] = ['(voltageRatio / 0.057143 - 8.75, 4); // kPa',
        '(sensorValue < 7.0)); // kPa',
        self.stateNames['PHIDUNIT_KILOPASCAL']]

        self.phDict['SENSOR_TYPE_1138'] = ['(voltageRatio / 0.018 - 2.222, 3); // kPa',
        '(sensorValue < 50.0)); // kPa',
        self.stateNames['PHIDUNIT_KILOPASCAL']]

        self.phDict['SENSOR_TYPE_1139'] = ['(voltageRatio / 0.009 - 4.444, 3); // kPa',
        '(sensorValue < 100.0)); // kPa',
        self.stateNames['PHIDUNIT_KILOPASCAL']]

        self.phDict['SENSOR_TYPE_1140'] = ['(voltageRatio / 0.002421 + 3.478, 2); // kPa',
        '(sensorValue < 400.0)); // kPa',
        self.stateNames['PHIDUNIT_KILOPASCAL']]

        self.phDict['SENSOR_TYPE_1141'] = ['(voltageRatio / 0.0092 + 10.652, 2); // kPa',
        '(sensorValue < 115.0)); // kPa',
        self.stateNames['PHIDUNIT_KILOPASCAL']]

        self.phDict['SENSOR_TYPE_1142'] = ['(voltage * 295.7554 + 33.67076, 2); // lux  NOTE: user should really calculate using calibration values',
        '(sensorValue < 1000.0)); // lux  NOTE: user should really calculate using calibration values',
        self.stateNames['PHIDUNIT_LUX']]

        self.phDict['SENSOR_TYPE_1143'] = ['(voltage * 4.77 - 0.56905), 4); // lux  NOTE: user should really calculate using calibration values',
        '(sensorValue < 70000.0)); // lux  NOTE: user should really calculate using calibration values',
        self.stateNames['PHIDUNIT_LUX']]

        self.phDict['SENSOR_TYPE_1146'] = ['(1.967 * voltageRatio), 2); // mm',
        '(sensorValue < 4.0)); // mm',
        self.stateNames['PHIDUNIT_MILLIMETER']]

        self.phDict['SENSOR_TYPE_3120'] = ['(voltageRatio / 0.15432 - 0.647989, 4); // kg',
        '(sensorValue < 4.5)); // kg',
        self.stateNames['PHIDUNIT_KILOGRAM']]

        self.phDict['SENSOR_TYPE_3121'] = ['(voltageRatio / 0.0617295 - 1.619971, 4); // kg',
        '(sensorValue < 11.3)); // kg',
        self.stateNames['PHIDUNIT_KILOGRAM']]

        self.phDict['SENSOR_TYPE_3122'] = ['(voltageRatio / 0.0308647 - 3.239943, 3); // kg',
        '(sensorValue < 22.7)); // kg',
        self.stateNames['PHIDUNIT_KILOGRAM']]

        self.phDict['SENSOR_TYPE_3123'] = ['(voltageRatio / 0.0154324 - 6.479886, 3); // kg',
        '(sensorValue < 45.3)); // kg',
        self.stateNames['PHIDUNIT_KILOGRAM']]

        self.phDict['SENSOR_TYPE_3130'] = ['(voltageRatio * 190.6 - 40.2, 3); // %RH',
        '(sensorValue < 100.0)); // %RH',
        self.stateNames['PHIDUNIT_PERCENT']]

        self.phDict['SENSOR_TYPE_3500'] = ['(voltage / 0.5, 4); // RMS Amps',
        '(sensorValue < 10.0)); // RMS Amps',
        self.stateNames['PHIDUNIT_AMPERE']]

        self.phDict['SENSOR_TYPE_3501'] = ['(voltage / 0.2, 4); // RMS Amps',
        '(sensorValue < 25.0)); // RMS Amps',
        self.stateNames['PHIDUNIT_AMPERE']]

        self.phDict['SENSOR_TYPE_3502'] = ['(voltage / 0.1, 4); // RMS Amps',
        '(sensorValue < 50.0)); // RMS Amps',
        self.stateNames['PHIDUNIT_AMPERE']]

        self.phDict['SENSOR_TYPE_3503'] = ['(voltage / 0.05, 3); // RMS Amps',
        '(sensorValue < 100.0)); // RMS Amps',
        self.stateNames['PHIDUNIT_AMPERE']]

        self.phDict['SENSOR_TYPE_3507'] = ['(voltage * 50, 3); // V AC',
        '(sensorValue < 250.0)); // V AC',
        self.stateNames['PHIDUNIT_VOLT']]

        self.phDict['SENSOR_TYPE_3508'] = ['(voltage * 50, 3); // V AC',
        '(sensorValue < 250.0)); // V AC',
        self.stateNames['PHIDUNIT_VOLT']]

        self.phDict['SENSOR_TYPE_3509'] = ['(voltage * 40, 3); // V DC',
        '(sensorValue < 200.0)); // V DC',
        self.stateNames['PHIDUNIT_VOLT']]

        self.phDict['SENSOR_TYPE_3510'] = ['(voltage * 15, 4); // V DC',
        '(sensorValue < 75.0)); // V DC',
        self.stateNames['PHIDUNIT_VOLT']]

        self.phDict['SENSOR_TYPE_3511'] = ['(voltage * 2, 4); // mA',
        '(sensorValue < 10.0)); // mA',
        self.stateNames['PHIDUNIT_MILLIAMPERE']]

        self.phDict['SENSOR_TYPE_3512'] = ['(voltage * 20, 3); // mA',
        '(sensorValue < 100.0)); // mA',
        self.stateNames['PHIDUNIT_MILLIAMPERE']]

        self.phDict['SENSOR_TYPE_3513'] = ['(voltage * 200, 2); // mA',
        '(sensorValue < 1000.0)); // mA',
        self.stateNames['PHIDUNIT_MILLIAMPERE']]

        self.phDict['SENSOR_TYPE_3514'] = ['(voltage * 1500, 1); // W  NOTE: User must determine offset',
        '(sensorValue < 7500.0)); // W  NOTE: User must determine offset',
        self.stateNames['PHIDUNIT_WATT']]

        self.phDict['SENSOR_TYPE_3515'] = ['(voltage * 1500, 1); // W  NOTE: User must determine offset',
        '(sensorValue < 7500.0)); // W  NOTE: User must determine offset',
        self.stateNames['PHIDUNIT_WATT']]

        self.phDict['SENSOR_TYPE_3516'] = ['(voltage * 250, 2); // W  NOTE: User must determine offset',
        '(sensorValue < 1250.0)); // W  NOTE: User must determine offset',
        self.stateNames['PHIDUNIT_WATT']]

        self.phDict['SENSOR_TYPE_3517'] = ['(voltage * 250, 2); // W  NOTE: User must determine offset',
        '(sensorValue < 1250.0)); // W  NOTE: User must determine offset',
        self.stateNames['PHIDUNIT_WATT']]

        self.phDict['SENSOR_TYPE_3518'] = ['(voltage * 110, 3); // W  NOTE: User must determine offset',
        '(sensorValue < 550.0)); // W  NOTE: User must determine offset',
        self.stateNames['PHIDUNIT_WATT']]

        self.phDict['SENSOR_TYPE_3519'] = ['(voltage * 330, 2); // W  NOTE: User must determine offset',
        '(sensorValue < 1650.0)); // W  NOTE: User must determine offset',
        self.stateNames['PHIDUNIT_WATT']]

        self.phDict['SENSOR_TYPE_3520'] = ['(voltageRatio - 0.011), 2); // cm',
        '(sensorValue < 30.0)); // cm',
        self.stateNames['PHIDUNIT_CENTIMETER']]

        self.phDict['SENSOR_TYPE_3521'] = ['(voltageRatio - 0.02), 2); // cm',
        '(sensorValue < 80.0)); // cm',
        self.stateNames['PHIDUNIT_CENTIMETER']]

        self.phDict['SENSOR_TYPE_3522'] = ['(voltageRatio - 0.01692), 2); // cm',
        '(sensorValue < 150.0)); // cm',
        self.stateNames['PHIDUNIT_CENTIMETER']]

        self.phDict['SENSOR_TYPE_3584'] = ['(voltage * 10, 4); // DC Amps',
        '(sensorValue < 50.0)); // DC Amps',
        self.stateNames['PHIDUNIT_AMPERE']]

        self.phDict['SENSOR_TYPE_3585'] = ['(voltage * 20, 3); // DC Amps',
        '(sensorValue < 100.0)); // DC Amps',
        self.stateNames['PHIDUNIT_AMPERE']]

        self.phDict['SENSOR_TYPE_3586'] = ['(voltage * 50, 3); // DC Amps',
        '(sensorValue < 250.0)); // DC Amps',
        self.stateNames['PHIDUNIT_AMPERE']]

        self.phDict['SENSOR_TYPE_3587'] = ['(voltage * 20 - 50, 3); // DC Amps',
        '(sensorValue < 50.0)); // DC Amps',
        self.stateNames['PHIDUNIT_AMPERE']]

        self.phDict['SENSOR_TYPE_3588'] = ['(voltage * 40 - 100, 3); // DC Amps',
        '(sensorValue < 100.0)); // DC Amps',
        self.stateNames['PHIDUNIT_AMPERE']]

        self.phDict['SENSOR_TYPE_3589'] = ['(voltage * 100 - 250, 3); // DC Amps',
        '(sensorValue < 250.0)); // DC Amps',
        self.stateNames['PHIDUNIT_AMPERE']]

        self.phDict['SENSOR_TYPE_MOT2002_HIGH'] = ['(voltageInputSupport->motionSensorBaseline != PUNK_DBL)',
        '(voltageInputSupport, 0.04);',
        self.stateNames['PHIDUNIT_NONE']]

        self.phDict['SENSOR_TYPE_MOT2002_LOW'] = ['(voltageInputSupport->motionSensorBaseline != PUNK_DBL)',
        '(voltageInputSupport, 0.8);',
        self.stateNames['PHIDUNIT_NONE']]

        self.phDict['SENSOR_TYPE_MOT2002_MED'] = ['(voltageInputSupport->motionSensorBaseline != PUNK_DBL)',
        '(voltageInputSupport, 0.4);',
        self.stateNames['PHIDUNIT_NONE']]

        self.phDict['SENSOR_TYPE_VCP4114'] = ['(voltage - 2.5) / 0.0625), 3); // DC Amps',
        '(sensorValue < 25.0)); // DC Amps',
        self.stateNames['PHIDUNIT_AMPERE']]

        self.phDict['SENSOR_TYPE_VOLTAGE'] = ['voltage',
        '(PTRUE)',
        self.stateNames['PHIDUNIT_NONE']]

        self.phDict['SENSOR_TYPE_VOLTAGERATIO'] = ['voltageRatio',
        '(PTRUE)',
        self.stateNames['PHIDUNIT_NONE']]

    def getSensorInfo(self, phidget):
        if phidget in self.phDict:
            phInfo = self.phDict[phidget]
        elif phidget + '_AC' in self.phDict:
            phInfo = self.phDict[phidget + '_AC']
        elif phidget + '_DC' in self.phDict:
            phInfo = self.phDict[phidget + '_DC']
        else:
            phInfo = "none"

        return phInfo


    # for phidget in self.phDict:
    #     print("%s: %s (%s)" % (phidget, stateNames[self.phDict[phidget][2]][0], stateNames[self.phDict[phidget][2]][1]))
