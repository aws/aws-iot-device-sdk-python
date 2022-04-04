# This integration test verifies the functionality of asynchronous API for plain MQTT operations, as well as general
# notification callbacks. There are 2 phases for this test:
# a) Testing async APIs + onMessage general notification callback
# b) Testing onOnline, onOffline notification callbacks
# To achieve test goal a) and b), the client will follow the routine described below:
# 1. Client does async connect to AWS IoT and captures the CONNACK event and onOnline callback event in the record
# 2. Client does async subscribe to a topic and captures the SUBACK event in the record
# 3. Client does several async publish (QoS1) to the same topic and captures the PUBACK event in the record
# 4. Since client subscribes and publishes to the same topic, onMessage callback should be triggered. We capture these
# events as well in the record.
# 5. Client does async disconnect. This would trigger the offline callback and disconnect event callback. We capture
# them in the record.
# We should be able to receive all ACKs for all operations and corresponding general notification callback triggering
# events.


import random
import string
import time
import sys
sys.path.insert(0, "./test-integration/IntegrationTests/TestToolLibrary")
sys.path.insert(0, "./test-integration/IntegrationTests/TestToolLibrary/SDKPackage")

from TestToolLibrary.checkInManager import checkInManager
from TestToolLibrary.MQTTClientManager import MQTTClientManager
from TestToolLibrary.skip import skip_when_match
from TestToolLibrary.skip import ModeIsALPN
from TestToolLibrary.skip import Python2VersionLowerThan
from TestToolLibrary.skip import Python3VersionLowerThan


TOPIC = "topic/test/async_cb/"
MESSAGE_PREFIX = "MagicMessage-"
NUMBER_OF_PUBLISHES = 3
HOST = "ajje7lpljulm4-ats.iot.us-east-1.amazonaws.com"
ROOT_CA = "./test-integration/Credentials/rootCA.crt"
CERT = "./test-integration/Credentials/certificate.pem.crt"
KEY = "./test-integration/Credentials/privateKey.pem.key"
CLIENT_ID = "PySdkIntegTest_AsyncAPI_Callbacks"

KEY_ON_ONLINE = "OnOnline"
KEY_ON_OFFLINE = "OnOffline"
KEY_ON_MESSAGE = "OnMessage"
KEY_CONNACK = "Connack"
KEY_DISCONNECT = "Disconnect"
KEY_PUBACK = "Puback"
KEY_SUBACK = "Suback"
KEY_UNSUBACK = "Unsuback"


class CallbackManager(object):

    def __init__(self):
        self.callback_invocation_record = {
            KEY_ON_ONLINE : 0,
            KEY_ON_OFFLINE : 0,
            KEY_ON_MESSAGE : 0,
            KEY_CONNACK : 0,
            KEY_DISCONNECT : 0,
            KEY_PUBACK : 0,
            KEY_SUBACK : 0,
            KEY_UNSUBACK : 0
        }

    def on_online(self):
        print("OMG, I am online!")
        self.callback_invocation_record[KEY_ON_ONLINE] += 1

    def on_offline(self):
        print("OMG, I am offline!")
        self.callback_invocation_record[KEY_ON_OFFLINE] += 1

    def on_message(self, message):
        print("OMG, I got a message!")
        self.callback_invocation_record[KEY_ON_MESSAGE] += 1

    def connack(self, mid, data):
        print("OMG, I got a connack!")
        self.callback_invocation_record[KEY_CONNACK] += 1

    def disconnect(self, mid, data):
        print("OMG, I got a disconnect!")
        self.callback_invocation_record[KEY_DISCONNECT] += 1

    def puback(self, mid):
        print("OMG, I got a puback!")
        self.callback_invocation_record[KEY_PUBACK] += 1

    def suback(self, mid, data):
        print("OMG, I got a suback!")
        self.callback_invocation_record[KEY_SUBACK] += 1

    def unsuback(self, mid):
        print("OMG, I got an unsuback!")
        self.callback_invocation_record[KEY_UNSUBACK] += 1


def get_random_string(length):
    return "".join(random.choice(string.ascii_lowercase) for i in range(length))


############################################################################
# Main #
# Check inputs
my_check_in_manager = checkInManager(1)
my_check_in_manager.verify(sys.argv)
mode = my_check_in_manager.mode

skip_when_match(ModeIsALPN(mode).And(
    Python2VersionLowerThan((2, 7, 10)).Or(Python3VersionLowerThan((3, 5, 0)))
), "This test is not applicable for mode %s and Python verison %s. Skipping..." % (mode, sys.version_info[:3]))

# Performing
############
print("Connecting...")
callback_manager = CallbackManager()
sdk_mqtt_client = MQTTClientManager()\
    .create_nonconnected_mqtt_client(mode, CLIENT_ID, HOST, (ROOT_CA, CERT, KEY), callback_manager)
sdk_mqtt_client.connectAsync(keepAliveIntervalSecond=1, ackCallback=callback_manager.connack)  # Add callback
print("Wait some time to make sure we are connected...")
time.sleep(10)  # 10 sec

topic = TOPIC + get_random_string(4)
print("Subscribing to topic: " + topic)
sdk_mqtt_client.subscribeAsync(topic, 1, ackCallback=callback_manager.suback, messageCallback=None)
print("Wait some time to make sure we are subscribed...")
time.sleep(3)  # 3 sec

print("Publishing...")
for i in range(NUMBER_OF_PUBLISHES):
    sdk_mqtt_client.publishAsync(topic, MESSAGE_PREFIX + str(i), 1, ackCallback=callback_manager.puback)
    time.sleep(1)
print("Wait sometime to make sure we finished with publishing...")
time.sleep(2)

print("Unsubscribing...")
sdk_mqtt_client.unsubscribeAsync(topic, ackCallback=callback_manager.unsuback)
print("Wait sometime to make sure we finished with unsubscribing...")
time.sleep(2)

print("Disconnecting...")
sdk_mqtt_client.disconnectAsync(ackCallback=callback_manager.disconnect)

print("Wait sometime to let the test result sync...")
time.sleep(3)

print("Verifying...")
try:
    assert callback_manager.callback_invocation_record[KEY_ON_ONLINE] == 1
    assert callback_manager.callback_invocation_record[KEY_CONNACK] == 1
    assert callback_manager.callback_invocation_record[KEY_SUBACK] == 1
    assert callback_manager.callback_invocation_record[KEY_PUBACK] == NUMBER_OF_PUBLISHES
    assert callback_manager.callback_invocation_record[KEY_ON_MESSAGE] == NUMBER_OF_PUBLISHES
    assert callback_manager.callback_invocation_record[KEY_UNSUBACK] == 1
    assert callback_manager.callback_invocation_record[KEY_DISCONNECT] == 1
    assert callback_manager.callback_invocation_record[KEY_ON_OFFLINE] == 1
except BaseException as e:
    print("Failed! %s" % e.message)
print("Pass!")
