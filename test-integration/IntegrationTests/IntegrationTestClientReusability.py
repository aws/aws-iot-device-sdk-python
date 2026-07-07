# This integration test verifies the re-usability of SDK MQTT client.
# By saying re-usability, we mean that users should be able to reuse
# the same SDK MQTT client object to connect and invoke other APIs
# after a disconnect API call has been invoked on that client object.
# This test contains 2 clients living 2 separate threads:
# 1. Thread publish: In this thread, a MQTT client will do the following
# in a loop:
# a. Connect to AWS IoT
# b. Publish several messages to a dedicated topic
# c. Disconnect from AWS IoT
# d. Sleep for a while
# 2. Thread subscribe: In this thread, a MQTT client will do nothing
# other than subscribing to a dedicated topic and counting the incoming
# messages.
# Assuming the client is reusable, the subscriber should be able to
# receive all the messages published by the publisher from the same
# client object in different connect sessions.


import uuid
import time
import sys
sys.path.insert(0, "./test-integration/IntegrationTests/TestToolLibrary")
sys.path.insert(0, "./test-integration/IntegrationTests/TestToolLibrary/SDKPackage")

from threading import Event
from TestToolLibrary.checkInManager import checkInManager
from TestToolLibrary.simpleThreadManager import simpleThreadManager
from TestToolLibrary.MQTTClientManager import MQTTClientManager
from TestToolLibrary.skip import skip_when_match
from TestToolLibrary.skip import ModeIsALPN
from TestToolLibrary.skip import Python2VersionLowerThan
from TestToolLibrary.skip import Python3VersionLowerThan


TOPIC = "topic/" + str(uuid.uuid1())
CLIENT_ID_PUB = "publisher" + str(uuid.uuid1())
CLIENT_ID_SUB = "subscriber" + str(uuid.uuid1())
MESSAGE_PREFIX = "Message-"
NUMBER_OF_MESSAGES_PER_LOOP = 3
NUMBER_OF_LOOPS = 3
SUB_WAIT_TIME_OUT_SEC = 20
ROOT_CA = "./test-integration/Credentials/rootCA.crt"
CERT = "./test-integration/Credentials/certificate.pem.crt"
KEY = "./test-integration/Credentials/privateKey.pem.key"


class ClientTwins(object):

    def __init__(self, client_pub, client_sub):
        self._client_pub = client_pub
        self._client_sub = client_sub
        self._message_publish_set = set()
        self._message_receive_set = set()
        self._publish_done = Event()

    def run_publisher(self, *params):
        self._publish_done.clear()
        time.sleep(3)
        for i in range(NUMBER_OF_LOOPS):
            self._single_publish_loop(i)
            time.sleep(2)
        self._publish_done.set()

    def _single_publish_loop(self, iteration_count):
        print("In loop %d: " % iteration_count)
        self._client_pub.connect()
        print("Publisher connected!")
        for i in range(NUMBER_OF_MESSAGES_PER_LOOP):
            message = MESSAGE_PREFIX + str(iteration_count) + "_" + str(i)
            self._client_pub.publish(TOPIC, message, 1)
            print("Publisher published %s to topic %s" % (message, TOPIC))
            self._message_publish_set.add(message.encode("utf-8"))
            time.sleep(1)
        self._client_pub.disconnect()
        print("Publisher disconnected!\n\n")

    def run_subscriber(self, *params):
        self._client_sub.connect()
        self._client_sub.subscribe(TOPIC, 1, self._callback)
        self._publish_done.wait(20)
        self._client_sub.disconnect()

    def _callback(self, client, user_data, message):
        self._message_receive_set.add(message.payload)
        print("Subscriber received %s from topic %s" % (message.payload, message.topic))

    def verify(self):
        assert len(self._message_receive_set) != 0
        assert len(self._message_publish_set) != 0
        assert self._message_publish_set == self._message_receive_set


############################################################################
# Main #
my_check_in_manager = checkInManager(2)
my_check_in_manager.verify(sys.argv)
mode = my_check_in_manager.mode
host = my_check_in_manager.host

skip_when_match(ModeIsALPN(mode).And(
    Python2VersionLowerThan((2, 7, 10)).Or(Python3VersionLowerThan((3, 5, 0)))
), "This test is not applicable for mode %s and Python verison %s. Skipping..." % (mode, sys.version_info[:3]))

simple_thread_manager = simpleThreadManager()

client_pub = MQTTClientManager().create_nonconnected_mqtt_client(mode, CLIENT_ID_PUB, host, (ROOT_CA, CERT, KEY))
print("Client publisher initialized.")
client_sub = MQTTClientManager().create_nonconnected_mqtt_client(mode, CLIENT_ID_SUB, host, (ROOT_CA, CERT, KEY))
print("Client subscriber initialized.")
client_twins = ClientTwins(client_pub, client_sub)
print("Client twins initialized.")

publisher_thread_id = simple_thread_manager.createOneTimeThread(client_twins.run_publisher, [])
subscriber_thread_id = simple_thread_manager.createOneTimeThread(client_twins.run_subscriber, [])
simple_thread_manager.startThreadWithID(subscriber_thread_id)
print("Started subscriber thread.")
simple_thread_manager.startThreadWithID(publisher_thread_id)
print("Started publisher thread.")

print("Main thread starts waiting.")
simple_thread_manager.joinOneTimeThreadWithID(publisher_thread_id)
simple_thread_manager.joinOneTimeThreadWithID(subscriber_thread_id)
print("Main thread waiting is done!")

print("Verifying...")
client_twins.verify()
print("Pass!")
