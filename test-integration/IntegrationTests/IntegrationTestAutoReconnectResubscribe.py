# This integration test verifies the functionality in the Python core of Yun/Python SDK
# for auto-reconnect and auto-resubscribe.
# It starts two threads using two different connections to AWS IoT:
# Thread A publishes 10 messages to topicB first, then quiet for a while, and finally
# publishes another 10 messages to topicB.
# Thread B subscribes to topicB and waits to receive messages. Once it receives the first
# 10 messages. It simulates a network error, disconnecting from the broker. In a short time,
# it should automatically reconnect and resubscribe to the previous topic and be able to
# receive the next 10 messages from thread A.
# Because of auto-reconnect/resubscribe, thread B should be able to receive all of the
# messages from topicB published by thread A without calling subscribe again in user code 
# explicitly.


import random
import string
import sys
import time
sys.path.insert(0, "./test-integration/IntegrationTests/TestToolLibrary")
sys.path.insert(0, "./test-integration/IntegrationTests/TestToolLibrary/SDKPackage")

import TestToolLibrary.checkInManager as checkInManager
import TestToolLibrary.MQTTClientManager as MQTTClientManager
from TestToolLibrary import simpleThreadManager
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.exception.AWSIoTExceptions import publishError
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.exception.AWSIoTExceptions import subscribeError
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.exception.AWSIoTExceptions import subscribeTimeoutException
from TestToolLibrary.skip import skip_when_match
from TestToolLibrary.skip import ModeIsALPN
from TestToolLibrary.skip import Python2VersionLowerThan
from TestToolLibrary.skip import Python3VersionLowerThan

CLIENT_ID_PUB = "integrationTestMQTT_ClientPub" + "".join(random.choice(string.ascii_lowercase) for i in range(4))
CLIENT_ID_SUB = "integrationTestMQTT_ClientSub" + "".join(random.choice(string.ascii_lowercase) for i in range(4))

# Callback unit
class callbackUnit:
    def __init__(self):
        self._internalSet = set()

    # Callback fro clientSub
    def messageCallback(self, client, userdata, message):
        print("Received a new message: " + str(message.payload))
        self._internalSet.add(message.payload.decode('utf-8'))

    def getInternalSet(self):
        return self._internalSet


# Simulate a network error
def manualNetworkError(srcPyMQTTCore):
    # Ensure we close the socket
    if srcPyMQTTCore._internal_async_client._paho_client._sock:
        srcPyMQTTCore._internal_async_client._paho_client._sock.close()
        srcPyMQTTCore._internal_async_client._paho_client._sock = None
    if srcPyMQTTCore._internal_async_client._paho_client._ssl:
        srcPyMQTTCore._internal_async_client._paho_client._ssl.close()
        srcPyMQTTCore._internal_async_client._paho_client._ssl = None
    # Fake that we have detected the disconnection
    srcPyMQTTCore._internal_async_client._paho_client.on_disconnect(None, None, 0)


# runFunctionUnit
class runFunctionUnit():
    def __init__(self):
        self._messagesPublished = set()
        self._topicB = "topicB/" + "".join(random.choice(string.ascii_lowercase) for i in range(4))

    # ThreadA runtime function:
    # 1. Publish 10 messages to topicB.
    # 2. Take a nap: 20 sec
    # 3. Publish another 10 messages to topicB.
    def threadARuntime(self, pyCoreClient):
        time.sleep(3)  # Ensure a valid subscription
        messageCount = 0
        # First 10 messages
        while messageCount < 10:
            try:
                pyCoreClient.publish(self._topicB, str(messageCount), 1, False)
                self._messagesPublished.add(str(messageCount))
            except publishError:
                print("Publish error!")
            except Exception as e:
                print("Unknown exception!")
                print("Type: " + str(type(e)))
                print("Message: " + str(e.message))
            messageCount += 1
            time.sleep(0.5)  # TPS = 2
        # Take a nap
        time.sleep(20)
        # Second 10 messages
        while messageCount < 20:
            try:
                pyCoreClient.publish(self._topicB, str(messageCount), 1, False)
                self._messagesPublished.add(str(messageCount))
            except publishError:
                print("Publish Error!")
            except Exception as e:
                print("Unknown exception!")
                print("Type: " + str(type(e)))
                print("Message: " + str(e.message))
            messageCount += 1
            time.sleep(0.5)
        print("Publish thread terminated.")

    # ThreadB runtime function:
    # 1. Subscribe to topicB
    # 2. Wait for a while
    # 3. Create network blocking, triggering auto-reconnect and auto-resubscribe
    # 4. On connect, wait for another while
    def threadBRuntime(self, pyCoreClient, callback):
        try:
            # Subscribe to topicB
            pyCoreClient.subscribe(self._topicB, 1, callback)
        except subscribeTimeoutException:
            print("Subscribe timeout!")
        except subscribeError:
            print("Subscribe error!")
        except Exception as e:
            print("Unknown exception!")
            print("Type: " + str(type(e)))
            print("Message: " + str(e.message))
        # Wait to get the first 10 messages from thread A
        time.sleep(10)
        # Block the network for 3 sec
        print("Block the network for 3 sec...")
        blockingTimeTenMs = 300
        while blockingTimeTenMs != 0:
            manualNetworkError(pyCoreClient)
            blockingTimeTenMs -= 1
            time.sleep(0.01)
        print("Leave it to the main thread to keep waiting...")


############################################################################
# Main #
# Check inputs
myCheckInManager = checkInManager.checkInManager(1)
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
    print("Clients not init!")
    exit(4)

print("Two clients are connected!")

# Configurations
################
# Callback unit
subCallbackUnit = callbackUnit()
# Threads
mySimpleThreadManager = simpleThreadManager.simpleThreadManager()
myRunFunctionUnit = runFunctionUnit()
publishThreadID = mySimpleThreadManager.createOneTimeThread(myRunFunctionUnit.threadARuntime, [clientPub])
subscribeThreadID = mySimpleThreadManager.createOneTimeThread(myRunFunctionUnit.threadBRuntime,
                                                              [clientSub, subCallbackUnit.messageCallback])

# Performing
############
mySimpleThreadManager.startThreadWithID(subscribeThreadID)
mySimpleThreadManager.startThreadWithID(publishThreadID)
mySimpleThreadManager.joinOneTimeThreadWithID(subscribeThreadID)
mySimpleThreadManager.joinOneTimeThreadWithID(publishThreadID)
time.sleep(3)  # Just in case messages arrive slowly

# Verifying
###########
# Length
print("Check if the length of the two sets are equal...")
print("Received from subscription: " + str(len(subCallbackUnit.getInternalSet())))
print("Sent through publishes: " + str(len(myRunFunctionUnit._messagesPublished)))
if len(myRunFunctionUnit._messagesPublished) != len(subCallbackUnit.getInternalSet()):
    print("Number of messages not equal!")
    exit(4)
# Content
print("Check if the content if the two sets are equivalent...")
if myRunFunctionUnit._messagesPublished != subCallbackUnit.getInternalSet():
    print("Sent through publishes:")
    print(myRunFunctionUnit._messagesPublished)
    print("Received from subscription:")
    print(subCallbackUnit.getInternalSet())
    print("Set content not equal!")
    exit(4)
else:
    print("Yes!")
