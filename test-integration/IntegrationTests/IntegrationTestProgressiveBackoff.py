# This integration test verifies the functionality in the Python core of Yun/Python SDK
# for progressive backoff logic in auto-reconnect.
# It starts two threads using two different connections to AWS IoT:
# Thread B subscribes to "coolTopic" and waits for incoming messages. Network
# failure will happen occasionally in thread B with a variant interval (connected
# period), simulating stable/unstable connection so as to test the reset logic of
# backoff timing. Once thread B is back online, an internal flag will be set to
# notify the other thread, Thread A, to start publishing to the same topic.
# Thread A will publish a set of messages (a fixed number of messages) to "coolTopic"
# using QoS1 and does nothing in the rest of the time. It will only start publishing
# when it gets ready notification from thread B. No network failure will happen in 
# thread A.
# Because thread A is always online and only publishes when thread B is back online,
# all messages published to "coolTopic" should be received by thread B. In meantime,
# thread B should have an increasing amount of backoff waiting period until the
# connected period reaches the length of time for a stable connection. After that,
# the backoff waiting period should be reset.
# The following things will be verified to pass the test:
# 1. All messages are received.
# 2. Backoff waiting period increases as configured before the thread reaches to a
# stable connection.
# 3. Backoff waiting period does not exceed the maximum allowed time.
# 4. Backoff waiting period is reset after the thread reaches to a stable connection.


import string
import random
import time
import threading
import sys
sys.path.insert(0, "./test-integration/IntegrationTests/TestToolLibrary")
sys.path.insert(0, "./test-integration/IntegrationTests/TestToolLibrary/SDKPackage")

from TestToolLibrary import simpleThreadManager
import TestToolLibrary.checkInManager as checkInManager
import TestToolLibrary.MQTTClientManager as MQTTClientManager
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.exception.AWSIoTExceptions import publishError
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.exception.AWSIoTExceptions import subscribeError
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.exception.AWSIoTExceptions import subscribeTimeoutException
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.core.protocol.internal.clients import ClientStatus
from TestToolLibrary.skip import skip_when_match
from TestToolLibrary.skip import ModeIsALPN
from TestToolLibrary.skip import Python2VersionLowerThan
from TestToolLibrary.skip import Python3VersionLowerThan

CLIENT_ID_PUB = "integrationTestMQTT_ClientPub" + "".join(random.choice(string.ascii_lowercase) for i in range(4))
CLIENT_ID_SUB = "integrationTestMQTT_ClientSub" + "".join(random.choice(string.ascii_lowercase) for i in range(4))

# Class that implements all the related threads in the test in a controllable manner
class threadPool:
    def __init__(self, srcTotalNumberOfNetworkFailure, clientPub, clientSub):
        self._threadBReadyFlag = 0  # 0-Not connected, 1-Connected+Subscribed, -1-ShouldExit
        self._threadBReadyFlagMutex = threading.Lock()
        self._targetedTopic = "coolTopic" + "".join(random.choice(string.ascii_lowercase) for i in range(4))
        self._publishMessagePool = set()
        self._receiveMessagePool = set()
        self._roundOfNetworkFailure = 1
        self._totalNumberOfNetworkFailure = srcTotalNumberOfNetworkFailure
        self._clientPub = clientPub
        self._clientSub = clientSub
        self._pubCount = 0
        self._reconnectTimeRecord = list()
        self._connectedTimeRecord = list()

    # Message callback for collecting incoming messages from the subscribed topic
    def _messageCallback(self, client, userdata, message):
        print("Thread B: Received new message: " + str(message.payload))
        self._receiveMessagePool.add(message.payload.decode('utf-8'))

    # The one that publishes
    def threadARuntime(self):
        exitNow = False
        while not exitNow:
            self._threadBReadyFlagMutex.acquire()
            # Thread A is still reconnecting, WAIT!
            if self._threadBReadyFlag == 0:
                pass
            # Thread A is connected and subscribed, PUBLISH!
            elif self._threadBReadyFlag == 1:
                self._publish3Messages()
                self._threadBReadyFlag = 0  # Reset the readyFlag
            # Thread A has finished all rounds of network failure/reconnect, EXIT!
            else:
                exitNow = True
            self._threadBReadyFlagMutex.release()
            time.sleep(0.01)  # 0.01 sec scanning

    # Publish a set of messages: 3
    def _publish3Messages(self):
        loopCount = 3
        while loopCount != 0:
            try:
                currentMessage = "Message" + str(self._pubCount)
                print("Test publish to topic : " + self._targetedTopic)
                self._clientPub.publish(self._targetedTopic, currentMessage, 1, False)
                print("Thread A: Published new message: " + str(currentMessage))
                self._publishMessagePool.add(currentMessage)
                self._pubCount += 1
                loopCount -= 1
            except publishError:
                print("Publish error!")
            except Exception as e:
                print("Unknown exception!")
                print("Type: " + str(type(e)))
                print("Message: " + str(e.message))
            time.sleep(0.5)

    # The one that subscribes and has network failures
    def threadBRuntime(self):
        # Subscribe to the topic
        try:
            print("Test subscribe to topic : " + self._targetedTopic)
            self._clientSub.subscribe(self._targetedTopic, 1, self._messageCallback)
        except subscribeTimeoutException:
            print("Subscribe timeout!")
        except subscribeError:
            print("Subscribe error!")
        except Exception as e:
            print("Unknown exception!")
            print("Type: " + str(type(e)))
            print("Message: " + str(e.message))
        print("Thread B: Subscribe request sent. Staring waiting for subscription processing...")
        time.sleep(3)
        print("Thread B: Done waiting.")
        self._threadBReadyFlagMutex.acquire()
        self._threadBReadyFlag = 1
        self._threadBReadyFlagMutex.release()
        # Start looping with network failure
        connectedPeriodSecond = 3
        while self._roundOfNetworkFailure <= self._totalNumberOfNetworkFailure:
            self._connectedTimeRecord.append(connectedPeriodSecond)
            # Wait for connectedPeriodSecond
            print("Thread B: Connected time: " + str(connectedPeriodSecond) + " seconds.")
            print("Thread B: Stable time: 60 seconds.")
            time.sleep(connectedPeriodSecond)
            print("Thread B: Network failure. Round: " + str(self._roundOfNetworkFailure) + ". 0.5 seconds.")
            print("Thread B: Backoff time for this round should be: " + str(
                self._clientSub._internal_async_client._paho_client._backoffCore._currentBackoffTimeSecond) + " second(s).")
            # Set the readyFlag
            self._threadBReadyFlagMutex.acquire()
            self._threadBReadyFlag = 0
            self._threadBReadyFlagMutex.release()
            # Now lose connection for 0.5 seconds, preventing multiple reconnect attempts
            loseConnectionLoopCount = 50
            while loseConnectionLoopCount != 0:
                self._manualNetworkError()
                loseConnectionLoopCount -= 1
                time.sleep(0.01)
            # Wait until the connection/subscription is recovered
            reconnectTiming = 0
            while self._clientSub._client_status.get_status() != ClientStatus.STABLE:
                time.sleep(0.01)
                reconnectTiming += 1
                if reconnectTiming % 100 == 0:
                    print("Thread B: Counting reconnect time: " + str(reconnectTiming / 100) + " seconds.")
            print("Thread B: Counting reconnect time result: " + str(float(reconnectTiming) / 100) + " seconds.")
            self._reconnectTimeRecord.append(reconnectTiming / 100)

            time.sleep(3)  # For valid subscription

            # Update thread B status
            self._threadBReadyFlagMutex.acquire()
            self._threadBReadyFlag = 1
            self._threadBReadyFlagMutex.release()

            # Update connectedPeriodSecond
            connectedPeriodSecond += (2 ** (self._roundOfNetworkFailure - 1))
            # Update roundOfNetworkFailure
            self._roundOfNetworkFailure += 1

        # Notify thread A shouldExit
        self._threadBReadyFlagMutex.acquire()
        self._threadBReadyFlag = -1
        self._threadBReadyFlagMutex.release()

    # Simulate a network error
    def _manualNetworkError(self):
        # Only the subscriber needs the network error
        if self._clientSub._internal_async_client._paho_client._sock:
            self._clientSub._internal_async_client._paho_client._sock.close()
            self._clientSub._internal_async_client._paho_client._sock = None
        if self._clientSub._internal_async_client._paho_client._ssl:
            self._clientSub._internal_async_client._paho_client._ssl.close()
            self._clientSub._internal_async_client._paho_client._ssl = None
        # Fake that we have detected the disconnection
        self._clientSub._internal_async_client._paho_client.on_disconnect(None, None, 0)

    def getReconnectTimeRecord(self):
        return self._reconnectTimeRecord

    def getConnectedTimeRecord(self):
        return self._connectedTimeRecord


# Generate the correct backoff timing to compare the test result with
def generateCorrectAnswer(baseTime, maximumTime, stableTime, connectedTimeRecord):
    answer = list()
    currentTime = baseTime
    nextTime = baseTime
    for i in range(0, len(connectedTimeRecord)):
        if connectedTimeRecord[i] >= stableTime or i == 0:
            currentTime = baseTime
        else:
            currentTime = min(currentTime * 2, maximumTime)
        answer.append(currentTime)
    return answer


# Verify backoff time
# Corresponding element should have no diff or a bias greater than 1.5
def verifyBackoffTime(answerList, resultList):
    result = True
    for i in range(0, len(answerList)):
        if abs(answerList[i] - resultList[i]) > 1.5:
            result = False
            break
    return result


############################################################################
# Main #
# Check inputs
myCheckInManager = checkInManager.checkInManager(3)
myCheckInManager.verify(sys.argv)

#host via describe-endpoint on this OdinMS: com.amazonaws.iot.device.sdk.credentials.testing.websocket
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

# Extra configuration for clients
clientPub.configure_reconnect_back_off(1, 16, 60)
clientSub.configure_reconnect_back_off(1, 16, 60)

print("Two clients are connected!")

# Configurations
################
# Custom parameters
NumberOfNetworkFailure = myCheckInManager.customParameter
# ThreadPool object
threadPoolObject = threadPool(NumberOfNetworkFailure, clientPub, clientSub)
# Threads
mySimpleThreadManager = simpleThreadManager.simpleThreadManager()
threadAID = mySimpleThreadManager.createOneTimeThread(threadPoolObject.threadARuntime, [])
threadBID = mySimpleThreadManager.createOneTimeThread(threadPoolObject.threadBRuntime, [])

# Performing
############
mySimpleThreadManager.startThreadWithID(threadBID)
mySimpleThreadManager.startThreadWithID(threadAID)
mySimpleThreadManager.joinOneTimeThreadWithID(threadBID)
mySimpleThreadManager.joinOneTimeThreadWithID(threadAID)

# Verifying
###########
print("Verify that all messages are received...")
if threadPoolObject._publishMessagePool == threadPoolObject._receiveMessagePool:
    print("Passed. Recv/Pub: " + str(len(threadPoolObject._receiveMessagePool)) + "/" + str(
        len(threadPoolObject._publishMessagePool)))
else:
    print("Not all messages are received!")
    exit(4)
print("Verify reconnect backoff time record...")
print("ConnectedTimeRecord: " + str(threadPoolObject.getConnectedTimeRecord()))
print("ReconnectTimeRecord: " + str(threadPoolObject.getReconnectTimeRecord()))
print("Answer: " + str(generateCorrectAnswer(1, 16, 60, threadPoolObject.getConnectedTimeRecord())))
if verifyBackoffTime(generateCorrectAnswer(1, 16, 60, threadPoolObject.getConnectedTimeRecord()),
                     threadPoolObject.getReconnectTimeRecord()):
    print("Passed.")
else:
    print("Backoff time does not match theoretical value!")
    exit(4)
