# Test shadow behavior for a single device shadow

from AWSIoTPythonSDK.core.shadow.deviceShadow import deviceShadow
from AWSIoTPythonSDK.core.shadow.shadowManager import shadowManager
from AWSIoTPythonSDK.core.protocol.paho.client import MQTTMessage
import time
import json
try:
    from mock import MagicMock
except:
    from unittest.mock import MagicMock


DUMMY_THING_NAME = "CoolThing"
DUMMY_SHADOW_OP_TIME_OUT_SEC = 3

SHADOW_OP_TYPE_GET = "get"
SHADOW_OP_TYPE_DELETE = "delete"
SHADOW_OP_TYPE_UPDATE = "update"
SHADOW_OP_RESPONSE_STATUS_ACCEPTED = "accepted"
SHADOW_OP_RESPONSE_STATUS_REJECTED = "rejected"
SHADOW_OP_RESPONSE_STATUS_TIMEOUT = "timeout"
SHADOW_OP_RESPONSE_STATUS_DELTA = "delta"

SHADOW_TOPIC_PREFIX = "$aws/things/"
SHADOW_TOPIC_GET_ACCEPTED = SHADOW_TOPIC_PREFIX + DUMMY_THING_NAME + "/shadow/get/accepted"
SHADOW_TOPIC_GET_REJECTED = SHADOW_TOPIC_PREFIX + DUMMY_THING_NAME + "/shadow/get/rejected"
SHADOW_TOPIC_DELETE_ACCEPTED = SHADOW_TOPIC_PREFIX + DUMMY_THING_NAME + "/shadow/delete/accepted"
SHADOW_TOPIC_DELETE_REJECTED = SHADOW_TOPIC_PREFIX + DUMMY_THING_NAME + "/shadow/delete/rejected"
SHADOW_TOPIC_UPDATE_ACCEPTED = SHADOW_TOPIC_PREFIX + DUMMY_THING_NAME + "/shadow/update/accepted"
SHADOW_TOPIC_UPDATE_REJECTED = SHADOW_TOPIC_PREFIX + DUMMY_THING_NAME + "/shadow/update/rejected"
SHADOW_TOPIC_UPDATE_DELTA = SHADOW_TOPIC_PREFIX + DUMMY_THING_NAME + "/shadow/update/delta"
SHADOW_RESPONSE_PAYLOAD_TIMEOUT = "REQUEST TIME OUT"

VALUE_OVERRIDE_KEY_INBOUND_PAYLOAD = "InBoundPayload"
VALUE_OVERRIDE_KEY_OUTBOUND_PAYLOAD = "OutBoundPayload"

GARBAGE_PAYLOAD = b"ThisIsGarbagePayload!"

VALUE_OVERRIDE_GARBAGE_INBOUND_PAYLOAD = {
    VALUE_OVERRIDE_KEY_INBOUND_PAYLOAD : GARBAGE_PAYLOAD
}


class TestDeviceShadow:

    def setup_class(cls):
        cls.invoke_shadow_operation = {
            SHADOW_OP_TYPE_GET : cls._invoke_shadow_get,
            SHADOW_OP_TYPE_DELETE : cls._invoke_shadow_delete,
            SHADOW_OP_TYPE_UPDATE : cls._invoke_shadow_update
        }
        cls._get_topics = {
            SHADOW_OP_RESPONSE_STATUS_ACCEPTED : SHADOW_TOPIC_GET_ACCEPTED,
            SHADOW_OP_RESPONSE_STATUS_REJECTED : SHADOW_TOPIC_GET_REJECTED,
        }
        cls._delete_topics = {
            SHADOW_OP_RESPONSE_STATUS_ACCEPTED : SHADOW_TOPIC_DELETE_ACCEPTED,
            SHADOW_OP_RESPONSE_STATUS_REJECTED : SHADOW_TOPIC_DELETE_REJECTED
        }
        cls._update_topics = {
            SHADOW_OP_RESPONSE_STATUS_ACCEPTED : SHADOW_TOPIC_UPDATE_ACCEPTED,
            SHADOW_OP_RESPONSE_STATUS_REJECTED : SHADOW_TOPIC_UPDATE_REJECTED,
            SHADOW_OP_RESPONSE_STATUS_DELTA : SHADOW_TOPIC_UPDATE_DELTA
        }
        cls.shadow_topics = {
            SHADOW_OP_TYPE_GET : cls._get_topics,
            SHADOW_OP_TYPE_DELETE : cls._delete_topics,
            SHADOW_OP_TYPE_UPDATE : cls._update_topics
        }

    def _invoke_shadow_get(self):
        return self.device_shadow_handler.shadowGet(self.shadow_callback, DUMMY_SHADOW_OP_TIME_OUT_SEC)

    def _invoke_shadow_delete(self):
        return self.device_shadow_handler.shadowDelete(self.shadow_callback, DUMMY_SHADOW_OP_TIME_OUT_SEC)

    def _invoke_shadow_update(self):
        return self.device_shadow_handler.shadowUpdate("{}", self.shadow_callback, DUMMY_SHADOW_OP_TIME_OUT_SEC)

    def setup_method(self, method):
        self.shadow_manager_mock = MagicMock(spec=shadowManager)
        self.shadow_callback = MagicMock()
        self._create_device_shadow_handler()  # Create device shadow handler with persistent subscribe by default

    def _create_device_shadow_handler(self, is_persistent_subscribe=True):
        self.device_shadow_handler = deviceShadow(DUMMY_THING_NAME, is_persistent_subscribe, self.shadow_manager_mock)

    # Shadow delta
    def test_register_delta_callback_older_version_should_not_invoke(self):
        self.device_shadow_handler.shadowRegisterDeltaCallback(self.shadow_callback)
        self._fake_incoming_delta_message_with(version=3)

        # Make next delta message with an old version
        self._fake_incoming_delta_message_with(version=1)

        assert self.shadow_callback.call_count == 1  # Once time from the previous delta message

    def test_unregister_delta_callback_should_not_invoke_after(self):
        self.device_shadow_handler.shadowRegisterDeltaCallback(self.shadow_callback)
        fake_delta_message = self._fake_incoming_delta_message_with(version=3)
        self.shadow_callback.assert_called_once_with(fake_delta_message.payload.decode("utf-8"),
                                                     SHADOW_OP_RESPONSE_STATUS_DELTA + "/" + DUMMY_THING_NAME,
                                                     None)

        # Now we unregister
        self.device_shadow_handler.shadowUnregisterDeltaCallback()
        self._fake_incoming_delta_message_with(version=5)
        assert self.shadow_callback.call_count == 1  # One time from the previous delta message

    def test_register_delta_callback_newer_version_should_invoke(self):
        self.device_shadow_handler.shadowRegisterDeltaCallback(self.shadow_callback)
        fake_delta_message = self._fake_incoming_delta_message_with(version=300)

        self.shadow_callback.assert_called_once_with(fake_delta_message.payload.decode("utf-8"),
                                                     SHADOW_OP_RESPONSE_STATUS_DELTA + "/" + DUMMY_THING_NAME,
                                                     None)

    def test_register_delta_callback_no_version_should_not_invoke(self):
        self.device_shadow_handler.shadowRegisterDeltaCallback(self.shadow_callback)
        self._fake_incoming_delta_message_with(version=None)

        assert self.shadow_callback.call_count == 0

    def _fake_incoming_delta_message_with(self, version):
        fake_delta_message = self._create_fake_shadow_response(SHADOW_TOPIC_UPDATE_DELTA,
                                                               self._create_simple_payload(token=None, version=version))
        self.device_shadow_handler.generalCallback(None, None, fake_delta_message)
        time.sleep(1)  # Callback executed in another thread, wait to make sure the artifacts are generated
        return fake_delta_message

    # Shadow get
    def test_persistent_shadow_get_accepted(self):
        self._internal_test_persistent_shadow_operation(SHADOW_OP_TYPE_GET, SHADOW_OP_RESPONSE_STATUS_ACCEPTED)

    def test_persistent_shadow_get_rejected(self):
        self._internal_test_persistent_shadow_operation(SHADOW_OP_TYPE_GET, SHADOW_OP_RESPONSE_STATUS_REJECTED)

    def test_persistent_shadow_get_time_out(self):
        self._internal_test_persistent_shadow_operation(SHADOW_OP_TYPE_GET, SHADOW_OP_RESPONSE_STATUS_TIMEOUT)

    def test_persistent_shadow_get_garbage_response_should_time_out(self):
        self._internal_test_persistent_shadow_operation(SHADOW_OP_TYPE_GET,
                                                        SHADOW_OP_RESPONSE_STATUS_ACCEPTED,
                                                        value_override=VALUE_OVERRIDE_GARBAGE_INBOUND_PAYLOAD)

    def test_non_persistent_shadow_get_accepted(self):
        self._internal_test_non_persistent_shadow_operation(SHADOW_OP_TYPE_GET, SHADOW_OP_RESPONSE_STATUS_ACCEPTED)

    def test_non_persistent_shadow_get_rejected(self):
        self._internal_test_non_persistent_shadow_operation(SHADOW_OP_TYPE_GET, SHADOW_OP_RESPONSE_STATUS_REJECTED)

    def test_non_persistent_shadow_get_time_out(self):
        self._internal_test_non_persistent_shadow_operation(SHADOW_OP_TYPE_GET, SHADOW_OP_RESPONSE_STATUS_TIMEOUT)

    def test_non_persistent_shadow_get_garbage_response_should_time_out(self):
        self._internal_test_non_persistent_shadow_operation(SHADOW_OP_TYPE_GET,
                                                            SHADOW_OP_RESPONSE_STATUS_ACCEPTED,
                                                            value_override=VALUE_OVERRIDE_GARBAGE_INBOUND_PAYLOAD)

    # Shadow delete
    def test_persistent_shadow_delete_accepted(self):
        self._internal_test_persistent_shadow_operation(SHADOW_OP_TYPE_DELETE, SHADOW_OP_RESPONSE_STATUS_ACCEPTED)

    def test_persistent_shadow_delete_rejected(self):
        self._internal_test_persistent_shadow_operation(SHADOW_OP_TYPE_DELETE, SHADOW_OP_RESPONSE_STATUS_REJECTED)

    def test_persistent_shadow_delete_time_out(self):
        self._internal_test_persistent_shadow_operation(SHADOW_OP_TYPE_DELETE, SHADOW_OP_RESPONSE_STATUS_TIMEOUT)

    def test_persistent_shadow_delete_garbage_response_should_time_out(self):
        self._internal_test_persistent_shadow_operation(SHADOW_OP_TYPE_DELETE,
                                                        SHADOW_OP_RESPONSE_STATUS_ACCEPTED,
                                                        value_override=VALUE_OVERRIDE_GARBAGE_INBOUND_PAYLOAD)

    def test_non_persistent_shadow_delete_accepted(self):
        self._internal_test_non_persistent_shadow_operation(SHADOW_OP_TYPE_DELETE, SHADOW_OP_RESPONSE_STATUS_ACCEPTED)

    def test_non_persistent_shadow_delete_rejected(self):
        self._internal_test_non_persistent_shadow_operation(SHADOW_OP_TYPE_DELETE, SHADOW_OP_RESPONSE_STATUS_REJECTED)

    def test_non_persistent_shadow_delete_time_out(self):
        self._internal_test_non_persistent_shadow_operation(SHADOW_OP_TYPE_DELETE, SHADOW_OP_RESPONSE_STATUS_TIMEOUT)

    def test_non_persistent_shadow_delete_garbage_response_should_time_out(self):
        self._internal_test_non_persistent_shadow_operation(SHADOW_OP_TYPE_DELETE,
                                                            SHADOW_OP_RESPONSE_STATUS_ACCEPTED,
                                                            value_override=VALUE_OVERRIDE_GARBAGE_INBOUND_PAYLOAD)

    # Shadow update
    def test_persistent_shadow_update_accepted(self):
        self._internal_test_persistent_shadow_operation(SHADOW_OP_TYPE_UPDATE, SHADOW_OP_RESPONSE_STATUS_ACCEPTED)

    def test_persistent_shadow_update_rejected(self):
        self._internal_test_persistent_shadow_operation(SHADOW_OP_TYPE_UPDATE, SHADOW_OP_RESPONSE_STATUS_REJECTED)

    def test_persistent_shadow_update_time_out(self):
        self._internal_test_persistent_shadow_operation(SHADOW_OP_TYPE_UPDATE, SHADOW_OP_RESPONSE_STATUS_TIMEOUT)

    def test_persistent_shadow_update_garbage_response_should_time_out(self):
        self._internal_test_persistent_shadow_operation(SHADOW_OP_TYPE_UPDATE,
                                                        SHADOW_OP_RESPONSE_STATUS_ACCEPTED,
                                                        value_override=VALUE_OVERRIDE_GARBAGE_INBOUND_PAYLOAD)

    def test_non_persistent_shadow_update_accepted(self):
        self._internal_test_non_persistent_shadow_operation(SHADOW_OP_TYPE_UPDATE, SHADOW_OP_RESPONSE_STATUS_ACCEPTED)

    def test_non_persistent_shadow_update_rejected(self):
        self._internal_test_non_persistent_shadow_operation(SHADOW_OP_TYPE_UPDATE, SHADOW_OP_RESPONSE_STATUS_REJECTED)

    def test_non_persistent_shadow_update_time_out(self):
        self._internal_test_non_persistent_shadow_operation(SHADOW_OP_TYPE_UPDATE, SHADOW_OP_RESPONSE_STATUS_TIMEOUT)

    def test_non_persistent_shadow_update_garbage_response_should_time_out(self):
        self._internal_test_non_persistent_shadow_operation(SHADOW_OP_TYPE_UPDATE,
                                                            SHADOW_OP_RESPONSE_STATUS_ACCEPTED,
                                                            value_override=VALUE_OVERRIDE_GARBAGE_INBOUND_PAYLOAD)

    def _internal_test_non_persistent_shadow_operation(self, operation_type, operation_response_type, value_override=None):
        self._create_device_shadow_handler(is_persistent_subscribe=False)
        token = self.invoke_shadow_operation[operation_type](self)
        inbound_payload, wait_time_sec, expected_response_type, expected_shadow_response_payload = \
            self._prepare_test_values(token, operation_response_type, value_override)
        expected_shadow_response_payload = \
            self._invoke_shadow_general_callback_on_demand(operation_type, operation_response_type,
                                                           (inbound_payload, wait_time_sec, expected_shadow_response_payload))

        self._assert_first_call_correct(operation_type, (token, expected_response_type, expected_shadow_response_payload))

    def _internal_test_persistent_shadow_operation(self, operation_type, operation_response_type, value_override=None):
        token = self.invoke_shadow_operation[operation_type](self)
        inbound_payload, wait_time_sec, expected_response_type, expected_shadow_response_payload = \
            self._prepare_test_values(token, operation_response_type, value_override)
        expected_shadow_response_payload = \
            self._invoke_shadow_general_callback_on_demand(operation_type, operation_response_type,
                                                           (inbound_payload, wait_time_sec, expected_shadow_response_payload))

        self._assert_first_call_correct(operation_type,
                                        (token, expected_response_type, expected_shadow_response_payload),
                                        is_persistent=True)

    def _prepare_test_values(self, token, operation_response_type, value_override):
        inbound_payload = None
        if value_override:
            inbound_payload = value_override.get(VALUE_OVERRIDE_KEY_INBOUND_PAYLOAD)
        if inbound_payload is None:
            inbound_payload = self._create_simple_payload(token, version=3)  # Should be bytes in Py3
        if inbound_payload == GARBAGE_PAYLOAD:
            expected_shadow_response_payload = SHADOW_RESPONSE_PAYLOAD_TIMEOUT
            wait_time_sec = DUMMY_SHADOW_OP_TIME_OUT_SEC + 1
            expected_response_type = SHADOW_OP_RESPONSE_STATUS_TIMEOUT
        else:
            expected_shadow_response_payload = inbound_payload.decode("utf-8")  # Should always be str in Py2/3
            wait_time_sec = 1
            expected_response_type = operation_response_type

        return inbound_payload, wait_time_sec, expected_response_type, expected_shadow_response_payload

    def _invoke_shadow_general_callback_on_demand(self, operation_type, operation_response_type, data):
        inbound_payload, wait_time_sec, expected_shadow_response_payload = data

        if operation_response_type == SHADOW_OP_RESPONSE_STATUS_TIMEOUT:
            time.sleep(DUMMY_SHADOW_OP_TIME_OUT_SEC + 1)  # Make it time out for sure
            return SHADOW_RESPONSE_PAYLOAD_TIMEOUT
        else:
            fake_shadow_response = self._create_fake_shadow_response(self.shadow_topics[operation_type][operation_response_type],
                                                                     inbound_payload)
            self.device_shadow_handler.generalCallback(None, None, fake_shadow_response)
            time.sleep(wait_time_sec)  # Callback executed in another thread, wait to make sure the artifacts are generated
            return expected_shadow_response_payload

    def _assert_first_call_correct(self, operation_type, expected_data, is_persistent=False):
        token, expected_response_type, expected_shadow_response_payload = expected_data

        self.shadow_manager_mock.basicShadowSubscribe.assert_called_once_with(DUMMY_THING_NAME, operation_type,
                                                                              self.device_shadow_handler.generalCallback)
        self.shadow_manager_mock.basicShadowPublish.\
            assert_called_once_with(DUMMY_THING_NAME,
                                    operation_type,
                                    self._create_simple_payload(token, version=None).decode("utf-8"))
        self.shadow_callback.assert_called_once_with(expected_shadow_response_payload, expected_response_type, token)
        if not is_persistent:
            self.shadow_manager_mock.basicShadowUnsubscribe.assert_called_once_with(DUMMY_THING_NAME, operation_type)

    def _create_fake_shadow_response(self, topic, payload):
        response = MQTTMessage()
        response.topic = topic
        response.payload = payload
        return response

    def _create_simple_payload(self, token, version):
        payload_object = dict()
        if token is not None:
            payload_object["clientToken"] = token
        if version is not None:
            payload_object["version"] = version
        return json.dumps(payload_object).encode("utf-8")
