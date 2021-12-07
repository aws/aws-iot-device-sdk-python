import AWSIoTPythonSDK
from AWSIoTPythonSDK.core.protocol.mqtt_core import MqttCore
from AWSIoTPythonSDK.core.protocol.internal.clients import InternalAsyncMqttClient
from AWSIoTPythonSDK.core.protocol.internal.clients import ClientStatusContainer
from AWSIoTPythonSDK.core.protocol.internal.clients import ClientStatus
from AWSIoTPythonSDK.core.protocol.internal.workers import EventProducer
from AWSIoTPythonSDK.core.protocol.internal.workers import EventConsumer
from AWSIoTPythonSDK.core.protocol.internal.workers import SubscriptionManager
from AWSIoTPythonSDK.core.protocol.internal.workers import OfflineRequestsManager
from AWSIoTPythonSDK.core.protocol.internal.events import FixedEventMids
from AWSIoTPythonSDK.core.protocol.internal.queues import AppendResults
from AWSIoTPythonSDK.core.protocol.internal.requests import RequestTypes
from AWSIoTPythonSDK.core.protocol.internal.defaults import METRICS_PREFIX
from AWSIoTPythonSDK.exception.AWSIoTExceptions import connectError
from AWSIoTPythonSDK.exception.AWSIoTExceptions import connectTimeoutException
from AWSIoTPythonSDK.exception.AWSIoTExceptions import disconnectError
from AWSIoTPythonSDK.exception.AWSIoTExceptions import disconnectTimeoutException
from AWSIoTPythonSDK.exception.AWSIoTExceptions import publishError
from AWSIoTPythonSDK.exception.AWSIoTExceptions import publishTimeoutException
from AWSIoTPythonSDK.exception.AWSIoTExceptions import publishQueueFullException
from AWSIoTPythonSDK.exception.AWSIoTExceptions import publishQueueDisabledException
from AWSIoTPythonSDK.exception.AWSIoTExceptions import subscribeError
from AWSIoTPythonSDK.exception.AWSIoTExceptions import subscribeTimeoutException
from AWSIoTPythonSDK.exception.AWSIoTExceptions import subscribeQueueFullException
from AWSIoTPythonSDK.exception.AWSIoTExceptions import subscribeQueueDisabledException
from AWSIoTPythonSDK.exception.AWSIoTExceptions import unsubscribeError
from AWSIoTPythonSDK.exception.AWSIoTExceptions import unsubscribeTimeoutException
from AWSIoTPythonSDK.exception.AWSIoTExceptions import unsubscribeQueueFullException
from AWSIoTPythonSDK.exception.AWSIoTExceptions import unsubscribeQueueDisabledException
from AWSIoTPythonSDK.core.protocol.paho.client import MQTT_ERR_SUCCESS
from AWSIoTPythonSDK.core.protocol.paho.client import MQTT_ERR_ERRNO
from AWSIoTPythonSDK.core.protocol.paho.client import MQTTv311
from AWSIoTPythonSDK.core.protocol.internal.defaults import ALPN_PROTCOLS
try:
    from mock import patch
    from mock import MagicMock
    from mock import NonCallableMagicMock
    from mock import call
except:
    from unittest.mock import patch
    from unittest.mock import MagicMock
    from unittest.mock import NonCallableMagicMock
    from unittest.mock import call
from threading import Event
import pytest


PATCH_MODULE_LOCATION = "AWSIoTPythonSDK.core.protocol.mqtt_core."
DUMMY_SUCCESS_RC = MQTT_ERR_SUCCESS
DUMMY_FAILURE_RC = MQTT_ERR_ERRNO
DUMMY_REQUEST_MID = 89757
DUMMY_CLIENT_ID = "CoolClientId"
DUMMY_KEEP_ALIVE_SEC = 60
DUMMY_TOPIC = "topic/cool"
DUMMY_PAYLOAD = "CoolPayload"
DUMMY_QOS = 1
DUMMY_USERNAME = "DummyUsername"
DUMMY_PASSWORD = "DummyPassword"

KEY_EXPECTED_REQUEST_RC = "ExpectedRequestRc"
KEY_EXPECTED_QUEUE_APPEND_RESULT = "ExpectedQueueAppendResult"
KEY_EXPECTED_REQUEST_MID_OVERRIDE = "ExpectedRequestMidOverride"
KEY_EXPECTED_REQUEST_TIMEOUT = "ExpectedRequestTimeout"
SUCCESS_RC_EXPECTED_VALUES = {
    KEY_EXPECTED_REQUEST_RC : DUMMY_SUCCESS_RC
}
FAILURE_RC_EXPECTED_VALUES = {
    KEY_EXPECTED_REQUEST_RC : DUMMY_FAILURE_RC
}
TIMEOUT_EXPECTED_VALUES = {
    KEY_EXPECTED_REQUEST_TIMEOUT : True
}
NO_TIMEOUT_EXPECTED_VALUES = {
    KEY_EXPECTED_REQUEST_TIMEOUT : False
}
QUEUED_EXPECTED_VALUES = {
    KEY_EXPECTED_QUEUE_APPEND_RESULT : AppendResults.APPEND_SUCCESS
}
QUEUE_FULL_EXPECTED_VALUES = {
    KEY_EXPECTED_QUEUE_APPEND_RESULT : AppendResults.APPEND_FAILURE_QUEUE_FULL
}
QUEUE_DISABLED_EXPECTED_VALUES = {
    KEY_EXPECTED_QUEUE_APPEND_RESULT : AppendResults.APPEND_FAILURE_QUEUE_DISABLED
}

class TestMqttCore:

    def setup_class(cls):
        cls.configure_internal_async_client = {
            RequestTypes.CONNECT : cls._configure_internal_async_client_connect,
            RequestTypes.DISCONNECT : cls._configure_internal_async_client_disconnect,
            RequestTypes.PUBLISH : cls._configure_internal_async_client_publish,
            RequestTypes.SUBSCRIBE : cls._configure_internal_async_client_subscribe,
            RequestTypes.UNSUBSCRIBE : cls._configure_internal_async_client_unsubscribe
        }
        cls.invoke_mqtt_core_async_api = {
            RequestTypes.CONNECT : cls._invoke_mqtt_core_connect_async,
            RequestTypes.DISCONNECT : cls._invoke_mqtt_core_disconnect_async,
            RequestTypes.PUBLISH : cls._invoke_mqtt_core_publish_async,
            RequestTypes.SUBSCRIBE : cls._invoke_mqtt_core_subscribe_async,
            RequestTypes.UNSUBSCRIBE : cls._invoke_mqtt_core_unsubscribe_async
        }
        cls.invoke_mqtt_core_sync_api = {
            RequestTypes.CONNECT : cls._invoke_mqtt_core_connect,
            RequestTypes.DISCONNECT : cls._invoke_mqtt_core_disconnect,
            RequestTypes.PUBLISH : cls._invoke_mqtt_core_publish,
            RequestTypes.SUBSCRIBE : cls._invoke_mqtt_core_subscribe,
            RequestTypes.UNSUBSCRIBE : cls._invoke_mqtt_core_unsubscribe
        }
        cls.verify_mqtt_core_async_api = {
            RequestTypes.CONNECT : cls._verify_mqtt_core_connect_async,
            RequestTypes.DISCONNECT : cls._verify_mqtt_core_disconnect_async,
            RequestTypes.PUBLISH : cls._verify_mqtt_core_publish_async,
            RequestTypes.SUBSCRIBE : cls._verify_mqtt_core_subscribe_async,
            RequestTypes.UNSUBSCRIBE : cls._verify_mqtt_core_unsubscribe_async
        }
        cls.request_error = {
            RequestTypes.CONNECT : connectError,
            RequestTypes.DISCONNECT : disconnectError,
            RequestTypes.PUBLISH : publishError,
            RequestTypes.SUBSCRIBE: subscribeError,
            RequestTypes.UNSUBSCRIBE: unsubscribeError
        }
        cls.request_queue_full = {
            RequestTypes.PUBLISH : publishQueueFullException,
            RequestTypes.SUBSCRIBE: subscribeQueueFullException,
            RequestTypes.UNSUBSCRIBE: unsubscribeQueueFullException
        }
        cls.request_queue_disable = {
            RequestTypes.PUBLISH : publishQueueDisabledException,
            RequestTypes.SUBSCRIBE : subscribeQueueDisabledException,
            RequestTypes.UNSUBSCRIBE : unsubscribeQueueDisabledException
        }
        cls.request_timeout = {
            RequestTypes.CONNECT : connectTimeoutException,
            RequestTypes.DISCONNECT : disconnectTimeoutException,
            RequestTypes.PUBLISH : publishTimeoutException,
            RequestTypes.SUBSCRIBE : subscribeTimeoutException,
            RequestTypes.UNSUBSCRIBE : unsubscribeTimeoutException
        }

    def _configure_internal_async_client_connect(self, expected_rc, expected_mid=None):
        self.internal_async_client_mock.connect.return_value = expected_rc

    def _configure_internal_async_client_disconnect(self, expected_rc, expeected_mid=None):
        self.internal_async_client_mock.disconnect.return_value = expected_rc

    def _configure_internal_async_client_publish(self, expected_rc, expected_mid):
        self.internal_async_client_mock.publish.return_value = expected_rc, expected_mid

    def _configure_internal_async_client_subscribe(self, expected_rc, expected_mid):
        self.internal_async_client_mock.subscribe.return_value = expected_rc, expected_mid

    def _configure_internal_async_client_unsubscribe(self, expected_rc, expected_mid):
        self.internal_async_client_mock.unsubscribe.return_value = expected_rc, expected_mid

    def _invoke_mqtt_core_connect_async(self, ack_callback, message_callback):
        return self.mqtt_core.connect_async(DUMMY_KEEP_ALIVE_SEC, ack_callback)

    def _invoke_mqtt_core_disconnect_async(self, ack_callback, message_callback):
        return self.mqtt_core.disconnect_async(ack_callback)

    def _invoke_mqtt_core_publish_async(self, ack_callback, message_callback):
        return self.mqtt_core.publish_async(DUMMY_TOPIC, DUMMY_PAYLOAD, DUMMY_QOS, False, ack_callback)

    def _invoke_mqtt_core_subscribe_async(self, ack_callback, message_callback):
        return self.mqtt_core.subscribe_async(DUMMY_TOPIC, DUMMY_QOS, ack_callback, message_callback)

    def _invoke_mqtt_core_unsubscribe_async(self, ack_callback, message_callback):
        return self.mqtt_core.unsubscribe_async(DUMMY_TOPIC, ack_callback)

    def _invoke_mqtt_core_connect(self, message_callback):
        return self.mqtt_core.connect(DUMMY_KEEP_ALIVE_SEC)

    def _invoke_mqtt_core_disconnect(self, message_callback):
        return self.mqtt_core.disconnect()

    def _invoke_mqtt_core_publish(self, message_callback):
        return self.mqtt_core.publish(DUMMY_TOPIC, DUMMY_PAYLOAD, DUMMY_QOS)

    def _invoke_mqtt_core_subscribe(self, message_callback):
        return self.mqtt_core.subscribe(DUMMY_TOPIC, DUMMY_QOS, message_callback)

    def _invoke_mqtt_core_unsubscribe(self, message_callback):
        return self.mqtt_core.unsubscribe(DUMMY_TOPIC)

    def _verify_mqtt_core_connect_async(self, ack_callback, message_callback):
        self.internal_async_client_mock.connect.assert_called_once_with(DUMMY_KEEP_ALIVE_SEC, ack_callback)
        self.client_status_mock.set_status.assert_called_once_with(ClientStatus.CONNECT)

    def _verify_mqtt_core_disconnect_async(self, ack_callback, message_callback):
        self.internal_async_client_mock.disconnect.assert_called_once_with(ack_callback)
        self.client_status_mock.set_status.assert_called_once_with(ClientStatus.USER_DISCONNECT)

    def _verify_mqtt_core_publish_async(self, ack_callback, message_callback):
        self.internal_async_client_mock.publish.assert_called_once_with(DUMMY_TOPIC, DUMMY_PAYLOAD, DUMMY_QOS,
                                                                        False, ack_callback)

    def _verify_mqtt_core_subscribe_async(self, ack_callback, message_callback):
        self.internal_async_client_mock.subscribe.assert_called_once_with(DUMMY_TOPIC, DUMMY_QOS, ack_callback)
        self.subscription_manager_mock.add_record.assert_called_once_with(DUMMY_TOPIC, DUMMY_QOS, message_callback, ack_callback)

    def _verify_mqtt_core_unsubscribe_async(self, ack_callback, message_callback):
        self.internal_async_client_mock.unsubscribe.assert_called_once_with(DUMMY_TOPIC, ack_callback)
        self.subscription_manager_mock.remove_record.assert_called_once_with(DUMMY_TOPIC)

    def setup_method(self, test_method):
        self._use_mock_internal_async_client()
        self._use_mock_event_producer()
        self._use_mock_event_consumer()
        self._use_mock_subscription_manager()
        self._use_mock_offline_requests_manager()
        self._use_mock_client_status()
        self.mqtt_core = MqttCore(DUMMY_CLIENT_ID, True, MQTTv311, False)  # We choose x.509 auth type for this test

    def _use_mock_internal_async_client(self):
        self.internal_async_client_patcher = patch(PATCH_MODULE_LOCATION + "InternalAsyncMqttClient",
                                                   spec=InternalAsyncMqttClient)
        self.mock_internal_async_client_constructor = self.internal_async_client_patcher.start()
        self.internal_async_client_mock = MagicMock()
        self.mock_internal_async_client_constructor.return_value = self.internal_async_client_mock

    def _use_mock_event_producer(self):
        self.event_producer_patcher = patch(PATCH_MODULE_LOCATION + "EventProducer", spec=EventProducer)
        self.mock_event_producer_constructor = self.event_producer_patcher.start()
        self.event_producer_mock = MagicMock()
        self.mock_event_producer_constructor.return_value = self.event_producer_mock

    def _use_mock_event_consumer(self):
        self.event_consumer_patcher = patch(PATCH_MODULE_LOCATION + "EventConsumer", spec=EventConsumer)
        self.mock_event_consumer_constructor = self.event_consumer_patcher.start()
        self.event_consumer_mock = MagicMock()
        self.mock_event_consumer_constructor.return_value = self.event_consumer_mock

    def _use_mock_subscription_manager(self):
        self.subscription_manager_patcher = patch(PATCH_MODULE_LOCATION + "SubscriptionManager",
                                                  spec=SubscriptionManager)
        self.mock_subscription_manager_constructor = self.subscription_manager_patcher.start()
        self.subscription_manager_mock = MagicMock()
        self.mock_subscription_manager_constructor.return_value = self.subscription_manager_mock

    def _use_mock_offline_requests_manager(self):
        self.offline_requests_manager_patcher = patch(PATCH_MODULE_LOCATION + "OfflineRequestsManager",
                                                      spec=OfflineRequestsManager)
        self.mock_offline_requests_manager_constructor = self.offline_requests_manager_patcher.start()
        self.offline_requests_manager_mock = MagicMock()
        self.mock_offline_requests_manager_constructor.return_value = self.offline_requests_manager_mock

    def _use_mock_client_status(self):
        self.client_status_patcher = patch(PATCH_MODULE_LOCATION + "ClientStatusContainer", spec=ClientStatusContainer)
        self.mock_client_status_constructor = self.client_status_patcher.start()
        self.client_status_mock = MagicMock()
        self.mock_client_status_constructor.return_value = self.client_status_mock

    def teardown_method(self, test_method):
        self.internal_async_client_patcher.stop()
        self.event_producer_patcher.stop()
        self.event_consumer_patcher.stop()
        self.subscription_manager_patcher.stop()
        self.offline_requests_manager_patcher.stop()
        self.client_status_patcher.stop()

    # Finally... Tests start
    def test_use_wss(self):
        self.mqtt_core = MqttCore(DUMMY_CLIENT_ID, True, MQTTv311, True)  # use wss
        assert self.mqtt_core.use_wss() is True

    def test_configure_alpn_protocols(self):
        self.mqtt_core.configure_alpn_protocols()
        self.internal_async_client_mock.configure_alpn_protocols.assert_called_once_with([ALPN_PROTCOLS])

    def test_enable_metrics_collection_with_username_in_connect(self):
        self._configure_internal_async_client_connect(DUMMY_SUCCESS_RC)
        self._use_mock_python_event()
        self.python_event_mock.wait.return_value = True
        self.mqtt_core.configure_username_password(DUMMY_USERNAME, DUMMY_PASSWORD)
        self.mqtt_core.connect(DUMMY_KEEP_ALIVE_SEC)
        self.internal_async_client_mock.set_username_password.assert_called_once_with(DUMMY_USERNAME +
                                                                                      METRICS_PREFIX +
                                                                                      AWSIoTPythonSDK.__version__,
                                                                                      DUMMY_PASSWORD)
        self.python_event_patcher.stop()

    def test_enable_metrics_collection_with_username_in_connect_async(self):
        self._configure_internal_async_client_connect(DUMMY_SUCCESS_RC)
        self.mqtt_core.configure_username_password(DUMMY_USERNAME, DUMMY_PASSWORD)
        self.mqtt_core.connect_async(DUMMY_KEEP_ALIVE_SEC)
        self.internal_async_client_mock.set_username_password.assert_called_once_with(DUMMY_USERNAME +
                                                                                      METRICS_PREFIX +
                                                                                      AWSIoTPythonSDK.__version__,
                                                                                      DUMMY_PASSWORD)

    def test_enable_metrics_collection_without_username_in_connect(self):
        self._configure_internal_async_client_connect(DUMMY_SUCCESS_RC)
        self._use_mock_python_event()
        self.python_event_mock.wait.return_value = True
        self.mqtt_core.connect(DUMMY_KEEP_ALIVE_SEC)
        self.internal_async_client_mock.set_username_password.assert_called_once_with(METRICS_PREFIX +
                                                                                      AWSIoTPythonSDK.__version__,
                                                                                      None)
        self.python_event_patcher.stop()

    def test_enable_metrics_collection_without_username_in_connect_async(self):
        self._configure_internal_async_client_connect(DUMMY_SUCCESS_RC)
        self.mqtt_core.connect_async(DUMMY_KEEP_ALIVE_SEC)
        self.internal_async_client_mock.set_username_password.assert_called_once_with(METRICS_PREFIX +
                                                                                      AWSIoTPythonSDK.__version__,
                                                                                      None)

    def test_disable_metrics_collection_with_username_in_connect(self):
        self._configure_internal_async_client_connect(DUMMY_SUCCESS_RC)
        self._use_mock_python_event()
        self.python_event_mock.wait.return_value = True
        self.mqtt_core.disable_metrics_collection()
        self.mqtt_core.configure_username_password(DUMMY_USERNAME, DUMMY_PASSWORD)
        self.mqtt_core.connect(DUMMY_KEEP_ALIVE_SEC)
        self.internal_async_client_mock.set_username_password.assert_called_once_with(DUMMY_USERNAME, DUMMY_PASSWORD)
        self.python_event_patcher.stop()

    def test_disable_metrics_collection_with_username_in_connect_async(self):
        self._configure_internal_async_client_connect(DUMMY_SUCCESS_RC)
        self.mqtt_core.disable_metrics_collection()
        self.mqtt_core.configure_username_password(DUMMY_USERNAME, DUMMY_PASSWORD)
        self.mqtt_core.connect_async(DUMMY_KEEP_ALIVE_SEC)
        self.internal_async_client_mock.set_username_password.assert_called_once_with(DUMMY_USERNAME, DUMMY_PASSWORD)

    def test_disable_metrics_collection_without_username_in_connect(self):
        self._configure_internal_async_client_connect(DUMMY_SUCCESS_RC)
        self._use_mock_python_event()
        self.python_event_mock.wait.return_value = True
        self.mqtt_core.disable_metrics_collection()
        self.mqtt_core.connect(DUMMY_KEEP_ALIVE_SEC)
        self.internal_async_client_mock.set_username_password.assert_called_once_with("", None)
        self.python_event_patcher.stop()

    def test_disable_metrics_collection_without_username_in_connect_asyc(self):
        self._configure_internal_async_client_connect(DUMMY_SUCCESS_RC)
        self.mqtt_core.disable_metrics_collection()
        self.mqtt_core.connect_async(DUMMY_KEEP_ALIVE_SEC)
        self.internal_async_client_mock.set_username_password.assert_called_once_with("", None)

    def test_connect_async_success_rc(self):
        expected_values = {
            KEY_EXPECTED_REQUEST_RC : DUMMY_SUCCESS_RC,
            KEY_EXPECTED_REQUEST_MID_OVERRIDE : FixedEventMids.CONNACK_MID
        }
        self._internal_test_async_api_with(RequestTypes.CONNECT, expected_values)

    def test_connect_async_failure_rc(self):
        expected_values = {
            KEY_EXPECTED_REQUEST_RC : DUMMY_FAILURE_RC,
            KEY_EXPECTED_REQUEST_MID_OVERRIDE : FixedEventMids.CONNACK_MID
        }
        self._internal_test_async_api_with(RequestTypes.CONNECT, expected_values)

    def test_connect_async_when_failure_rc_should_stop_event_consumer(self):
        self.internal_async_client_mock.connect.return_value = DUMMY_FAILURE_RC

        with pytest.raises(connectError):
            self.mqtt_core.connect_async(DUMMY_KEEP_ALIVE_SEC)

        self.event_consumer_mock.start.assert_called_once()
        self.event_consumer_mock.stop.assert_called_once()
        self.event_consumer_mock.wait_until_it_stops.assert_called_once()
        assert self.client_status_mock.set_status.call_count == 2
        assert self.client_status_mock.set_status.call_args_list == [call(ClientStatus.CONNECT), call(ClientStatus.IDLE)]

    def test_connect_async_when_exception_should_stop_event_consumer(self):
        self.internal_async_client_mock.connect.side_effect = Exception("Something weird happened")

        with pytest.raises(Exception):
            self.mqtt_core.connect_async(DUMMY_KEEP_ALIVE_SEC)

        self.event_consumer_mock.start.assert_called_once()
        self.event_consumer_mock.stop.assert_called_once()
        self.event_consumer_mock.wait_until_it_stops.assert_called_once()
        assert self.client_status_mock.set_status.call_count == 2
        assert self.client_status_mock.set_status.call_args_list == [call(ClientStatus.CONNECT), call(ClientStatus.IDLE)]

    def test_disconnect_async_success_rc(self):
        expected_values = {
            KEY_EXPECTED_REQUEST_RC : DUMMY_SUCCESS_RC,
            KEY_EXPECTED_REQUEST_MID_OVERRIDE : FixedEventMids.DISCONNECT_MID
        }
        self._internal_test_async_api_with(RequestTypes.DISCONNECT, expected_values)

    def test_disconnect_async_failure_rc(self):
        expected_values = {
            KEY_EXPECTED_REQUEST_RC : DUMMY_FAILURE_RC,
            KEY_EXPECTED_REQUEST_MID_OVERRIDE : FixedEventMids.DISCONNECT_MID
        }
        self._internal_test_async_api_with(RequestTypes.DISCONNECT, expected_values)

    def test_publish_async_success_rc(self):
        self._internal_test_async_api_with(RequestTypes.PUBLISH, SUCCESS_RC_EXPECTED_VALUES)

    def test_publish_async_failure_rc(self):
        self._internal_test_async_api_with(RequestTypes.PUBLISH, FAILURE_RC_EXPECTED_VALUES)

    def test_publish_async_queued(self):
        self._internal_test_async_api_with(RequestTypes.PUBLISH, QUEUED_EXPECTED_VALUES)

    def test_publish_async_queue_disabled(self):
        self._internal_test_async_api_with(RequestTypes.PUBLISH, QUEUE_DISABLED_EXPECTED_VALUES)

    def test_publish_async_queue_full(self):
        self._internal_test_async_api_with(RequestTypes.PUBLISH, QUEUE_FULL_EXPECTED_VALUES)

    def test_subscribe_async_success_rc(self):
        self._internal_test_async_api_with(RequestTypes.SUBSCRIBE, SUCCESS_RC_EXPECTED_VALUES)

    def test_subscribe_async_failure_rc(self):
        self._internal_test_async_api_with(RequestTypes.SUBSCRIBE, FAILURE_RC_EXPECTED_VALUES)

    def test_subscribe_async_queued(self):
        self._internal_test_async_api_with(RequestTypes.SUBSCRIBE, QUEUED_EXPECTED_VALUES)

    def test_subscribe_async_queue_full(self):
        self._internal_test_async_api_with(RequestTypes.SUBSCRIBE, QUEUE_FULL_EXPECTED_VALUES)

    def test_subscribe_async_queue_disabled(self):
        self._internal_test_async_api_with(RequestTypes.SUBSCRIBE, QUEUE_DISABLED_EXPECTED_VALUES)

    def test_unsubscribe_async_success_rc(self):
        self._internal_test_async_api_with(RequestTypes.UNSUBSCRIBE, SUCCESS_RC_EXPECTED_VALUES)

    def test_unsubscribe_async_failure_rc(self):
        self._internal_test_async_api_with(RequestTypes.UNSUBSCRIBE, FAILURE_RC_EXPECTED_VALUES)

    def test_unsubscribe_async_queued(self):
        self._internal_test_async_api_with(RequestTypes.UNSUBSCRIBE, QUEUED_EXPECTED_VALUES)

    def test_unsubscribe_async_queue_full(self):
        self._internal_test_async_api_with(RequestTypes.UNSUBSCRIBE, QUEUE_FULL_EXPECTED_VALUES)

    def test_unsubscribe_async_queue_disabled(self):
        self._internal_test_async_api_with(RequestTypes.UNSUBSCRIBE, QUEUE_DISABLED_EXPECTED_VALUES)

    def _internal_test_async_api_with(self, request_type, expected_values):
        expected_rc = expected_values.get(KEY_EXPECTED_REQUEST_RC)
        expected_append_result = expected_values.get(KEY_EXPECTED_QUEUE_APPEND_RESULT)
        expected_request_mid_override = expected_values.get(KEY_EXPECTED_REQUEST_MID_OVERRIDE)
        ack_callback = NonCallableMagicMock()
        message_callback = NonCallableMagicMock()

        if expected_rc is not None:
            self.configure_internal_async_client[request_type](self, expected_rc, DUMMY_REQUEST_MID)
            self.client_status_mock.get_status.return_value = ClientStatus.STABLE
            if expected_rc == DUMMY_SUCCESS_RC:
                mid = self.invoke_mqtt_core_async_api[request_type](self, ack_callback, message_callback)
                self.verify_mqtt_core_async_api[request_type](self, ack_callback, message_callback)
                if expected_request_mid_override is not None:
                    assert mid == expected_request_mid_override
                else:
                    assert mid == DUMMY_REQUEST_MID
            else:  # FAILURE_RC
                with pytest.raises(self.request_error[request_type]):
                    self.invoke_mqtt_core_async_api[request_type](self, ack_callback, message_callback)

        if expected_append_result is not None:
            self.client_status_mock.get_status.return_value = ClientStatus.ABNORMAL_DISCONNECT
            self.offline_requests_manager_mock.add_one.return_value = expected_append_result
            if expected_append_result == AppendResults.APPEND_SUCCESS:
                mid = self.invoke_mqtt_core_async_api[request_type](self, ack_callback, message_callback)
                assert mid == FixedEventMids.QUEUED_MID
            elif expected_append_result == AppendResults.APPEND_FAILURE_QUEUE_FULL:
                with pytest.raises(self.request_queue_full[request_type]):
                    self.invoke_mqtt_core_async_api[request_type](self, ack_callback, message_callback)
            else:  # AppendResults.APPEND_FAILURE_QUEUE_DISABLED
                with pytest.raises(self.request_queue_disable[request_type]):
                    self.invoke_mqtt_core_async_api[request_type](self, ack_callback, message_callback)

    def test_connect_success(self):
        expected_values = {
            KEY_EXPECTED_REQUEST_TIMEOUT : False,
            KEY_EXPECTED_REQUEST_MID_OVERRIDE : FixedEventMids.CONNACK_MID
        }
        self._internal_test_sync_api_with(RequestTypes.CONNECT, expected_values)

    def test_connect_timeout(self):
        expected_values = {
            KEY_EXPECTED_REQUEST_TIMEOUT : True,
            KEY_EXPECTED_REQUEST_MID_OVERRIDE : FixedEventMids.CONNACK_MID
        }
        self._internal_test_sync_api_with(RequestTypes.CONNECT, expected_values)

    def test_disconnect_success(self):
        expected_values = {
            KEY_EXPECTED_REQUEST_TIMEOUT : False,
            KEY_EXPECTED_REQUEST_MID_OVERRIDE : FixedEventMids.DISCONNECT_MID
        }
        self._internal_test_sync_api_with(RequestTypes.DISCONNECT, expected_values)

    def test_disconnect_timeout(self):
        expected_values = {
            KEY_EXPECTED_REQUEST_TIMEOUT : True,
            KEY_EXPECTED_REQUEST_MID_OVERRIDE : FixedEventMids.DISCONNECT_MID
        }
        self._internal_test_sync_api_with(RequestTypes.DISCONNECT, expected_values)

    def test_publish_success(self):
        self._internal_test_sync_api_with(RequestTypes.PUBLISH, NO_TIMEOUT_EXPECTED_VALUES)

    def test_publish_timeout(self):
        self._internal_test_sync_api_with(RequestTypes.PUBLISH, TIMEOUT_EXPECTED_VALUES)

    def test_publish_queued(self):
        self._internal_test_sync_api_with(RequestTypes.PUBLISH, QUEUED_EXPECTED_VALUES)

    def test_publish_queue_full(self):
        self._internal_test_sync_api_with(RequestTypes.PUBLISH, QUEUE_FULL_EXPECTED_VALUES)

    def test_publish_queue_disabled(self):
        self._internal_test_sync_api_with(RequestTypes.PUBLISH, QUEUE_DISABLED_EXPECTED_VALUES)

    def test_subscribe_success(self):
        self._internal_test_sync_api_with(RequestTypes.SUBSCRIBE, NO_TIMEOUT_EXPECTED_VALUES)

    def test_subscribe_timeout(self):
        self._internal_test_sync_api_with(RequestTypes.SUBSCRIBE, TIMEOUT_EXPECTED_VALUES)

    def test_subscribe_queued(self):
        self._internal_test_sync_api_with(RequestTypes.SUBSCRIBE, QUEUED_EXPECTED_VALUES)

    def test_subscribe_queue_full(self):
        self._internal_test_sync_api_with(RequestTypes.SUBSCRIBE, QUEUE_FULL_EXPECTED_VALUES)

    def test_subscribe_queue_disabled(self):
        self._internal_test_sync_api_with(RequestTypes.SUBSCRIBE, QUEUE_DISABLED_EXPECTED_VALUES)

    def test_unsubscribe_success(self):
        self._internal_test_sync_api_with(RequestTypes.UNSUBSCRIBE, NO_TIMEOUT_EXPECTED_VALUES)

    def test_unsubscribe_timeout(self):
        self._internal_test_sync_api_with(RequestTypes.UNSUBSCRIBE, TIMEOUT_EXPECTED_VALUES)

    def test_unsubscribe_queued(self):
        self._internal_test_sync_api_with(RequestTypes.UNSUBSCRIBE, QUEUED_EXPECTED_VALUES)

    def test_unsubscribe_queue_full(self):
        self._internal_test_sync_api_with(RequestTypes.UNSUBSCRIBE, QUEUE_FULL_EXPECTED_VALUES)

    def test_unsubscribe_queue_disabled(self):
        self._internal_test_sync_api_with(RequestTypes.UNSUBSCRIBE, QUEUE_DISABLED_EXPECTED_VALUES)

    def _internal_test_sync_api_with(self, request_type, expected_values):
        expected_request_mid = expected_values.get(KEY_EXPECTED_REQUEST_MID_OVERRIDE)
        expected_timeout = expected_values.get(KEY_EXPECTED_REQUEST_TIMEOUT)
        expected_append_result = expected_values.get(KEY_EXPECTED_QUEUE_APPEND_RESULT)

        if expected_request_mid is None:
            expected_request_mid = DUMMY_REQUEST_MID
        message_callback = NonCallableMagicMock()
        self.configure_internal_async_client[request_type](self, DUMMY_SUCCESS_RC, expected_request_mid)
        self._use_mock_python_event()

        if expected_timeout is not None:
            self.client_status_mock.get_status.return_value = ClientStatus.STABLE
            if expected_timeout:
                self.python_event_mock.wait.return_value = False
                with pytest.raises(self.request_timeout[request_type]):
                    self.invoke_mqtt_core_sync_api[request_type](self, message_callback)
            else:
                self.python_event_mock.wait.return_value = True
                assert self.invoke_mqtt_core_sync_api[request_type](self, message_callback) is True

        if expected_append_result is not None:
            self.client_status_mock.get_status.return_value = ClientStatus.ABNORMAL_DISCONNECT
            self.offline_requests_manager_mock.add_one.return_value = expected_append_result
            if expected_append_result == AppendResults.APPEND_SUCCESS:
                assert self.invoke_mqtt_core_sync_api[request_type](self, message_callback) is False
            elif expected_append_result == AppendResults.APPEND_FAILURE_QUEUE_FULL:
                with pytest.raises(self.request_queue_full[request_type]):
                    self.invoke_mqtt_core_sync_api[request_type](self, message_callback)
            else:
                with pytest.raises(self.request_queue_disable[request_type]):
                    self.invoke_mqtt_core_sync_api[request_type](self, message_callback)

        self.python_event_patcher.stop()

    def _use_mock_python_event(self):
        self.python_event_patcher = patch(PATCH_MODULE_LOCATION + "Event", spec=Event)
        self.python_event_constructor = self.python_event_patcher.start()
        self.python_event_mock = MagicMock()
        self.python_event_constructor.return_value = self.python_event_mock
