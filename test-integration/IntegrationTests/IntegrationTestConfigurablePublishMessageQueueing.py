# This integration test verifies the functionality in the Python core of Yun SDK
# for configurable offline publish message queueing.
# For each offline publish queue to be tested, it starts two threads using
# different connections to AWS IoT:
# Thread A subscribes to TopicOnly and wait to receive messages published to
# TopicOnly from ThreadB.
# Thread B publishes to TopicOnly with a manual network error which triggers the
# offline publish message queueing. According to different configurations, the
# internal queue should keep as many publish requests as configured and then
# republish them once the connection is back.
# * After the network is down but before the client gets the notification of being
# * disconnected, QoS0 messages in between this "blind-window" will be lost. However,
# * once the client gets the notification, it should start queueing messages up to
# * its queue size limit.
# * Therefore, all published messages are QoS0, we are verifying the total amount.
# * Configuration to be tested:
# 1. Limited queueing section, limited response (in-flight) section, drop oldest
# 2. Limited queueing section, limited response (in-flight) section, drop newest


import threading
import sys
import time
import random
import string
sys.path.insert(0, "./test-integration/IntegrationTests/TestToolLibrary")
sys.path.insert(0, "./test-integration/IntegrationTests/TestToolLibrary/SDKPackage")

import TestToolLibrary.checkInManager as checkInManager
import TestToolLibrary.MQTTClientManager as MQTTClientManager
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.core.util.enums import DropBehaviorTypes
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.exception.AWSIoTExceptions import publishError
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.exception.AWSIoTExceptions import publishQueueFullException
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.exception.AWSIoTExceptions import subscribeError
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.exception.AWSIoTExceptions import subscribeTimeoutException
from TestToolLibrary.skip import skip_when_match
from TestToolLibrary.skip import ModeIsALPN
from TestToolLibrary.skip import Python2VersionLowerThan
from TestToolLibrary.skip import Python3VersionLowerThan

CLIENT_ID_PUB = "integrationTestMQTT_ClientPub" + "".join(random.choice(string.ascii_lowercase) for i in range(4))
CLIENT_ID_SUB = "integrationTestMQTT_ClientSub" + "".join(random.choice(string.ascii_lowercase) for i in range(4))

# Class that implements the publishing thread: Thread A, with network failure
# This thread will publish 3 messages first, and then keep publishing
# with a network failure, and then publish another set of 3 messages
# once the connection is resumed.
# * TPS = 1
class threadPub:
    def __init__(self, pyCoreClient, numberOfOfflinePublish, srcTopic):
        self._publishMessagePool = list()
        self._pyCoreClient = pyCoreClient
        self._numberOfOfflinePublish = numberOfOfflinePublish
        self._topic = srcTopic

    # Simulate a network error
    def _manualNetworkError(self):
        # Ensure we close the socket
        if self._pyCoreClient._internal_async_client._paho_client._sock:
            self._pyCoreClient._internal_async_client._paho_client._sock.close()
            self._pyCoreClient._internal_async_client._paho_client._sock = None
        if self._pyCoreClient._internal_async_client._paho_client._ssl:
            self._pyCoreClient._internal_async_client._paho_client._ssl.close()
            self._pyCoreClient._internal_async_client._paho_client._ssl = None
        # Fake that we have detected the disconnection
        self._pyCoreClient._internal_async_client._paho_client.on_disconnect(None, None, 0)

    def _runtime(self):
        messageCount = 0
        # Publish 3 messages
        print("Thread A: Publish 3 messages.")
        step1PublishCount = 3
        while step1PublishCount != 0:
            currentMessage = str(messageCount)
            self._publishMessagePool.append(int(currentMessage))
            try:
                self._pyCoreClient.publish(self._topic, currentMessage, 0, False)
                print("Thread A: Published a message: " + str(currentMessage))
                step1PublishCount -= 1
                messageCount += 1
            except publishError:
                print("Publish Error!")
            except publishQueueFullException:
                print("Internal Publish Queue is FULL!")
            except Exception as e:
                print("Unknown exception!")
                print("Type: " + str(type(e)))
                print("Message: " + str(e.message))
            time.sleep(1)
        # Network Failure, publish #numberOfOfflinePublish# messages
        # Scanning rate = 100 TPS
        print(
        "Thread A: Simulate an network error. Keep publishing for " + str(self._numberOfOfflinePublish) + " messages.")
        step2LoopCount = self._numberOfOfflinePublish * 100
        while step2LoopCount != 0:
            self._manualNetworkError()
            if step2LoopCount % 100 == 0:
                currentMessage = str(messageCount)
                self._publishMessagePool.append(int(currentMessage))
                try:
                    self._pyCoreClient.publish(self._topic, currentMessage, 0, False)
                    print("Thread A: Published a message: " + str(currentMessage))
                except publishError:
                    print("Publish Error!")
                except Exception as e:
                    print("Unknown exception!")
                    print("Type: " + str(type(e)))
                    print("Message: " + str(e.message))
                messageCount += 1
            step2LoopCount -= 1
            time.sleep(0.01)
        # Reconnecting
        reconnectTiming = 0  # count per 0.01 seconds
        while reconnectTiming <= 1000:
            if reconnectTiming % 100 == 0:
                print("Thread A: Counting reconnect time: " + str(reconnectTiming / 100) + "seconds.")
            reconnectTiming += 1
            time.sleep(0.01)
        print("Thread A: Reconnected!")
        # Publish another set of 3 messages
        print("Thread A: Publish 3 messages again.")
        step3PublishCount = 3
        while step3PublishCount != 0:
            currentMessage = str(messageCount)
            self._publishMessagePool.append(int(currentMessage))
            try:
                self._pyCoreClient.publish(self._topic, currentMessage, 0, False)
                print("Thread A: Published a message: " + str(currentMessage))
                step3PublishCount -= 1
                messageCount += 1
            except publishError:
                print("Publish Error!")
            except Exception as e:
                print("Unknown exception!")
                print("Type: " + str(type(e)))
                print("Message: " + str(e.message))
            time.sleep(1)
        # Wrap up: Sleep for extra 5 seconds
        time.sleep(5)

    def startThreadAndGo(self):
        threadHandler = threading.Thread(target=self._runtime)
        threadHandler.start()
        return threadHandler

    def getPublishMessagePool(self):
        return self._publishMessagePool


# Class that implements the subscribing thread: Thread B.
# Basically this thread does nothing but subscribes to TopicOnly and keeps receiving messages.
class threadSub:
    def __init__(self, pyCoreClient, srcTopic):
        self._keepRunning = True
        self._pyCoreClient = pyCoreClient
        self._subscribeMessagePool = list()
        self._topic = srcTopic

    def _messageCallback(self, client, userdata, message):
        print("Thread B: Received a new message from topic: " + str(message.topic))
        print("Thread B: Payload is: " + str(message.payload))
        self._subscribeMessagePool.append(int(message.payload))

    def _runtime(self):
        # Subscribe to self._topic
        try:
            self._pyCoreClient.subscribe(self._topic, 1, self._messageCallback)
        except subscribeTimeoutException:
            print("Subscribe timeout!")
        except subscribeError:
            print("Subscribe error!")
        except Exception as e:
            print("Unknown exception!")
            print("Type: " + str(type(e)))
            print("Message: " + str(e.message))
        time.sleep(2.2)
        print("Thread B: Subscribed to " + self._topic)
        print("Thread B: Now wait for Thread A.")
        # Scanning rate is 100 TPS
        while self._keepRunning:
            time.sleep(0.01)

    def startThreadAndGo(self):
        threadHandler = threading.Thread(target=self._runtime)
        threadHandler.start()
        return threadHandler

    def stopRunning(self):
        self._keepRunning = False

    def getSubscribeMessagePool(self):
        return self._subscribeMessagePool


# Generate answer for this integration test using queue configuration
def generateAnswer(data, queueingSize, srcMode):
    dataInWork = sorted(data)
    dataHead = dataInWork[:3]
    dataTail = dataInWork[-3:]
    dataRet = dataHead
    dataInWork = dataInWork[3:]
    dataInWork = dataInWork[:-3]
    if srcMode == 0:  # DROP_OLDEST
        dataInWork = dataInWork[(-1 * queueingSize):]
        dataRet.extend(dataInWork)
        dataRet.extend(dataTail)
        return sorted(dataRet)
    elif srcMode == 1:  # DROP_NEWEST
        dataInWork = dataInWork[:queueingSize]
        dataRet.extend(dataInWork)
        dataRet.extend(dataTail)
        return sorted(dataRet)
    else:
        print("Unsupported drop behavior!")
        raise ValueError


# Create thread object, load in pyCoreClient and perform the set of integration tests
def performConfigurableOfflinePublishQueueTest(clientPub, clientSub):
    print("Test DROP_NEWEST....")
    clientPub[0].configure_offline_requests_queue(10, DropBehaviorTypes.DROP_NEWEST)  # dropNewest
    clientSub[0].configure_offline_requests_queue(10, DropBehaviorTypes.DROP_NEWEST)  # dropNewest
    # Create Topics
    TopicOnly = "TopicOnly/" + "".join(random.choice(string.ascii_lowercase) for i in range(4))
    # Create thread object
    threadPubObject = threadPub(clientPub[0], 15, TopicOnly)  # Configure to publish 15 messages during network outage
    threadSubObject = threadSub(clientSub[0], TopicOnly)
    threadSubHandler = threadSubObject.startThreadAndGo()
    time.sleep(3)
    threadPubHandler = threadPubObject.startThreadAndGo()
    threadPubHandler.join()
    threadSubObject.stopRunning()
    threadSubHandler.join()
    # Verify result
    print("Verify DROP_NEWEST:")
    answer = generateAnswer(threadPubObject.getPublishMessagePool(), 10, 1)
    print("ANSWER:")
    print(answer)
    print("ACTUAL:")
    print(threadSubObject.getSubscribeMessagePool())
    # We are doing QoS0 publish. We cannot guarantee when the drop will happen since we cannot guarantee a fixed time out
    # of disconnect detection. However, once offline requests queue starts involving, it should queue up to its limit,
    # thus the total number of received messages after draining should always match.
    if len(threadSubObject.getSubscribeMessagePool()) == len(answer):
        print("Passed.")
    else:
        print("Verify DROP_NEWEST failed!!!")
        return False
    time.sleep(5)
    print("Test DROP_OLDEST....")
    clientPub[0].configure_offline_requests_queue(10, DropBehaviorTypes.DROP_OLDEST)  # dropOldest
    clientSub[0].configure_offline_requests_queue(10, DropBehaviorTypes.DROP_OLDEST)  # dropOldest
    # Create thread object
    threadPubObject = threadPub(clientPub[0], 15, TopicOnly)  # Configure to publish 15 messages during network outage
    threadSubObject = threadSub(clientSub[0], TopicOnly)
    threadSubHandler = threadSubObject.startThreadAndGo()
    time.sleep(3)
    threadPubHandler = threadPubObject.startThreadAndGo()
    threadPubHandler.join()
    threadSubObject.stopRunning()
    threadSubHandler.join()
    # Verify result
    print("Verify DROP_OLDEST:")
    answer = generateAnswer(threadPubObject.getPublishMessagePool(), 10, 0)
    print(answer)
    print("ACTUAL:")
    print(threadSubObject.getSubscribeMessagePool())
    if len(threadSubObject.getSubscribeMessagePool()) == len(answer):
        print("Passed.")
    else:
        print("Verify DROP_OLDEST failed!!!")
        return False
    return True


# Check inputs
myCheckInManager = checkInManager.checkInManager(2)
myCheckInManager.verify(sys.argv)

host = myCheckInManager.host
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

# Functionality test
if not performConfigurableOfflinePublishQueueTest([clientPub], [clientSub]):
    print("The above Drop behavior broken!")
    exit(4)
