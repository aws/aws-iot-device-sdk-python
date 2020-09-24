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

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import logging
import time
import argparse
import json
import subprocess



# Custom MQTT message callback
def secureTunnelNotificationCallback(client, userdata, message):
    logger.debug('Received a secure tunneling notification: %s', message.payload)
    notification = json.loads(message.payload)
    logger.debug('clientAccessToken: %s', notification['clientAccessToken'])
    logger.debug('region: %s', notification['region'])
    logger.debug('clientMode: %s', notification['clientMode'])

    if notification['clientMode'] != 'destination':
        logger.warn('clientMode %s not supported', notification['clientMode'])
        return

    logger.debug('services: %s', notification['services'])
    if len(notification['services']) > 1:
        logger.warn('%d services specified; ignoring all but the first service', len(notification['services']))

    service = notification['services'][0]
    logger.debug('initializing secure proxy for %s', service)

    if service == 'ssh':
        servicePort = 22
    elif service == 'vnc':
        servicePort = 5900
    else:
        logger.warn('service %s not supported', service)
        return

    subprocess.run(["localproxy",
        "-t", notification['clientAccessToken'],
        "-r", notification['region'],
        "-d", "localhost:{portNumber}".format(portNumber = servicePort),
        "-v", "5"
    ])

# Read in command-line parameters
parser = argparse.ArgumentParser()
parser.add_argument("-e", "--endpoint", action="store", required=True, dest="host", help="Your AWS IoT custom endpoint")
parser.add_argument("-r", "--rootCA", action="store", required=True, dest="rootCAPath", help="Root CA file path")
parser.add_argument("-c", "--cert", action="store", dest="certificatePath", help="Certificate file path")
parser.add_argument("-k", "--key", action="store", dest="privateKeyPath", help="Private key file path")
parser.add_argument("-p", "--port", action="store", dest="port", type=int, help="Port number override")
parser.add_argument("-w", "--websocket", action="store_true", dest="useWebsocket", default=False,
                    help="Use MQTT over WebSocket")
parser.add_argument("-id", "--clientId", action="store", dest="clientId", default="basicPubSub",
                    help="Targeted client id")
parser.add_argument("-t", "--topic", action="store", dest="topic", default="$aws/things/{thingName}/tunnels/notify", help="Targeted topic")


args = parser.parse_args()
host = args.host
rootCAPath = args.rootCAPath
certificatePath = args.certificatePath
privateKeyPath = args.privateKeyPath
port = args.port
useWebsocket = args.useWebsocket
clientId = args.clientId
topic = args.topic.format(thingName = clientId)

if args.useWebsocket and args.certificatePath and args.privateKeyPath:
    parser.error("X.509 cert authentication and WebSocket are mutual exclusive. Please pick one.")
    exit(2)

if not args.useWebsocket and (not args.certificatePath or not args.privateKeyPath):
    parser.error("Missing credentials for authentication.")
    exit(2)

# Port defaults
if args.useWebsocket and not args.port:  # When no port override for WebSocket, default to 443
    port = 443
if not args.useWebsocket and not args.port:  # When no port override for non-WebSocket, default to 8883
    port = 8883

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Init AWSIoTMQTTClient
myAWSIoTMQTTClient = None
if useWebsocket:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId, useWebsocket=True)
    myAWSIoTMQTTClient.configureEndpoint(host, port)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath)
else:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
    myAWSIoTMQTTClient.configureEndpoint(host, port)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT listening for Secure Tunnel Notifications
myAWSIoTMQTTClient.connect()
logger.debug('Connection to AWS IoT Core initiated')
myAWSIoTMQTTClient.subscribe(topic, 1, secureTunnelNotificationCallback)

# Maintain connectivity until program is terminated
logger.debug('Subscribed to Secure Tunnel Notifications on topic %s', topic)
logger.debug('Ctrl+C To exit the program')
while True:
    # myAWSIoTMQTTClient.publish(topic, '{"message":"Not dead yet!"}', 1)
    # logger.debug('Published heartbeat message')
    time.sleep(60)
