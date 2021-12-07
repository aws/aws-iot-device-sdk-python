from AWSIoTPythonSDK.core.protocol.internal.clients import InternalAsyncMqttClient
from AWSIoTPythonSDK.core.protocol.internal.events import FixedEventMids
from AWSIoTPythonSDK.core.util.providers import CertificateCredentialsProvider
from AWSIoTPythonSDK.core.util.providers import IAMCredentialsProvider
from AWSIoTPythonSDK.core.util.providers import EndpointProvider
from AWSIoTPythonSDK.core.util.providers import CiphersProvider
from AWSIoTPythonSDK.core.protocol.paho.client import MQTTv311
from AWSIoTPythonSDK.core.protocol.paho.client import Client
from AWSIoTPythonSDK.core.protocol.paho.client import MQTT_ERR_SUCCESS
from AWSIoTPythonSDK.core.protocol.paho.client import MQTT_ERR_ERRNO
try:
    from mock import patch
    from mock import MagicMock
    from mock import NonCallableMagicMock
except:
    from unittest.mock import patch
    from unittest.mock import MagicMock
    from unittest.mock import NonCallableMagicMock
import ssl
import pytest


DUMMY_CLIENT_ID = "CoolClientId"
FAKE_PATH = "/fake/path/"
DUMMY_CA_PATH = FAKE_PATH + "ca.crt"
DUMMY_CERT_PATH = FAKE_PATH + "cert.pem"
DUMMY_KEY_PATH = FAKE_PATH + "key.pem"
DUMMY_ACCESS_KEY_ID = "AccessKeyId"
DUMMY_SECRET_ACCESS_KEY = "SecretAccessKey"
DUMMY_SESSION_TOKEN = "SessionToken"
DUMMY_TOPIC = "topic/test"
DUMMY_PAYLOAD = "TestPayload"
DUMMY_QOS = 1
DUMMY_BASE_RECONNECT_QUIET_SEC = 1
DUMMY_MAX_RECONNECT_QUIET_SEC = 32
DUMMY_STABLE_CONNECTION_SEC = 20
DUMMY_ENDPOINT = "dummy.endpoint.com"
DUMMY_PORT = 8888
DUMMY_SUCCESS_RC = MQTT_ERR_SUCCESS
DUMMY_FAILURE_RC = MQTT_ERR_ERRNO
DUMMY_KEEP_ALIVE_SEC = 60
DUMMY_REQUEST_MID = 89757
DUMMY_USERNAME = "DummyUsername"
DUMMY_PASSWORD = "DummyPassword"
DUMMY_ALPN_PROTOCOLS = ["DummyALPNProtocol"]

KEY_GET_CA_PATH_CALL_COUNT = "get_ca_path_call_count"
KEY_GET_CERT_PATH_CALL_COUNT = "get_cert_path_call_count"
KEY_GET_KEY_PATH_CALL_COUNT = "get_key_path_call_count"

class TestClientsInternalAsyncClient:

    def setup_method(self, test_method):
        # We init a cert based client by default
        self.internal_async_client = InternalAsyncMqttClient(DUMMY_CLIENT_ID, False, MQTTv311, False)
        self._mock_internal_members()

    def _mock_internal_members(self):
        self.mock_paho_client = MagicMock(spec=Client)
        # TODO: See if we can replace the following with patch.object
        self.internal_async_client._paho_client = self.mock_paho_client

    def test_set_cert_credentials_provider_x509(self):
        mock_cert_credentials_provider = self._mock_cert_credentials_provider()
        cipher_provider = CiphersProvider()
        self.internal_async_client.set_cert_credentials_provider(mock_cert_credentials_provider, cipher_provider)

        expected_call_count = {
            KEY_GET_CA_PATH_CALL_COUNT : 1,
            KEY_GET_CERT_PATH_CALL_COUNT : 1,
            KEY_GET_KEY_PATH_CALL_COUNT : 1
        }
        self._verify_cert_credentials_provider(mock_cert_credentials_provider, expected_call_count)
        self.mock_paho_client.tls_set.assert_called_once_with(ca_certs=DUMMY_CA_PATH,
                                                              certfile=DUMMY_CERT_PATH,
                                                              keyfile=DUMMY_KEY_PATH,
                                                              cert_reqs=ssl.CERT_REQUIRED,
                                                              tls_version=ssl.PROTOCOL_SSLv23,
                                                              ciphers=cipher_provider.get_ciphers())

    def test_set_cert_credentials_provider_wss(self):
        self.internal_async_client = InternalAsyncMqttClient(DUMMY_CLIENT_ID, False, MQTTv311, True)
        self._mock_internal_members()
        mock_cert_credentials_provider = self._mock_cert_credentials_provider()
        cipher_provider = CiphersProvider()

        self.internal_async_client.set_cert_credentials_provider(mock_cert_credentials_provider, cipher_provider)

        expected_call_count = {
            KEY_GET_CA_PATH_CALL_COUNT : 1
        }
        self._verify_cert_credentials_provider(mock_cert_credentials_provider, expected_call_count)
        self.mock_paho_client.tls_set.assert_called_once_with(ca_certs=DUMMY_CA_PATH,
                                                              cert_reqs=ssl.CERT_REQUIRED,
                                                              tls_version=ssl.PROTOCOL_SSLv23,
                                                              ciphers=cipher_provider.get_ciphers())

    def _mock_cert_credentials_provider(self):
        mock_cert_credentials_provider = MagicMock(spec=CertificateCredentialsProvider)
        mock_cert_credentials_provider.get_ca_path.return_value = DUMMY_CA_PATH
        mock_cert_credentials_provider.get_cert_path.return_value = DUMMY_CERT_PATH
        mock_cert_credentials_provider.get_key_path.return_value = DUMMY_KEY_PATH
        return mock_cert_credentials_provider

    def _verify_cert_credentials_provider(self, mock_cert_credentials_provider, expected_values):
        expected_get_ca_path_call_count = expected_values.get(KEY_GET_CA_PATH_CALL_COUNT)
        expected_get_cert_path_call_count = expected_values.get(KEY_GET_CERT_PATH_CALL_COUNT)
        expected_get_key_path_call_count = expected_values.get(KEY_GET_KEY_PATH_CALL_COUNT)

        if expected_get_ca_path_call_count is not None:
            assert mock_cert_credentials_provider.get_ca_path.call_count == expected_get_ca_path_call_count
        if expected_get_cert_path_call_count is not None:
            assert mock_cert_credentials_provider.get_cert_path.call_count == expected_get_cert_path_call_count
        if expected_get_key_path_call_count is not None:
            assert mock_cert_credentials_provider.get_key_path.call_count == expected_get_key_path_call_count

    def test_set_iam_credentials_provider(self):
        self.internal_async_client = InternalAsyncMqttClient(DUMMY_CLIENT_ID, False, MQTTv311, True)
        self._mock_internal_members()
        mock_iam_credentials_provider = self._mock_iam_credentials_provider()

        self.internal_async_client.set_iam_credentials_provider(mock_iam_credentials_provider)

        self._verify_iam_credentials_provider(mock_iam_credentials_provider)

    def _mock_iam_credentials_provider(self):
        mock_iam_credentials_provider = MagicMock(spec=IAMCredentialsProvider)
        mock_iam_credentials_provider.get_ca_path.return_value = DUMMY_CA_PATH
        mock_iam_credentials_provider.get_access_key_id.return_value = DUMMY_ACCESS_KEY_ID
        mock_iam_credentials_provider.get_secret_access_key.return_value = DUMMY_SECRET_ACCESS_KEY
        mock_iam_credentials_provider.get_session_token.return_value = DUMMY_SESSION_TOKEN
        return mock_iam_credentials_provider

    def _verify_iam_credentials_provider(self, mock_iam_credentials_provider):
        assert mock_iam_credentials_provider.get_access_key_id.call_count == 1
        assert mock_iam_credentials_provider.get_secret_access_key.call_count == 1
        assert mock_iam_credentials_provider.get_session_token.call_count == 1

    def test_configure_last_will(self):
        self.internal_async_client.configure_last_will(DUMMY_TOPIC, DUMMY_PAYLOAD, DUMMY_QOS)
        self.mock_paho_client.will_set.assert_called_once_with(DUMMY_TOPIC,
                                                               DUMMY_PAYLOAD,
                                                               DUMMY_QOS,
                                                               False)

    def test_clear_last_will(self):
        self.internal_async_client.clear_last_will()
        assert self.mock_paho_client.will_clear.call_count == 1

    def test_set_username_password(self):
        self.internal_async_client.set_username_password(DUMMY_USERNAME, DUMMY_PASSWORD)
        self.mock_paho_client.username_pw_set.assert_called_once_with(DUMMY_USERNAME, DUMMY_PASSWORD)

    def test_configure_reconnect_back_off(self):
        self.internal_async_client.configure_reconnect_back_off(DUMMY_BASE_RECONNECT_QUIET_SEC,
                                                                DUMMY_MAX_RECONNECT_QUIET_SEC,
                                                                DUMMY_STABLE_CONNECTION_SEC)
        self.mock_paho_client.setBackoffTiming.assert_called_once_with(DUMMY_BASE_RECONNECT_QUIET_SEC,
                                                                DUMMY_MAX_RECONNECT_QUIET_SEC,
                                                                DUMMY_STABLE_CONNECTION_SEC)
    def test_configure_alpn_protocols(self):
        self.internal_async_client.configure_alpn_protocols(DUMMY_ALPN_PROTOCOLS)
        self.mock_paho_client.config_alpn_protocols.assert_called_once_with(DUMMY_ALPN_PROTOCOLS)

    def test_connect_success_rc(self):
        self._internal_test_connect_with_rc(DUMMY_SUCCESS_RC)

    def test_connect_failure_rc(self):
        self._internal_test_connect_with_rc(DUMMY_FAILURE_RC)

    def _internal_test_connect_with_rc(self, expected_connect_rc):
        mock_endpoint_provider = self._mock_endpoint_provider()
        self.mock_paho_client.connect.return_value = expected_connect_rc
        self.internal_async_client.set_endpoint_provider(mock_endpoint_provider)

        actual_rc = self.internal_async_client.connect(DUMMY_KEEP_ALIVE_SEC)

        assert mock_endpoint_provider.get_host.call_count == 1
        assert mock_endpoint_provider.get_port.call_count == 1
        event_callback_map = self.internal_async_client.get_event_callback_map()
        assert len(event_callback_map) == 3
        assert event_callback_map[FixedEventMids.CONNACK_MID] is not None
        assert event_callback_map[FixedEventMids.DISCONNECT_MID] is not None
        assert event_callback_map[FixedEventMids.MESSAGE_MID] is not None
        assert self.mock_paho_client.connect.call_count == 1
        if expected_connect_rc == MQTT_ERR_SUCCESS:
            assert self.mock_paho_client.loop_start.call_count == 1
        else:
            assert self.mock_paho_client.loop_start.call_count == 0
        assert actual_rc == expected_connect_rc

    def _mock_endpoint_provider(self):
        mock_endpoint_provider = MagicMock(spec=EndpointProvider)
        mock_endpoint_provider.get_host.return_value = DUMMY_ENDPOINT
        mock_endpoint_provider.get_port.return_value = DUMMY_PORT
        return mock_endpoint_provider

    def test_start_background_network_io(self):
        self.internal_async_client.start_background_network_io()
        assert self.mock_paho_client.loop_start.call_count == 1

    def test_stop_background_network_io(self):
        self.internal_async_client.stop_background_network_io()
        assert self.mock_paho_client.loop_stop.call_count == 1

    def test_disconnect_success_rc(self):
        self._internal_test_disconnect_with_rc(DUMMY_SUCCESS_RC)

    def test_disconnect_failure_rc(self):
        self._internal_test_disconnect_with_rc(DUMMY_FAILURE_RC)

    def _internal_test_disconnect_with_rc(self, expected_disconnect_rc):
        self.mock_paho_client.disconnect.return_value = expected_disconnect_rc

        actual_rc = self.internal_async_client.disconnect()

        event_callback_map = self.internal_async_client.get_event_callback_map()
        assert self.mock_paho_client.disconnect.call_count == 1
        if expected_disconnect_rc == MQTT_ERR_SUCCESS:
            # Since we only call disconnect, there should be only one registered callback
            assert len(event_callback_map) == 1
            assert event_callback_map[FixedEventMids.DISCONNECT_MID] is not None
        else:
            assert len(event_callback_map) == 0
        assert actual_rc == expected_disconnect_rc

    def test_publish_qos0_success_rc(self):
        self._internal_test_publish_with(0, DUMMY_REQUEST_MID, DUMMY_SUCCESS_RC)
        self._internal_test_publish_with(0, DUMMY_REQUEST_MID, DUMMY_SUCCESS_RC, NonCallableMagicMock())

    def test_publish_qos0_failure_rc(self):
        self._internal_test_publish_with(0, DUMMY_REQUEST_MID, DUMMY_FAILURE_RC)
        self._internal_test_publish_with(0, DUMMY_REQUEST_MID, DUMMY_FAILURE_RC, NonCallableMagicMock())

    def test_publish_qos1_success_rc(self):
        self._internal_test_publish_with(1, DUMMY_REQUEST_MID, DUMMY_SUCCESS_RC)
        self._internal_test_publish_with(1, DUMMY_REQUEST_MID, DUMMY_SUCCESS_RC, NonCallableMagicMock())

    def test_publish_qos1_failure_rc(self):
        self._internal_test_publish_with(1, DUMMY_REQUEST_MID, DUMMY_FAILURE_RC)
        self._internal_test_publish_with(1, DUMMY_REQUEST_MID, DUMMY_FAILURE_RC, NonCallableMagicMock())

    def _internal_test_publish_with(self, qos, expected_mid, expected_rc, expected_callback=None):
        self.mock_paho_client.publish.return_value = expected_rc, expected_mid

        actual_rc, actual_mid = self.internal_async_client.publish(DUMMY_TOPIC,
                                                                   DUMMY_PAYLOAD,
                                                                   qos,
                                                                   retain=False,
                                                                   ack_callback=expected_callback)

        self._verify_event_callback_map_for_pub_sub_unsub(expected_rc, expected_mid, qos, expected_callback)
        assert actual_rc == expected_rc
        assert actual_mid == expected_mid

    def test_subscribe_success_rc(self):
        self._internal_test_subscribe_with(DUMMY_REQUEST_MID, DUMMY_SUCCESS_RC)
        self._internal_test_subscribe_with(DUMMY_REQUEST_MID, DUMMY_SUCCESS_RC, NonCallableMagicMock())

    def test_subscribe_failure_rc(self):
        self._internal_test_subscribe_with(DUMMY_REQUEST_MID, DUMMY_FAILURE_RC)
        self._internal_test_subscribe_with(DUMMY_REQUEST_MID, DUMMY_FAILURE_RC, NonCallableMagicMock())

    def _internal_test_subscribe_with(self, expected_mid, expected_rc, expected_callback=None):
        self.mock_paho_client.subscribe.return_value = expected_rc, expected_mid

        actual_rc, actual_mid = self.internal_async_client.subscribe(DUMMY_TOPIC, DUMMY_QOS, expected_callback)

        self._verify_event_callback_map_for_pub_sub_unsub(expected_rc, expected_mid, qos=None, callback=expected_callback)
        assert actual_rc == expected_rc
        assert actual_mid == expected_mid

    def test_unsubscribe_success_rc(self):
        self._internal_test_unsubscribe_with(DUMMY_REQUEST_MID, DUMMY_SUCCESS_RC)
        self._internal_test_unsubscribe_with(DUMMY_REQUEST_MID, DUMMY_SUCCESS_RC, NonCallableMagicMock())

    def test_unsubscribe_failure_rc(self):
        self._internal_test_unsubscribe_with(DUMMY_REQUEST_MID, DUMMY_FAILURE_RC)
        self._internal_test_publish_with(DUMMY_REQUEST_MID, DUMMY_FAILURE_RC, NonCallableMagicMock())

    def _internal_test_unsubscribe_with(self, expected_mid, expected_rc, expected_callback=None):
        self.mock_paho_client.unsubscribe.return_value = expected_rc, expected_mid

        actual_rc, actual_mid = self.internal_async_client.unsubscribe(DUMMY_TOPIC, expected_callback)

        self._verify_event_callback_map_for_pub_sub_unsub(expected_rc, expected_mid, qos=None, callback=expected_callback)
        assert actual_rc == expected_rc
        assert actual_mid == expected_mid

    def _verify_event_callback_map_for_pub_sub_unsub(self, expected_rc, expected_mid, qos=None, callback=None):
        event_callback_map = self.internal_async_client.get_event_callback_map()
        should_have_callback_in_map = expected_rc == DUMMY_SUCCESS_RC and callback
        if qos is not None:
            should_have_callback_in_map = should_have_callback_in_map and qos > 0

        if should_have_callback_in_map:
            # Since we only perform this request, there should be only one registered callback
            assert len(event_callback_map) == 1
            assert event_callback_map[expected_mid] == callback
        else:
            assert len(event_callback_map) == 0

    def test_register_internal_event_callbacks(self):
        expected_callback = NonCallableMagicMock()
        self.internal_async_client.register_internal_event_callbacks(expected_callback,
                                                                     expected_callback,
                                                                     expected_callback,
                                                                     expected_callback,
                                                                     expected_callback,
                                                                     expected_callback)
        self._verify_internal_event_callbacks(expected_callback)

    def test_unregister_internal_event_callbacks(self):
        self.internal_async_client.unregister_internal_event_callbacks()
        self._verify_internal_event_callbacks(None)

    def _verify_internal_event_callbacks(self, expected_callback):
        assert self.mock_paho_client.on_connect == expected_callback
        assert self.mock_paho_client.on_disconnect == expected_callback
        assert self.mock_paho_client.on_publish == expected_callback
        assert self.mock_paho_client.on_subscribe == expected_callback
        assert self.mock_paho_client.on_unsubscribe == expected_callback
        assert self.mock_paho_client.on_message == expected_callback

    def test_invoke_event_callback_fixed_request(self):
        # We use disconnect as an example for fixed request to "register" and event callback
        self.mock_paho_client.disconnect.return_value = DUMMY_SUCCESS_RC
        event_callback = MagicMock()
        rc = self.internal_async_client.disconnect(event_callback)
        self.internal_async_client.invoke_event_callback(FixedEventMids.DISCONNECT_MID, rc)

        event_callback.assert_called_once_with(FixedEventMids.DISCONNECT_MID, rc)
        event_callback_map = self.internal_async_client.get_event_callback_map()
        assert len(event_callback_map) == 1  # Fixed request event callback never gets removed
        assert event_callback_map[FixedEventMids.DISCONNECT_MID] is not None

    def test_invoke_event_callback_non_fixed_request(self):
        # We use unsubscribe as an example for non-fixed request to "register" an event callback
        self.mock_paho_client.unsubscribe.return_value = DUMMY_SUCCESS_RC, DUMMY_REQUEST_MID
        event_callback = MagicMock()
        rc, mid = self.internal_async_client.unsubscribe(DUMMY_TOPIC, event_callback)
        self.internal_async_client.invoke_event_callback(mid)

        event_callback.assert_called_once_with(mid=mid)
        event_callback_map = self.internal_async_client.get_event_callback_map()
        assert len(event_callback_map) == 0  # Non-fixed request event callback gets removed after successfully invoked

    @pytest.mark.timeout(3)
    def test_invoke_event_callback_that_has_client_api_call(self):
        # We use subscribe and publish on SUBACK as an example of having client API call within event callbacks
        self.mock_paho_client.subscribe.return_value = DUMMY_SUCCESS_RC, DUMMY_REQUEST_MID
        self.mock_paho_client.publish.return_value = DUMMY_SUCCESS_RC, DUMMY_REQUEST_MID + 1
        rc, mid = self.internal_async_client.subscribe(DUMMY_TOPIC, DUMMY_QOS, ack_callback=self._publish_on_suback)

        self.internal_async_client.invoke_event_callback(mid, (DUMMY_QOS,))

        event_callback_map = self.internal_async_client.get_event_callback_map()
        assert len(event_callback_map) == 0

    def _publish_on_suback(self, mid, data):
        self.internal_async_client.publish(DUMMY_TOPIC, DUMMY_PAYLOAD, DUMMY_QOS)

    def test_remove_event_callback(self):
        # We use unsubscribe as an example for non-fixed request to "register" an event callback
        self.mock_paho_client.unsubscribe.return_value = DUMMY_SUCCESS_RC, DUMMY_REQUEST_MID
        event_callback = MagicMock()
        rc, mid = self.internal_async_client.unsubscribe(DUMMY_TOPIC, event_callback)

        event_callback_map = self.internal_async_client.get_event_callback_map()
        assert len(event_callback_map) == 1

        self.internal_async_client.remove_event_callback(mid)
        assert len(event_callback_map) == 0

    def test_clean_up_event_callbacks(self):
        # We use unsubscribe as an example for on-fixed request to "register" an event callback
        self.mock_paho_client.unsubscribe.return_value = DUMMY_SUCCESS_RC, DUMMY_REQUEST_MID
        # We use disconnect as an example for fixed request to "register" and event callback
        self.mock_paho_client.disconnect.return_value = DUMMY_SUCCESS_RC
        event_callback = MagicMock()
        self.internal_async_client.unsubscribe(DUMMY_TOPIC, event_callback)
        self.internal_async_client.disconnect(event_callback)

        event_callback_map = self.internal_async_client.get_event_callback_map()
        assert len(event_callback_map) == 2

        self.internal_async_client.clean_up_event_callbacks()
        assert len(event_callback_map) == 0
