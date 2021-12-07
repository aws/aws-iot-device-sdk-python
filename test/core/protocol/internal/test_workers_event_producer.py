import pytest
from threading import Condition
from AWSIoTPythonSDK.core.protocol.internal.workers import EventProducer
from AWSIoTPythonSDK.core.protocol.internal.events import FixedEventMids
from AWSIoTPythonSDK.core.protocol.internal.events import EventTypes
from AWSIoTPythonSDK.core.protocol.paho.client import MQTTMessage
import sys
if sys.version_info[0] < 3:
    from Queue import Queue
else:
    from queue import Queue

DUMMY_PAHO_CLIENT = None
DUMMY_USER_DATA = None
DUMMY_FLAGS = None
DUMMY_GRANTED_QOS = 1
DUMMY_MID = 89757
SUCCESS_RC = 0

MAX_CV_WAIT_TIME_SEC = 5

class TestWorkersEventProducer:

    def setup_method(self, test_method):
        self._generate_test_targets()

    def test_produce_on_connect_event(self):
        self.event_producer.on_connect(DUMMY_PAHO_CLIENT, DUMMY_USER_DATA, DUMMY_FLAGS, SUCCESS_RC)
        self._verify_queued_event(self.event_queue, (FixedEventMids.CONNACK_MID, EventTypes.CONNACK, SUCCESS_RC))

    def test_produce_on_disconnect_event(self):
        self.event_producer.on_disconnect(DUMMY_PAHO_CLIENT, DUMMY_USER_DATA, SUCCESS_RC)
        self._verify_queued_event(self.event_queue, (FixedEventMids.DISCONNECT_MID, EventTypes.DISCONNECT, SUCCESS_RC))

    def test_produce_on_publish_event(self):
        self.event_producer.on_publish(DUMMY_PAHO_CLIENT, DUMMY_USER_DATA, DUMMY_MID)
        self._verify_queued_event(self.event_queue, (DUMMY_MID, EventTypes.PUBACK, None))

    def test_produce_on_subscribe_event(self):
        self.event_producer.on_subscribe(DUMMY_PAHO_CLIENT, DUMMY_USER_DATA, DUMMY_MID, DUMMY_GRANTED_QOS)
        self._verify_queued_event(self.event_queue, (DUMMY_MID, EventTypes.SUBACK, DUMMY_GRANTED_QOS))

    def test_produce_on_unsubscribe_event(self):
        self.event_producer.on_unsubscribe(DUMMY_PAHO_CLIENT, DUMMY_USER_DATA, DUMMY_MID)
        self._verify_queued_event(self.event_queue, (DUMMY_MID, EventTypes.UNSUBACK, None))

    def test_produce_on_message_event(self):
        dummy_message = MQTTMessage()
        dummy_message.topic = "test/topic"
        dummy_message.qos = 1
        dummy_message.payload = "test_payload"
        self.event_producer.on_message(DUMMY_PAHO_CLIENT, DUMMY_USER_DATA, dummy_message)
        self._verify_queued_event(self.event_queue, (FixedEventMids.MESSAGE_MID, EventTypes.MESSAGE, dummy_message))

    def _generate_test_targets(self):
        self.cv = Condition()
        self.event_queue = Queue()
        self.event_producer = EventProducer(self.cv, self.event_queue)

    def _verify_queued_event(self, queue, expected_results):
        expected_mid, expected_event_type, expected_data = expected_results
        actual_mid, actual_event_type, actual_data = queue.get()
        assert actual_mid == expected_mid
        assert actual_event_type == expected_event_type
        assert actual_data == expected_data
