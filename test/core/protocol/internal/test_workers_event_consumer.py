from AWSIoTPythonSDK.core.protocol.internal.workers import EventConsumer
from AWSIoTPythonSDK.core.protocol.internal.clients import ClientStatusContainer
from AWSIoTPythonSDK.core.protocol.internal.clients import ClientStatus
from AWSIoTPythonSDK.core.protocol.internal.events import FixedEventMids
from AWSIoTPythonSDK.core.protocol.internal.events import EventTypes
from AWSIoTPythonSDK.core.protocol.paho.client import MQTTMessage
from AWSIoTPythonSDK.core.protocol.internal.workers import SubscriptionManager
from AWSIoTPythonSDK.core.protocol.internal.workers import OfflineRequestsManager
from AWSIoTPythonSDK.core.protocol.internal.clients import InternalAsyncMqttClient
from AWSIoTPythonSDK.core.protocol.internal.requests import QueueableRequest
from AWSIoTPythonSDK.core.protocol.internal.requests import RequestTypes
from AWSIoTPythonSDK.core.protocol.internal.defaults import DEFAULT_DRAINING_INTERNAL_SEC
try:
    from mock import patch
    from mock import MagicMock
    from mock import call
except:
    from unittest.mock import patch
    from unittest.mock import MagicMock
    from unittest.mock import call
from threading import Condition
import time
import sys
if sys.version_info[0] < 3:
    from Queue import Queue
else:
    from queue import Queue


DUMMY_TOPIC = "dummy/topic"
DUMMY_MESSAGE = "dummy_message"
DUMMY_QOS = 1
DUMMY_SUCCESS_RC = 0
DUMMY_PUBACK_MID = 89757
DUMMY_SUBACK_MID = 89758
DUMMY_UNSUBACK_MID = 89579

KEY_CLIENT_STATUS_AFTER = "status_after"
KEY_STOP_BG_NW_IO_CALL_COUNT = "stop_background_network_io_call_count"
KEY_CLEAN_UP_EVENT_CBS_CALL_COUNT = "clean_up_event_callbacks_call_count"
KEY_IS_EVENT_Q_EMPTY = "is_event_queue_empty"
KEY_IS_EVENT_CONSUMER_UP = "is_event_consumer_running"

class TestWorkersEventConsumer:

    def setup_method(self, test_method):
        self.cv = Condition()
        self.event_queue = Queue()
        self.client_status = ClientStatusContainer()
        self.internal_async_client = MagicMock(spec=InternalAsyncMqttClient)
        self.subscription_manager = MagicMock(spec=SubscriptionManager)
        self.offline_requests_manager = MagicMock(spec=OfflineRequestsManager)
        self.message_callback = MagicMock()
        self.subscribe_callback = MagicMock()
        self.unsubscribe_callback = MagicMock()
        self.event_consumer = None

    def teardown_method(self, test_method):
        if self.event_consumer and self.event_consumer.is_running():
            self.event_consumer.stop()
            self.event_consumer.wait_until_it_stops(2)  # Make sure the event consumer stops gracefully

    def test_update_draining_interval_sec(self):
        EXPECTED_DRAINING_INTERVAL_SEC = 0.5
        self.load_mocks_into_test_target()
        self.event_consumer.update_draining_interval_sec(EXPECTED_DRAINING_INTERVAL_SEC)
        assert self.event_consumer.get_draining_interval_sec() == EXPECTED_DRAINING_INTERVAL_SEC

    def test_dispatch_message_event(self):
        expected_message_event = self._configure_mocks_message_event()
        self._start_consumer()
        self._verify_message_event_dispatch(expected_message_event)

    def _configure_mocks_message_event(self):
        message_event = self._create_message_event(DUMMY_TOPIC, DUMMY_MESSAGE, DUMMY_QOS)
        self._fill_in_fake_events([message_event])
        self.subscription_manager.list_records.return_value = [(DUMMY_TOPIC, (DUMMY_QOS, self.message_callback, self.subscribe_callback))]
        self.load_mocks_into_test_target()
        return message_event

    def _create_message_event(self, topic, payload, qos):
        mqtt_message = MQTTMessage()
        mqtt_message.topic = topic
        mqtt_message.payload = payload
        mqtt_message.qos = qos
        return FixedEventMids.MESSAGE_MID, EventTypes.MESSAGE, mqtt_message

    def _verify_message_event_dispatch(self, expected_message_event):
        expected_message = expected_message_event[2]
        self.message_callback.assert_called_once_with(None, None, expected_message)
        self.internal_async_client.invoke_event_callback.assert_called_once_with(FixedEventMids.MESSAGE_MID, data=expected_message)
        assert self.event_consumer.is_running() is True

    def test_dispatch_disconnect_event_user_disconnect(self):
        self._configure_mocks_disconnect_event(ClientStatus.USER_DISCONNECT)
        self._start_consumer()
        expected_values = {
            KEY_CLIENT_STATUS_AFTER : ClientStatus.USER_DISCONNECT,
            KEY_STOP_BG_NW_IO_CALL_COUNT : 1,
            KEY_CLEAN_UP_EVENT_CBS_CALL_COUNT : 1,
            KEY_IS_EVENT_Q_EMPTY : True,
            KEY_IS_EVENT_CONSUMER_UP : False
        }
        self._verify_disconnect_event_dispatch(expected_values)
        assert self.event_consumer.is_fully_stopped() is True

    def test_dispatch_disconnect_event_connect_failure(self):
        self._configure_mocks_disconnect_event(ClientStatus.CONNECT)
        self._start_consumer()
        expected_values = {
            KEY_CLIENT_STATUS_AFTER : ClientStatus.CONNECT,
            KEY_STOP_BG_NW_IO_CALL_COUNT : 1,
            KEY_CLEAN_UP_EVENT_CBS_CALL_COUNT : 1,
            KEY_IS_EVENT_Q_EMPTY : True,
            KEY_IS_EVENT_CONSUMER_UP : False
        }
        self._verify_disconnect_event_dispatch(expected_values)
        assert self.event_consumer.is_fully_stopped() is True

    def test_dispatch_disconnect_event_abnormal_disconnect(self):
        self._configure_mocks_disconnect_event(ClientStatus.STABLE)
        self._start_consumer()
        expected_values = {
            KEY_CLIENT_STATUS_AFTER : ClientStatus.ABNORMAL_DISCONNECT,
            KEY_STOP_BG_NW_IO_CALL_COUNT : 0,
            KEY_CLEAN_UP_EVENT_CBS_CALL_COUNT : 0,
            KEY_IS_EVENT_CONSUMER_UP : True
        }
        self._verify_disconnect_event_dispatch(expected_values)
        assert self.event_consumer.is_fully_stopped() is False

    def _configure_mocks_disconnect_event(self, start_client_status):
        self.client_status.set_status(start_client_status)
        self._fill_in_fake_events([self._create_disconnect_event()])
        self.load_mocks_into_test_target()

    def _create_disconnect_event(self):
        return FixedEventMids.DISCONNECT_MID, EventTypes.DISCONNECT, DUMMY_SUCCESS_RC

    def _verify_disconnect_event_dispatch(self, expected_values):
        client_status_after = expected_values.get(KEY_CLIENT_STATUS_AFTER)
        stop_background_network_io_call_count = expected_values.get(KEY_STOP_BG_NW_IO_CALL_COUNT)
        clean_up_event_callbacks_call_count = expected_values.get(KEY_CLEAN_UP_EVENT_CBS_CALL_COUNT)
        is_event_queue_empty = expected_values.get(KEY_IS_EVENT_Q_EMPTY)
        is_event_consumer_running = expected_values.get(KEY_IS_EVENT_CONSUMER_UP)

        if client_status_after is not None:
            assert self.client_status.get_status() == client_status_after
        if stop_background_network_io_call_count is not None:
            assert self.internal_async_client.stop_background_network_io.call_count == stop_background_network_io_call_count
        if clean_up_event_callbacks_call_count is not None:
            assert self.internal_async_client.clean_up_event_callbacks.call_count == clean_up_event_callbacks_call_count
        if is_event_queue_empty is not None:
            assert self.event_queue.empty() == is_event_queue_empty
        if is_event_consumer_running is not None:
            assert self.event_consumer.is_running() == is_event_consumer_running

        self.internal_async_client.invoke_event_callback.assert_called_once_with(FixedEventMids.DISCONNECT_MID, data=DUMMY_SUCCESS_RC)

    def test_dispatch_connack_event_no_recovery(self):
        self._configure_mocks_connack_event()
        self._start_consumer()
        self._verify_connack_event_dispatch()

    def test_dispatch_connack_event_need_resubscribe(self):
        resub_records = [
            (DUMMY_TOPIC + "1", (DUMMY_QOS, self.message_callback, self.subscribe_callback)),
            (DUMMY_TOPIC + "2", (DUMMY_QOS, self.message_callback, self.subscribe_callback)),
            (DUMMY_TOPIC + "3", (DUMMY_QOS, self.message_callback, self.subscribe_callback))
        ]
        self._configure_mocks_connack_event(resubscribe_records=resub_records)
        self._start_consumer()
        self._verify_connack_event_dispatch(resubscribe_records=resub_records)

    def test_dispatch_connack_event_need_draining(self):
        self._configure_mocks_connack_event(need_draining=True)
        self._start_consumer()
        self._verify_connack_event_dispatch(need_draining=True)

    def test_dispatch_connack_event_need_resubscribe_draining(self):
        resub_records = [
            (DUMMY_TOPIC + "1", (DUMMY_QOS, self.message_callback, self.subscribe_callback)),
            (DUMMY_TOPIC + "2", (DUMMY_QOS, self.message_callback, self.subscribe_callback)),
            (DUMMY_TOPIC + "3", (DUMMY_QOS, self.message_callback, self.subscribe_callback))
        ]
        self._configure_mocks_connack_event(resubscribe_records=resub_records, need_draining=True)
        self._start_consumer()
        self._verify_connack_event_dispatch(resubscribe_records=resub_records, need_draining=True)

    def _configure_mocks_connack_event(self, resubscribe_records=list(), need_draining=False):
        self.client_status.set_status(ClientStatus.CONNECT)
        self._fill_in_fake_events([self._create_connack_event()])
        self.subscription_manager.list_records.return_value = resubscribe_records
        if need_draining:  # We pack publish, subscribe and unsubscribe requests into the offline queue
            if resubscribe_records:
                has_more_side_effect_list = 4 * [True]
            else:
                has_more_side_effect_list = 5 * [True]
            has_more_side_effect_list += [False]
            self.offline_requests_manager.has_more.side_effect = has_more_side_effect_list
            self.offline_requests_manager.get_next.side_effect = [
                QueueableRequest(RequestTypes.PUBLISH, (DUMMY_TOPIC, DUMMY_MESSAGE, DUMMY_QOS, False)),
                QueueableRequest(RequestTypes.SUBSCRIBE, (DUMMY_TOPIC, DUMMY_QOS, self.message_callback, self.subscribe_callback)),
                QueueableRequest(RequestTypes.UNSUBSCRIBE, (DUMMY_TOPIC, self.unsubscribe_callback))
            ]
        else:
            self.offline_requests_manager.has_more.return_value = False
        self.load_mocks_into_test_target()

    def _create_connack_event(self):
        return FixedEventMids.CONNACK_MID, EventTypes.CONNACK, DUMMY_SUCCESS_RC

    def _verify_connack_event_dispatch(self, resubscribe_records=list(), need_draining=False):
        time.sleep(3 * DEFAULT_DRAINING_INTERNAL_SEC)  # Make sure resubscribe/draining finishes
        assert self.event_consumer.is_running() is True
        self.internal_async_client.invoke_event_callback.assert_called_once_with(FixedEventMids.CONNACK_MID, data=DUMMY_SUCCESS_RC)
        if resubscribe_records:
            resub_call_sequence = []
            for topic, (qos, message_callback, subscribe_callback) in resubscribe_records:
                resub_call_sequence.append(call(topic, qos, subscribe_callback))
            self.internal_async_client.subscribe.assert_has_calls(resub_call_sequence)
        if need_draining:
            assert self.internal_async_client.publish.call_count == 1
            assert self.internal_async_client.unsubscribe.call_count == 1
            assert self.internal_async_client.subscribe.call_count == len(resubscribe_records) + 1
        assert self.event_consumer.is_fully_stopped() is False

    def test_dispatch_puback_suback_unsuback_events(self):
        self._configure_mocks_puback_suback_unsuback_events()
        self._start_consumer()
        self._verify_puback_suback_unsuback_events_dispatch()

    def _configure_mocks_puback_suback_unsuback_events(self):
        self.client_status.set_status(ClientStatus.STABLE)
        self._fill_in_fake_events([
            self._create_puback_event(DUMMY_PUBACK_MID),
            self._create_suback_event(DUMMY_SUBACK_MID),
            self._create_unsuback_event(DUMMY_UNSUBACK_MID)])
        self.load_mocks_into_test_target()

    def _verify_puback_suback_unsuback_events_dispatch(self):
        assert self.event_consumer.is_running() is True
        call_sequence = [
            call(DUMMY_PUBACK_MID, data=None),
            call(DUMMY_SUBACK_MID, data=DUMMY_QOS),
            call(DUMMY_UNSUBACK_MID, data=None)]
        self.internal_async_client.invoke_event_callback.assert_has_calls(call_sequence)
        assert self.event_consumer.is_fully_stopped() is False

    def _fill_in_fake_events(self, events):
        for event in events:
            self.event_queue.put(event)

    def _start_consumer(self):
        self.event_consumer.start()
        time.sleep(1)  # Make sure the event gets picked up by the consumer

    def load_mocks_into_test_target(self):
        self.event_consumer = EventConsumer(self.cv,
                                            self.event_queue,
                                            self.internal_async_client,
                                            self.subscription_manager,
                                            self.offline_requests_manager,
                                            self.client_status)

    def _create_puback_event(self, mid):
        return mid, EventTypes.PUBACK, None

    def _create_suback_event(self, mid):
        return mid, EventTypes.SUBACK, DUMMY_QOS

    def _create_unsuback_event(self, mid):
        return mid, EventTypes.UNSUBACK, None
