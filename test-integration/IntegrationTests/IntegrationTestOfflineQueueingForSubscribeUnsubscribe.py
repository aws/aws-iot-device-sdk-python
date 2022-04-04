# This integration test verifies the functionality off queueing up subscribe/unsubscribe requests submitted by the
# client when it is offline, and drain them out when the client is reconnected. The test contains 2 clients running in
# 2 different threads:
#
# In thread A, client_sub_unsub follows the below workflow:
# 1. Client connects to AWS IoT.
# 2. Client subscribes to "topic_A".
# 3. Experience a simulated network error which brings the client offline.
# 4. While offline, client subscribes to "topic_B' and unsubscribes from "topic_A".
# 5. Client reconnects, comes back online and drains out all offline queued requests.
# 6. Client stays and receives messages published in another thread.
#
# In thread B, client_pub follows the below workflow:
# 1. Client in thread B connects to AWS IoT.
# 2. After client in thread A connects and subscribes to "topic_A", client in thread B publishes messages to "topic_A".
# 3. Client in thread B keeps sleeping until client in thread A goes back online and reaches to a stable state (draining done).
# 4. Client in thread B then publishes messages to "topic_A" and "topic_B".
#
# Since client in thread A does a unsubscribe to "topic_A", it should never receive messages published to "topic_A" after
# it reconnects and gets stable. It should have the messages from "topic_A" published at the very beginning.
# Since client in thread A does a subscribe to "topic_B", it should receive messages published to "topic_B" after it
# reconnects and gets stable.


import random
import string
import time
from threading import Event
from threading import Thread
import sys
sys.path.insert(0, "./test-integration/IntegrationTests/TestToolLibrary")
sys.path.insert(0, "./test-integration/IntegrationTests/TestToolLibrary/SDKPackage")

from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.core.protocol.internal.clients import ClientStatus
from TestToolLibrary.checkInManager import checkInManager
from TestToolLibrary.MQTTClientManager import MQTTClientManager
from TestToolLibrary.skip import skip_when_match
from TestToolLibrary.skip import ModeIsALPN
from TestToolLibrary.skip import Python2VersionLowerThan
from TestToolLibrary.skip import Python3VersionLowerThan


TOPIC_A = "topic/test/offline_sub_unsub/a"
TOPIC_B = "topic/test/offline_sub_unsub/b"
MESSAGE_PREFIX = "MagicMessage-"
NUMBER_OF_PUBLISHES = 3
HOST = "ajje7lpljulm4-ats.iot.us-east-1.amazonaws.com"
ROOT_CA = "./test-integration/Credentials/rootCA.crt"
CERT = "./test-integration/Credentials/certificate.pem.crt"
KEY = "./test-integration/Credentials/privateKey.pem.key"
CLIENT_PUB_ID = "PySdkIntegTest_OfflineSubUnsub_pub"
CLIENT_SUB_UNSUB_ID = "PySdkIntegTest_OfflineSubUnsub_subunsub"
KEEP_ALIVE_SEC = 1
EVENT_WAIT_TIME_OUT_SEC = 5


def get_random_string(length):
    return "".join(random.choice(string.ascii_lowercase) for i in range(length))


class DualClientRunner(object):

    def __init__(self, mode):
        self._publish_end_flag = Event()
        self._stable_flag = Event()
        self._received_messages_topic_a = list()
        self._received_messages_topic_b = list()
        self.__mode = mode
        self._client_pub = self._create_connected_client(CLIENT_PUB_ID)
        print("Created connected client pub.")
        self._client_sub_unsub = self._create_connected_client(CLIENT_SUB_UNSUB_ID)
        print("Created connected client sub/unsub.")
        self._client_sub_unsub.subscribe(TOPIC_A, 1, self._collect_sub_messages)
        print("Client sub/unsub subscribed to topic: %s" % TOPIC_A)
        time.sleep(2)  # Make sure the subscription is valid

    def _create_connected_client(self, id_prefix):
        return MQTTClientManager().create_connected_mqtt_client(self.__mode, id_prefix, HOST, (ROOT_CA, CERT, KEY))

    def start(self):
        thread_client_sub_unsub = Thread(target=self._thread_client_sub_unsub_runtime)
        thread_client_pub = Thread(target=self._thread_client_pub_runtime)
        thread_client_sub_unsub.start()
        thread_client_pub.start()
        thread_client_pub.join()
        thread_client_sub_unsub.join()

    def _thread_client_sub_unsub_runtime(self):
        print("Start client sub/unsub runtime thread...")
        print("Client sub/unsub waits on the 1st round of publishes to end...")
        if not self._publish_end_flag.wait(EVENT_WAIT_TIME_OUT_SEC):
            raise RuntimeError("Timed out in waiting for the publishes to topic: %s" % TOPIC_A)
        print("Client sub/unsub gets notified.")
        self._publish_end_flag.clear()

        print("Client sub/unsub now goes offline...")
        self._go_offline_and_send_requests()

        # Wait until the connection is stable and then notify
        print("Client sub/unsub waits on a stable connection...")
        self._wait_until_stable_connection()

        print("Client sub/unsub waits on the 2nd round of publishes to end...")
        if not self._publish_end_flag.wait(EVENT_WAIT_TIME_OUT_SEC):
            raise RuntimeError("Timed out in waiting for the publishes to topic: %s" % TOPIC_B)
        print("Client sub/unsub gets notified.")
        self._publish_end_flag.clear()

        print("Client sub/unsub runtime thread ends.")

    def _wait_until_stable_connection(self):
        reconnect_timing = 0
        while self._client_sub_unsub._mqtt_core._client_status.get_status() != ClientStatus.STABLE:
            time.sleep(0.01)
            reconnect_timing += 1
            if reconnect_timing % 100 == 0:
                print("Client sub/unsub: Counting reconnect time: " + str(reconnect_timing / 100) + " seconds.")
        print("Client sub/unsub: Counting reconnect time result: " + str(float(reconnect_timing) / 100) + " seconds.")
        self._stable_flag.set()

    def _collect_sub_messages(self, client, userdata, message):
        if message.topic == TOPIC_A:
            print("Client sub/unsub: Got a message from %s" % TOPIC_A)
            self._received_messages_topic_a.append(message.payload)
        if message.topic == TOPIC_B:
            print("Client sub/unsub: Got a message from %s" % TOPIC_B)
            self._received_messages_topic_b.append(message.payload)

    def _go_offline_and_send_requests(self):
        do_once = True
        loop_count = EVENT_WAIT_TIME_OUT_SEC * 100
        while loop_count != 0:
            self._manual_network_error()
            if loop_count % 100 == 0:
                print("Client sub/unsub: Offline time down count: %d sec" % (loop_count / 100))
            if do_once and (loop_count / 100) <= (EVENT_WAIT_TIME_OUT_SEC / 2):
                print("Client sub/unsub: Performing offline sub/unsub...")
                self._client_sub_unsub.subscribe(TOPIC_B, 1, self._collect_sub_messages)
                self._client_sub_unsub.unsubscribe(TOPIC_A)
                print("Client sub/unsub: Done with offline sub/unsub.")
                do_once = False
            loop_count -= 1
            time.sleep(0.01)

    def _manual_network_error(self):
        # Ensure we close the socket
        if self._client_sub_unsub._mqtt_core._internal_async_client._paho_client._sock:
            self._client_sub_unsub._mqtt_core._internal_async_client._paho_client._sock.close()
            self._client_sub_unsub._mqtt_core._internal_async_client._paho_client._sock = None
        if self._client_sub_unsub._mqtt_core._internal_async_client._paho_client._ssl:
            self._client_sub_unsub._mqtt_core._internal_async_client._paho_client._ssl.close()
            self._client_sub_unsub._mqtt_core._internal_async_client._paho_client._ssl = None
        # Fake that we have detected the disconnection
        self._client_sub_unsub._mqtt_core._internal_async_client._paho_client.on_disconnect(None, None, 0)

    def _thread_client_pub_runtime(self):
        print("Start client pub runtime thread...")
        print("Client pub: 1st round of publishes")
        for i in range(NUMBER_OF_PUBLISHES):
            self._client_pub.publish(TOPIC_A, MESSAGE_PREFIX + str(i), 1)
            print("Client pub: Published a message")
            time.sleep(0.5)
        time.sleep(1)
        print("Client pub: Publishes done. Notifying...")
        self._publish_end_flag.set()

        print("Client pub waits on client sub/unsub to be stable...")
        time.sleep(1)
        if not self._stable_flag.wait(EVENT_WAIT_TIME_OUT_SEC * 3):  # We wait longer for the reconnect/stabilization
            raise RuntimeError("Timed out in waiting for client_sub_unsub to be stable")
        self._stable_flag.clear()

        print("Client pub: 2nd round of publishes")
        for j in range(NUMBER_OF_PUBLISHES):
            self._client_pub.publish(TOPIC_B, MESSAGE_PREFIX + str(j), 1)
            print("Client pub: Published a message to %s" % TOPIC_B)
            self._client_pub.publish(TOPIC_A, MESSAGE_PREFIX + str(j) + "-dup", 1)
            print("Client pub: Published a message to %s" % TOPIC_A)
            time.sleep(0.5)
        time.sleep(1)
        print("Client pub: Publishes done. Notifying...")
        self._publish_end_flag.set()

        print("Client pub runtime thread ends.")

    def verify(self):
        print("Verifying...")
        assert len(self._received_messages_topic_a) == NUMBER_OF_PUBLISHES  # We should only receive the first round
        assert len(self._received_messages_topic_b) == NUMBER_OF_PUBLISHES  # We should only receive the second round
        print("Pass!")


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
dual_client_runner = DualClientRunner(mode)
dual_client_runner.start()

# Verifying
###########
dual_client_runner.verify()
