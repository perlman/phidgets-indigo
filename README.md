# phidgets-indigo

An update to the [Phidgets Plugin](https://www.indigodomo.com/pluginstore/76/)
for [Indigo](https://www.indigodomo.com/).

## Requirements

- [Indigo 7.x](https://www.indigodomo.com)
- [Phidgets 2.2 Driver](https://www.phidgets.com/docs/OS_-_macOS)

## Status

The only Phidgets currently supported are analog Phidgets using VoltageRatioInput and VoltageInput.
This code is currently _unstable_ and is in the process of being reworked.

## Phidget Addressing

See the [Phidget Documentation](https://www.phidgets.com/docs/Addressing_Phidgets]) for details on how to address a Phidget.

## Other notes

- The [Phidgets Python 2.2 API](https://www.phidgets.com/docs/Language_-_Python) has been included, with a minor modification to use utf-8 encoding. This was required for python2.7 to grok ± which is used in several of the comments.
