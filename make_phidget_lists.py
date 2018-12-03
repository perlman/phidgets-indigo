#!/usr/bin/env python2.7

#
# Use comments from the Phidget22 python library to generate a JSON file mapping
# constants to human-readable descriptions.
#

import argparse
import os
import re
import json

PHIDGET_CLASSES=["VoltageRatioSensorType", "VoltageSensorType"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phidgetpath', help="Path to Phdiget22 python library",
        default="Phidgets.indigoPlugin/Contents/Server Plugin/Phidget22/")
    parser.add_argument('--output', help="JSON output file",
        default="Phidgets.indigoPlugin/Contents/Resources/phidgets.json")
    args = parser.parse_args()

    output = {}

    for phidget_class in PHIDGET_CLASSES:
        output[phidget_class] = []
        with open(os.path.join(args.phidgetpath, "%s.py" % phidget_class), 'rb') as f:
            for m in re.finditer(r'^\t# (?P<desc>.+)\n^\t(?P<def>[0-9A-Z_]+) = (?P<value>[\d]+)',
                                 f.read().decode("UTF-8"), re.MULTILINE):
                output[phidget_class].append({
                    'value' : int(m.group('value')),
                    'desc' : m.group('desc'),
                    'def' : m.group('def')
                    })

    with open(args.output, 'w') as f:
        json.dump(output, f, ensure_ascii=False, indent=4, sort_keys=True)


if __name__ == "__main__":
    main()