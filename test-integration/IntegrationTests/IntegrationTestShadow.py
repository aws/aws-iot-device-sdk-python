# This integration test verifies the functionality in the Python core of Yun/Python SDK
# for IoT shadow operations: shadowUpdate and delta.
# 1. The test generates a X-byte-long random sting and breaks it into a random
# number of chunks, with a fixed length variation from 1 byte to 10 bytes.
# 2. Two threads are created to do shadowUpdate and delta on the same device
# shadow. The update thread updates the desired state with an increasing sequence
# number and a chunk. It is terminated when there are no more chunks to be sent. 
# 3. The delta thread listens on delta topic and receives the changes in device 
# shadow JSON document. It parses out the sequence number and the chunk, then pack
# them into a dictionary with sequence number as the key and the chunk as the value.
# 4. To verify the result of the test, the random string is re-assembled for both
# the update thread and the delta thread to see if they are equal.
# 5. Since shadow operations are all QoS0 (Pub/Sub), it is still a valid case when
# the re-assembled strings are not equal. Then we need to make sure that the number
# of the missing chunks does not exceed 10% of the total number of chunk transmission
# that succeeds.

import time
import random
import string
import json
import sys
sys.path.insert(0, "./test-integration/IntegrationTests/TestToolLibrary")
sys.path.insert(0, "./test-integration/IntegrationTests/TestToolLibrary/SDKPackage")

from TestToolLibrary import simpleThreadManager
import TestToolLibrary.checkInManager as checkInManager
import TestToolLibrary.MQTTClientManager as MQTTClientManager
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.core.shadow.deviceShadow import deviceShadow
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.core.shadow.shadowManager import shadowManager
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.exception.AWSIoTExceptions import publishError
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.exception.AWSIoTExceptions import subscribeError
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.exception.AWSIoTExceptions import subscribeTimeoutException
from TestToolLibrary.skip import skip_when_match
from TestToolLibrary.skip import ModeIsALPN
from TestToolLibrary.skip import Python2VersionLowerThan
from TestToolLibrary.skip import Python3VersionLowerThan


# Global configuration
TPS = 1  # Update speed, Spectre does not tolerate high TPS shadow operations...


# Class that manages the generation and chopping of the random string
class GibberishBox:
    def __init__(self, length):
        self._content = self._generateGibberish(length)

    def getGibberish(self):
        return self._content

    # Random string generator: lower/upper case letter + digits
    def _generateGibberish(self, length):
        s = string.ascii_lowercase + string.digits + string.ascii_uppercase
        return ''.join(random.sample(s * length, length))

    # Spit out the gibberish chunk by chunk (1-10 bytes)
    def gibberishSpitter(self):
        randomLength = random.randrange(1, 11)
        ret = None
        if self._content is not None:
            ret = self._content[0:randomLength]
            self._content = self._content[randomLength:]
        return ret


# Class that manages the callback function and record of chunks for re-assembling
class callbackContainer:
    def __init__(self):
        self._internalDictionary = dict()

    def getInternalDictionary(self):
        return self._internalDictionary

    def testCallback(self, payload, type, token):
        print("Type: " + type)
        print(payload)
        print("&&&&&&&&&&&&&&&&&&&&")
        # This is the shadow delta callback, so the token should be None
        if type == "accepted":
            JsonDict = json.loads(payload)
            try:
                sequenceNumber = int(JsonDict['state']['desired']['sequenceNumber'])
                gibberishChunk = JsonDict['state']['desired']['gibberishChunk']
                self._internalDictionary[sequenceNumber] = gibberishChunk
            except KeyError as e:
                print(e.message)
                print("No such key!")
        else:
            JsonDict = json.loads(payload)
            try:
                sequenceNumber = int(JsonDict['state']['sequenceNumber'])
                gibberishChunk = JsonDict['state']['gibberishChunk']
                self._internalDictionary[sequenceNumber] = gibberishChunk
            except KeyError as e:
                print(e.message)
                print("No such key!")


# Thread runtime function
def threadShadowUpdate(deviceShadow, callback, TPS, gibberishBox, maxNumMessage):
    time.sleep(2)
    chunkSequence = 0
    while True:
        currentChunk = gibberishBox.gibberishSpitter()
        if currentChunk != "":
            outboundJsonDict = dict()
            outboundJsonDict["state"] = dict()
            outboundJsonDict["state"]["desired"] = dict()
            outboundJsonDict["state"]["desired"]["sequenceNumber"] = chunkSequence
            outboundJsonDict["state"]["desired"]["gibberishChunk"] = currentChunk
            outboundJSON = json.dumps(outboundJsonDict)
            chunkSequence += 1
            try:
                deviceShadow.shadowUpdate(outboundJSON, callback, 5)
            except publishError:
                print("Publish error!")
            except subscribeTimeoutException:
                print("Subscribe timeout!")
            except subscribeError:
                print("Subscribe error!")
            except Exception as e:
                print("Unknown exception!")
                print("Type: " + str(type(e)))
                print("Message: " + str(e.message))
            time.sleep(1 / TPS)
        else:
            break
    print("Update thread completed.")


# Re-assemble gibberish
def reAssembleGibberish(srcDict, maxNumMessage):
    ret = ""
    for i in range(0, maxNumMessage):
        try:
            ret += srcDict[i]
        except KeyError:
            pass
    return ret


# RandomShadowNameSuffix
def randomString(lengthOfString):
    return "".join(random.choice(string.ascii_lowercase) for i in range(lengthOfString))


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
clientPub = myMQTTClientManager.create_connected_mqtt_core("integrationTestMQTT_ClientPub", host, rootCA,
                                                           certificate, privateKey, mode=mode)
clientSub = myMQTTClientManager.create_connected_mqtt_core("integrationTestMQTT_ClientSub", host, rootCA,
                                                           certificate, privateKey, mode=mode)

if clientPub is None or clientSub is None:
    exit(4)

print("Two clients are connected!")

# Configurations
################
# Data
gibberishLength = myCheckInManager.customParameter
# Init device shadow instance
shadowManager1 = shadowManager(clientPub)
shadowManager2 = shadowManager(clientSub)
shadowName = "GibberChunk" + randomString(5)
deviceShadow1 = deviceShadow(shadowName, True, shadowManager1)
deviceShadow2 = deviceShadow(shadowName, True, shadowManager2)
print("Two device shadow instances are created!")

# Callbacks
callbackHome_Update = callbackContainer()
callbackHome_Delta = callbackContainer()

# Listen on delta topic
try:
    deviceShadow2.shadowRegisterDeltaCallback(callbackHome_Delta.testCallback)
except subscribeError:
    print("Subscribe error!")
except subscribeTimeoutException:
    print("Subscribe timeout!")
except Exception as e:
    print("Unknown exception!")
    print("Type: " + str(type(e)))
    print("Message: " + str(e.message))

# Init gibberishBox
cipher = GibberishBox(gibberishLength)
gibberish = cipher.getGibberish()
print("Random string: " + gibberish)

# Threads
mySimpleThreadManager = simpleThreadManager.simpleThreadManager()
updateThreadID = mySimpleThreadManager.createOneTimeThread(threadShadowUpdate,
                                                           [deviceShadow1, callbackHome_Update.testCallback, TPS,
                                                            cipher, gibberishLength])

# Performing
############
# Functionality test
mySimpleThreadManager.startThreadWithID(updateThreadID)
mySimpleThreadManager.joinOneTimeThreadWithID(updateThreadID)
time.sleep(10)  # Just in case

# Now check the gibberish
gibberishUpdateResult = reAssembleGibberish(callbackHome_Update.getInternalDictionary(), gibberishLength)
gibberishDeltaResult = reAssembleGibberish(callbackHome_Delta.getInternalDictionary(), gibberishLength)
print("Update:")
print(gibberishUpdateResult)
print("Delta:")
print(gibberishDeltaResult)
print("Origin:")
print(gibberish)

if gibberishUpdateResult != gibberishDeltaResult:
    # Since shadow operations are on QoS0 (Pub/Sub), there could be a chance
    # where incoming messages are missing on the subscribed side
    # A ratio of 95% must be guaranteed to pass this test
    dictUpdate = callbackHome_Update.getInternalDictionary()
    dictDelta = callbackHome_Delta.getInternalDictionary()
    maxBaseNumber = max(len(dictUpdate), len(dictDelta))
    diff = float(abs(len(dictUpdate) - len(dictDelta))) / maxBaseNumber
    print("Update/Delta string not equal, missing rate is: " + str(diff * 100) + "%.")
    # Largest chunk is 10 bytes, total length is X bytes.
    # Minimum number of chunks is X/10
    # Maximum missing rate = 10%
    if diff > 0.1:
        print("Missing rate too high!")
        exit(4)
