#!/bin/bash
#
# This script checks which environment this
# is, brazil or ToD Worker and trying to find
# ZIP package for the latest build of SDK in
# certain directory.
# Will print out the location of ZIP package
# and return code specifying environment type:
# 0 - Brazil
# 1 - ToD
# -1 - Not supported
# Otherwise print nothing. The environment is
# not supported.

# Define usage
USAGE="usage: getSDKZIP.sh <whichSDK>"
# if input args not correct, echo usage
if [ $# -ne 1 ]; then
	echo ${USAGE}
else
# Find SDK ZIP package
	ZIPLocation=""
	if [ "$1"x == "IoTYunSDK"x ]; then
		ZIPLocation=$(find ../IotSdkArduino/build/zipPackage -name AWS-IoT-Arduino-Yun-SDK-latest.zip)
		if [ -n "$ZIPLocation" ]; then
		    echo ${ZIPLocation}
		    exit 0
		fi
		ZIPLocation=$(find ./test-runtime/ -name AWS-IoT-Arduino-Yun-SDK-latest.zip)
		if [ -n "$ZIPLocation" ]; then
		    echo ${ZIPLocation}
		    exit 1
		fi
	elif [ "$1"x == "IoTPySDK"x ]; then
		if [ -d "../../src/IotSdkPython/AWSIoTPythonSDK/" ]; then
			echo "../../src/IotSdkPython/AWSIoTPythonSDK/"
			exit 2
		fi
		if [ -d "./test-runtime/aws-iot-device-sdk-python/AWSIoTPythonSDK" ]; then
			echo "./test-runtime/aws-iot-device-sdk-python/AWSIoTPythonSDK"
			exit 3
		fi
	else
		exit -1
	fi
	exit -1
fi
