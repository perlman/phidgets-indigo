
# phidgets-indigo

<img src="./Phidgets22.indigoPlugin/Contents/Resources/icon.png" width="200" height="200" alt="[Phidget22 logo]" align="right"/>

An update to the [Phidgets Plugin](https://www.indigodomo.com/pluginstore/76/)
for [Indigo](https://www.indigodomo.com/).

## Requirements

- [Indigo >= 2021.1](https://www.indigodomo.com)
- [Phidgets 2.2 Driver](https://www.phidgets.com/docs/OS_-_macOS)

## Status

The following Phidget classes are currently supported:
* DigitalInput
* DigitalOutput
* FrequencyCounter
* TemperatureSensor
* VoltageInput
* VoltageRatioInput

Various devices are supported, including PhidgetInterfaceKits and VINT devices.
Only network phidgets are supported. To use local attached phidgets, enable the [network server](https://www.phidgets.com/docs/Phidget_Network_Server).

## Phidget Addressing

See the [Phidget Documentation](https://www.phidgets.com/docs/Addressing_Phidgets]) for details on how to address a Phidget.

## Other notes

- The [Phidgets Python 2.2 API](https://www.phidgets.com/docs/Language_-_Python) has been included, with a minor modification to use utf-8 encoding. This was required for python2.7 to grok ± which is used in several of the comments.
