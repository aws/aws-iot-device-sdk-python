'''
/*
 * Copyright 2010-2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *  http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */
 '''

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import sys
import logging
import time
import json
import getopt

class shadowCallbackContainer:
    def __init__(self, deviceShadowInstance):
        self.deviceShadowInstance = deviceShadowInstance

    # Custom Shadow callback
    def customShadowCallback_Delta(self, payload, responseStatus, token):
        # payload is a JSON string ready to be parsed using json.loads(...)
        # in both Py2.x and Py3.x
        print("Received a delta message:")
        payloadDict = json.loads(payload)
        deltaMessage = json.dumps(payloadDict["state"])
        print(deltaMessage)
        print("Request to update the reported state...")
        newPayload = '{"state":{"reported":' + deltaMessage + '}}'
        self.deviceShadowInstance.shadowUpdate(newPayload, None, 5)
        print("Sent.")

# Usage
usageInfo = """Usage:

Use certificate based mutual authentication:
python ThingShadowEcho.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath> -t <ThingName>

Use MQTT over WebSocket:
python ThingShadowEcho.py -e <endpoint> -r <rootCAFilePath> -w -t <ThingName>
Type "python ThingShadowEcho.py -h" for available options.


"""
# Help info
helpInfo = """-e, --endpoint
    Your AWS IoT custom endpoint
-r, --rootCA
    Root CA file path
-c, --cert
    Certificate file path
-k, --key
    Private key file path
-w, --websocket
    Use MQTT over WebSocket
-t, --thingname
    The thing name
-h, --help
    Help information


"""

# Read in command-line parameters
useWebsocket = False
host = ""
rootCAPath = ""
certificatePath = ""
privateKeyPath = ""
theThingName = ""

try:
    opts, args = getopt.getopt(sys.argv[1:], "hwe:k:c:r:t:", ["help", "endpoint=", "key=","cert=","rootCA=", "thingname=", "websocket"])
    if len(opts) == 0:
        raise getopt.GetoptError("No input parameters!")
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(helpInfo)
            exit(0)
        if opt in ("-e", "--endpoint"):
            host = arg
        if opt in ("-r", "--rootCA"):
            rootCAPath = arg
        if opt in ("-c", "--cert"):
            certificatePath = arg
        if opt in ("-k", "--key"):
            privateKeyPath = arg
        if opt in ("-t", "--thingname"):
            theThingName = arg
        if opt in ("-w", "--websocket"):
            useWebsocket = True
except getopt.GetoptError:
    print(usageInfo)
    exit(1)

# Missing configuration notification
missingConfiguration = False
if not host:
    print("Missing '-e' or '--endpoint'")
    missingConfiguration = True
if not rootCAPath:
    print("Missing '-r' or '--rootCA'")
    missingConfiguration = True
if not theThingName:
    print("Missing '-t' or '--thingname'")
    missingConfiguration = True
if not useWebsocket:
    if not certificatePath:
        print("Missing '-c' or '--cert'")
        missingConfiguration = True
    if not privateKeyPath:
        print("Missing '-k' or '--key'")
        missingConfiguration = True
if missingConfiguration:
    exit(2)

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Init AWSIoTMQTTShadowClient
myAWSIoTMQTTShadowClient = None
if useWebsocket:
    myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(theThingName, useWebsocket=True)
    myAWSIoTMQTTShadowClient.configureEndpoint(host, 443)
    myAWSIoTMQTTShadowClient.configureCredentials(rootCAPath)
else:
    myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(theThingName)
    myAWSIoTMQTTShadowClient.configureEndpoint(host, 8883)
    myAWSIoTMQTTShadowClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTShadowClient configuration
myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect to AWS IoT
myAWSIoTMQTTShadowClient.connect()

# Create a deviceShadow with persistent subscription
Bot = myAWSIoTMQTTShadowClient.createShadowHandlerWithName(theThingName, True)
shadowCallbackContainer_Bot = shadowCallbackContainer(Bot)

# Listen on deltas
Bot.shadowRegisterDeltaCallback(shadowCallbackContainer_Bot.customShadowCallback_Delta)

# Loop forever
while True:
    pass
