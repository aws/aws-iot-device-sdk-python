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

import boto3
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import sys
import logging
import time
import getopt

# Custom MQTT message callback
def customCallback(client, userdata, message):
	print("Received a new message: ")
	print(message.payload)
	print("from topic: ")
	print(message.topic)
	print("--------------\n\n")

# Usage
usageInfo = """Usage:

python basicPubSub_CognitoSTS.py -e <endpoint> -r <rootCAFilePath> -C <CognitoIdentityPoolID>


Type "python basicPubSub_CognitoSTS.py -h" for available options.
"""
# Help info
helpInfo = """-e, --endpoint
	Your AWS IoT custom endpoint
-r, --rootCA
	Root CA file path
-C, --CognitoIdentityPoolID
	Your AWS Cognito Identity Pool ID
-h, --help
	Help information


"""

# Read in command-line parameters
host = ""
rootCAPath = ""
cognitoIdentityPoolID = ""
try:
	opts, args = getopt.getopt(sys.argv[1:], "he:r:C:", ["help", "endpoint=", "rootCA=", "CognitoIdentityPoolID="])
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
		if opt in ("-C", "--CognitoIdentityPoolID"):
			cognitoIdentityPoolID = arg
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
if not cognitoIdentityPoolID:
	print("Missing '-C' or '--CognitoIdentityPoolID'")
	missingConfiguration = True
if missingConfiguration:
	exit(2)

# Configure logging
logger = None
if sys.version_info[0] == 3:
	logger = logging.getLogger("core")  # Python 3
else:
	logger = logging.getLogger("AWSIoTPythonSDK.core")  # Python 2
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Cognito auth
identityPoolID = cognitoIdentityPoolID
region = host.split('.')[2]
cognitoIdentityClient = boto3.client('cognito-identity', region_name=region)
# identityPoolInfo = cognitoIdentityClient.describe_identity_pool(IdentityPoolId=identityPoolID)
# print identityPoolInfo

temporaryIdentityId = cognitoIdentityClient.get_id(IdentityPoolId=identityPoolID)
identityID = temporaryIdentityId["IdentityId"]

temporaryCredentials = cognitoIdentityClient.get_credentials_for_identity(IdentityId=identityID)
AccessKeyId = temporaryCredentials["Credentials"]["AccessKeyId"]
SecretKey = temporaryCredentials["Credentials"]["SecretKey"]
SessionToken = temporaryCredentials["Credentials"]["SessionToken"]

# Init AWSIoTMQTTClient
myAWSIoTMQTTClient = AWSIoTMQTTClient("basicPubSub_CognitoSTS", useWebsocket=True)

# AWSIoTMQTTClient configuration
myAWSIoTMQTTClient.configureEndpoint(host, 443)
myAWSIoTMQTTClient.configureCredentials(rootCAPath)
myAWSIoTMQTTClient.configureIAMCredentials(AccessKeyId, SecretKey, SessionToken)
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
myAWSIoTMQTTClient.connect()
myAWSIoTMQTTClient.subscribe("sdk/test/Python", 1, customCallback)
time.sleep(2)

# Publish to the same topic in a loop forever
loopCount = 0
while True:
	myAWSIoTMQTTClient.publish("sdk/test/Python", "New Message " + str(loopCount), 1)
	loopCount += 1
	time.sleep(1)
