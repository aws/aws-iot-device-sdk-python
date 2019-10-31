#!/usr/bin/env python3

"""
script for testing callback for messages sent with publishAsync while disconnected --> messages drained from the queue
since lib version 1.4.8 the callback was not called when the messages were drained from the queue

-----> the goal is to trigger the callback and to generate ad id to pass when calling publishAsync (instead of the string 'queued') to use for traking purpose with the callback
"""
import time
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import logging

#------------------------ Useful functions -------------------------

def _onOnline():
    print("--> Connected")

def _onOffline():
    print("--> Disconnected")

def pubCallback(mid):
    print("Received PUBACK for message id {}".format(mid))

def mqttConnect():
    try:
        myMQTTClinet.connect(30)
        return True
    except Exception as err:
        print("Error occured while connecting - error: {}".format(err))
        return False

def mqttDisconnect():
    try:
        myMQTTClinet.disconnect()
    except Exception as err:
        print("Error occured while disconnecting - error: {}".format(err))

def sendMsg(msg):
    try:
        idMsg = myMQTTClinet.publishAsync(topic, msg, qos, pubCallback)
        print("Message id {} sent".format(idMsg))
        return True
    except Exception as err:
        print("Error occured while publishing - error: {}".format(err))
        return False

#-------------------- MQTT setup ---------------------
endpoint = 'endpoint...'
topic = 'testTopic/testClient'
qos = 1

myMQTTClinet = AWSIoTMQTTClient('testClient')
myMQTTClinet.disableMetricsCollection()
myMQTTClinet.configureEndpoint(endpoint,8883)
myMQTTClinet.configureCredentials('cert/rootCA.pem','cert/priv.pem.key','cert/cert.pem.crt')
myMQTTClinet.configureAutoReconnectBackoffTime(15,180,30)
myMQTTClinet.configureOfflinePublishQueueing(-1)
myMQTTClinet.configureConnectDisconnectTimeout(10)
myMQTTClinet.configureDrainingFrequency(1)
myMQTTClinet.configureMQTTOperationTimeout(5)
myMQTTClinet.onOnline = _onOnline
myMQTTClinet.onOffline = _onOffline

#-------------------- Other setup -------------------

#logging.getLogger("AWSIoTPythonSDK.core").setLevel("DEBUG")
#logging.getLogger("AWSIoTPythonSDK.core").addHandler(logging.StreamHandler())
totalMsgToSend = 20

#-------------------- Main code ----------------------
message = 'message number (from 100): {}'  #for have a message number different from the id generated when publish

if mqttConnect():
    for i in range(100,(100+totalMsgToSend)):
        sendMsg(message.format(i))
        time.sleep(20)
    time.sleep(10)
    mqttDisconnect()    


