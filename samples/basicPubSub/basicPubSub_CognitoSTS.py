'''
/*
 * Copyright 2010-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
from AWSIoTPythonSDK.core.util.providers import IAMCredentialsProvider
from datetime import datetime, timedelta
import logging
import time
import argparse


# Custom MQTT message callback
def customCallback(client, userdata, message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")


# Read in command-line parameters
parser = argparse.ArgumentParser()
parser.add_argument("-e", "--endpoint", action="store", required=True, dest="host", help="Your AWS IoT custom endpoint")
parser.add_argument("-r", "--rootCA", action="store", required=True, dest="rootCAPath", help="Root CA file path")
parser.add_argument("-C", "--CognitoIdentityPoolID", action="store", required=True, dest="cognitoIdentityPoolID",
                    help="Your AWS Cognito Identity Pool ID")
parser.add_argument("-id", "--clientId", action="store", dest="clientId", default="basicPubSub_CognitoSTS",
                    help="Targeted client id")
parser.add_argument("-t", "--topic", action="store", dest="topic", default="sdk/test/Python", help="Targeted topic")

args = parser.parse_args()
host = args.host
rootCAPath = args.rootCAPath
clientId = args.clientId
cognitoIdentityPoolID = args.cognitoIdentityPoolID
topic = args.topic

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Cognito auth
class CognitoIdentityProvider(IAMCredentialsProvider):
    def __init__(self, identityPoolID, region):
        IAMCredentialsProvider.__init__(self)

        self.identityPoolID = identityPoolID
        self.region = region

        self.updated_at = datetime.min

    def _refresh_credentials(self):
        if datetime.now() - self.updated_at < timedelta(hours=1):
            return

        self.updated_at = datetime.now()

        cognitoIdentityClient = boto3.client('cognito-identity', region_name=self.region)

        temporaryIdentityId = cognitoIdentityClient.get_id(IdentityPoolId=self.identityPoolID)
        identityID = temporaryIdentityId["IdentityId"]

        temporaryCredentials = cognitoIdentityClient.get_credentials_for_identity(IdentityId=identityID)
        self._aws_access_key_id = temporaryCredentials["Credentials"]["AccessKeyId"]
        self._aws_secret_access_key = temporaryCredentials["Credentials"]["SecretKey"]
        self._aws_session_token = temporaryCredentials["Credentials"]["SessionToken"]

    def get_access_key_id(self):
        self._refresh_credentials()
        return self._aws_access_key_id

    def get_secret_access_key(self):
        self._refresh_credentials()
        return self._aws_secret_access_key

    def get_session_token(self):
        self._refresh_credentials()
        return self._aws_session_token


region = host.split('.')[2]
credentials_provider = CognitoIdentityProvider(cognitoIdentityPoolID, region)

# Init AWSIoTMQTTClient
myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId, useWebsocket=True)

# AWSIoTMQTTClient configuration
myAWSIoTMQTTClient.configureEndpoint(host, 443)
myAWSIoTMQTTClient.configureCredentials(rootCAPath)
myAWSIoTMQTTClient.configureIAMCredentialsProvider(credentials_provider)
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
myAWSIoTMQTTClient.connect()
myAWSIoTMQTTClient.subscribe(topic, 1, customCallback)
time.sleep(2)

# Publish to the same topic in a loop forever
loopCount = 0
while True:
    myAWSIoTMQTTClient.publish(topic, "New Message " + str(loopCount), 1)
    loopCount += 1
    time.sleep(1)
