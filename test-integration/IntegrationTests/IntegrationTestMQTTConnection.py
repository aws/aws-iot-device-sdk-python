# This integration test verifies the functionality in the Python core of IoT Yun/Python SDK
# for basic MQTT connection.
# It starts two threads using two different connections to AWS IoT:
# Thread A: publish to "deviceSDK/PyIntegrationTest/Topic", X messages, QoS1, TPS=50
# Thread B: subscribe to "deviceSDK/PyIntegrationTest/Topic", QoS1
# Thread B will be started first with extra delay to ensure a valid subscription
# Then thread A will be started.
# Verify send/receive messages are equivalent


import random
import string
import time
import sys
sys.path.insert(0, "./test-integration/IntegrationTests/TestToolLibrary")
sys.path.insert(0, "./test-integration/IntegrationTests/TestToolLibrary/SDKPackage")

from TestToolLibrary import simpleThreadManager
import TestToolLibrary.checkInManager as checkInManager
import TestToolLibrary.MQTTClientManager as MQTTClientManager
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.exception.AWSIoTExceptions import publishError
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.exception.AWSIoTExceptions import subscribeError
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.exception.AWSIoTExceptions import subscribeTimeoutException
from TestToolLibrary.skip import skip_when_match
from TestToolLibrary.skip import ModeIsALPN
from TestToolLibrary.skip import Python2VersionLowerThan
from TestToolLibrary.skip import Python3VersionLowerThan


API_TYPE_SYNC = "sync"
API_TYPE_ASYNC = "async"

CLIENT_ID_PUB = "integrationTestMQTT_ClientPub" + "".join(random.choice(string.ascii_lowercase) for i in range(4))
CLIENT_ID_SUB = "integrationTestMQTT_ClientSub" + "".join(random.choice(string.ascii_lowercase) for i in range(4))



# Callback unit for subscribe
class callbackUnit:
    def __init__(self, srcSet, apiType):
        self._internalSet = srcSet
        self._apiType = apiType

    # Callback for clientSub
    def messageCallback(self, client, userdata, message):
        print(self._apiType + ": Received a new message: " + str(message.payload))
        self._internalSet.add(message.payload.decode('utf-8'))

    def getInternalSet(self):
        return self._internalSet


# Run function unit
class runFunctionUnit:
    def __init__(self, apiType):
        self._messagesPublished = set()
        self._apiType = apiType

    # Run function for publish thread (one time)
    def threadPublish(self, pyCoreClient, numberOfTotalMessages, topic, TPS):
        # One time thread
        time.sleep(3)  # Extra waiting time for valid subscription
        messagesLeftToBePublished = numberOfTotalMessages
        while messagesLeftToBePublished != 0:
            try:
                currentMessage = str(messagesLeftToBePublished)
                self._performPublish(pyCoreClient, topic, 1, currentMessage)
                self._messagesPublished.add(currentMessage)
            except publishError:
                print("Publish Error for message: " + currentMessage)
            except Exception as e:
                print("Unknown exception: " + str(type(e)) + " " + str(e.message))
            messagesLeftToBePublished -= 1
            time.sleep(1 / float(TPS))
        print("End of publish thread.")

    def _performPublish(self, pyCoreClient, topic, qos, payload):
        if self._apiType == API_TYPE_SYNC:
            pyCoreClient.publish(topic, payload, qos, False)
        if self._apiType == API_TYPE_ASYNC:
            pyCoreClient.publish_async(topic, payload, qos, False, None) # TODO: See if we can also check PUBACKs


############################################################################
# Main #
# Check inputs
myCheckInManager = checkInManager.checkInManager(2)
myCheckInManager.verify(sys.argv)

host = "ajje7lpljulm4-ats.iot.us-east-1.amazonaws.com"
rootCA = "./test-integration/Credentials/rootCA.crt"
certificate = "./test-integration/Credentials/certificate.pem.crt"
privateKey = "./test-integration/Credentials/privateKey.pem.key"
mode = myCheckInManager.mode

skip_when_match(ModeIsALPN(mode).And(
    Python2VersionLowerThan((2, 7, 10)).Or(Python3VersionLowerThan((3, 5, 0)))
), "This test is not applicable for mode %s and Python verison %s. Skipping..." % (mode, sys.version_info[:3]))

# Init Python core and connect
myMQTTClientManager = MQTTClientManager.MQTTClientManager()
clientPub = myMQTTClientManager.create_connected_mqtt_core(CLIENT_ID_PUB, host, rootCA,
                                                           certificate, privateKey, mode=mode)
clientSub = myMQTTClientManager.create_connected_mqtt_core(CLIENT_ID_SUB, host, rootCA,
                                                           certificate, privateKey, mode=mode)

if clientPub is None or clientSub is None:
    exit(4)

print("Two clients are connected!")

# Configurations
################
# Data/Data pool
TPS = 20
numberOfTotalMessagesAsync = myCheckInManager.customParameter
numberOfTotalMessagesSync = numberOfTotalMessagesAsync / 10
subSetAsync = set()
subSetSync = set()
subCallbackUnitAsync = callbackUnit(subSetAsync, API_TYPE_ASYNC)
subCallbackUnitSync = callbackUnit(subSetSync, API_TYPE_SYNC)
syncTopic = "YunSDK/PyIntegrationTest/Topic/sync" + "".join(random.choice(string.ascii_lowercase) for i in range(4))
print(syncTopic)
asyncTopic = "YunSDK/PyIntegrationTest/Topic/async" + "".join(random.choice(string.ascii_lowercase) for j in range(4))
# clientSub
try:
    clientSub.subscribe(asyncTopic, 1, subCallbackUnitAsync.messageCallback)
    clientSub.subscribe(syncTopic, 1, subCallbackUnitSync.messageCallback)
    time.sleep(3)
except subscribeTimeoutException:
    print("Subscribe timeout!")
except subscribeError:
    print("Subscribe error!")
except Exception as e:
    print("Unknown exception!")
    print("Type: " + str(type(e)))
    print("Message: " + str(e.message))
# Threads
mySimpleThreadManager = simpleThreadManager.simpleThreadManager()
myRunFunctionUnitSyncPub = runFunctionUnit(API_TYPE_SYNC)
myRunFunctionUnitAsyncPub = runFunctionUnit(API_TYPE_ASYNC)
publishSyncThreadID = mySimpleThreadManager.createOneTimeThread(myRunFunctionUnitSyncPub.threadPublish,
                                                                [clientPub, numberOfTotalMessagesSync, syncTopic, TPS])
publishAsyncThreadID = mySimpleThreadManager.createOneTimeThread(myRunFunctionUnitAsyncPub.threadPublish,
                                                                 [clientPub, numberOfTotalMessagesAsync, asyncTopic, TPS])

# Performing
############
mySimpleThreadManager.startThreadWithID(publishSyncThreadID)
mySimpleThreadManager.startThreadWithID(publishAsyncThreadID)
mySimpleThreadManager.joinOneTimeThreadWithID(publishSyncThreadID)
mySimpleThreadManager.joinOneTimeThreadWithID(publishAsyncThreadID)
time.sleep(numberOfTotalMessagesAsync / float(TPS) * 0.5)

# Verifying
###########
# Length
print("Check if the length of the two sets are equal...")
print("Received from subscription (sync pub): " + str(len(subCallbackUnitSync.getInternalSet())))
print("Received from subscription (async pub): " + str(len(subCallbackUnitAsync.getInternalSet())))
print("Sent through sync publishes: " + str(len(myRunFunctionUnitSyncPub._messagesPublished)))
print("Sent through async publishes: " + str(len(myRunFunctionUnitAsyncPub._messagesPublished)))
if len(myRunFunctionUnitSyncPub._messagesPublished) != len(subCallbackUnitSync.getInternalSet()):
    print("[Sync pub] Number of messages not equal!")
    exit(4)
if len(myRunFunctionUnitAsyncPub._messagesPublished) != len(subCallbackUnitAsync.getInternalSet()):
    print("[Asyn pub] Number of messages not equal!")
    exit(4)
# Content
print("Check if the content if the two sets are equivalent...")
if myRunFunctionUnitSyncPub._messagesPublished != subCallbackUnitSync.getInternalSet():
    print("[Sync pub] Set content not equal!")
    exit(4)
elif myRunFunctionUnitAsyncPub._messagesPublished != subCallbackUnitAsync.getInternalSet():
    print("[Async pub] Set content not equal!")
else:
    print("Yes!")
