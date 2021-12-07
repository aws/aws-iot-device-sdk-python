from AWSIoTPythonSDK.core.protocol.mqtt_core import MqttCore
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
from AWSIoTPythonSDK.MQTTLib import DROP_NEWEST
try:
    from mock import patch
    from mock import MagicMock
except:
    from unittest.mock import patch
    from unittest.mock import MagicMock


PATCH_MODULE_LOCATION = "AWSIoTPythonSDK.MQTTLib."
CLIENT_ID = "DefaultClientId"
SHADOW_CLIENT_ID = "DefaultShadowClientId"
DUMMY_HOST = "dummy.host"
PORT_443 = 443
PORT_8883 = 8883
DEFAULT_KEEPALIVE_SEC = 600
DUMMY_TOPIC = "dummy/topic"
DUMMY_PAYLOAD = "dummy/payload"
DUMMY_QOS = 1
DUMMY_AWS_ACCESS_KEY_ID = "DummyKeyId"
DUMMY_AWS_SECRET_KEY = "SecretKey"
DUMMY_AWS_TOKEN = "Token"
DUMMY_CA_PATH = "path/to/ca"
DUMMY_CERT_PATH = "path/to/cert"
DUMMY_KEY_PATH = "path/to/key"
DUMMY_BASE_RECONNECT_BACKOFF_SEC = 1
DUMMY_MAX_RECONNECT_BACKOFF_SEC = 32
DUMMY_STABLE_CONNECTION_SEC = 16
DUMMY_QUEUE_SIZE = 100
DUMMY_DRAINING_FREQUENCY = 2
DUMMY_TIMEOUT_SEC = 10
DUMMY_USER_NAME = "UserName"
DUMMY_PASSWORD = "Password"


class TestMqttLibShadowClient:

    def setup_method(self, test_method):
        self._use_mock_mqtt_core()

    def _use_mock_mqtt_core(self):
        self.mqtt_core_patcher =  patch(PATCH_MODULE_LOCATION + "MqttCore", spec=MqttCore)
        self.mock_mqtt_core_constructor = self.mqtt_core_patcher.start()
        self.mqtt_core_mock = MagicMock()
        self.mock_mqtt_core_constructor.return_value = self.mqtt_core_mock
        self.iot_mqtt_shadow_client = AWSIoTMQTTShadowClient(SHADOW_CLIENT_ID)

    def teardown_method(self, test_method):
        self.mqtt_core_patcher.stop()

    def test_iot_mqtt_shadow_client_with_provided_mqtt_client(self):
        mock_iot_mqtt_client = MagicMock()
        iot_mqtt_shadow_client_with_provided_mqtt_client = AWSIoTMQTTShadowClient(SHADOW_CLIENT_ID, awsIoTMQTTClient=mock_iot_mqtt_client)
        assert mock_iot_mqtt_client.configureOfflinePublishQueueing.called is False

    def test_iot_mqtt_shadow_client_connect_default_keepalive(self):
        self.iot_mqtt_shadow_client.connect()
        self.mqtt_core_mock.connect.assert_called_once_with(DEFAULT_KEEPALIVE_SEC)

    def test_iot_mqtt_shadow_client_auto_enable_when_use_cert_over_443(self):
        self.mqtt_core_mock.use_wss.return_value = False
        self.iot_mqtt_shadow_client.configureEndpoint(hostName=DUMMY_HOST, portNumber=PORT_443)
        self.mqtt_core_mock.configure_alpn_protocols.assert_called_once()

    def test_iot_mqtt_shadow_client_alpn_auto_disable_when_use_wss(self):
        self.mqtt_core_mock.use_wss.return_value = True
        self.iot_mqtt_shadow_client.configureEndpoint(hostName=DUMMY_HOST, portNumber=PORT_443)
        assert self.mqtt_core_mock.configure_alpn_protocols.called is False

    def test_iot_mqtt_shadow_client_alpn_auto_disable_when_use_cert_over_8883(self):
        self.mqtt_core_mock.use_wss.return_value = False
        self.iot_mqtt_shadow_client.configureEndpoint(hostName=DUMMY_HOST, portNumber=PORT_8883)
        assert self.mqtt_core_mock.configure_alpn_protocols.called is False

    def test_iot_mqtt_shadow_client_clear_last_will(self):
        self.iot_mqtt_shadow_client.clearLastWill()
        self.mqtt_core_mock.clear_last_will.assert_called_once()

    def test_iot_mqtt_shadow_client_configure_endpoint(self):
        self.iot_mqtt_shadow_client.configureEndpoint(DUMMY_HOST, PORT_8883)
        self.mqtt_core_mock.configure_endpoint.assert_called_once()

    def test_iot_mqtt_shadow_client_configure_iam_credentials(self):
        self.iot_mqtt_shadow_client.configureIAMCredentials(DUMMY_AWS_ACCESS_KEY_ID, DUMMY_AWS_SECRET_KEY, DUMMY_AWS_TOKEN)
        self.mqtt_core_mock.configure_iam_credentials.assert_called_once()

    def test_iot_mqtt_shadowclient_configure_credentials(self):
        self.iot_mqtt_shadow_client.configureCredentials(DUMMY_CA_PATH, DUMMY_KEY_PATH, DUMMY_CERT_PATH)
        self.mqtt_core_mock.configure_cert_credentials.assert_called_once()

    def test_iot_mqtt_shadow_client_configure_auto_reconnect_backoff(self):
        self.iot_mqtt_shadow_client.configureAutoReconnectBackoffTime(DUMMY_BASE_RECONNECT_BACKOFF_SEC,
                                                                      DUMMY_MAX_RECONNECT_BACKOFF_SEC,
                                                                      DUMMY_STABLE_CONNECTION_SEC)
        self.mqtt_core_mock.configure_reconnect_back_off.assert_called_once_with(DUMMY_BASE_RECONNECT_BACKOFF_SEC,
                                                                                 DUMMY_MAX_RECONNECT_BACKOFF_SEC,
                                                                                 DUMMY_STABLE_CONNECTION_SEC)

    def test_iot_mqtt_shadow_client_configure_offline_publish_queueing(self):
        # This configurable is done at object initialization. We do not allow customers to configure this.
        self.mqtt_core_mock.configure_offline_requests_queue.assert_called_once_with(0, DROP_NEWEST)  # Disabled

    def test_iot_mqtt_client_configure_draining_frequency(self):
        # This configurable is done at object initialization. We do not allow customers to configure this.
        # Sine queuing is disabled, draining interval configuration is meaningless.
        # "10" is just a placeholder value in the internal implementation.
        self.mqtt_core_mock.configure_draining_interval_sec.assert_called_once_with(1/float(10))

    def test_iot_mqtt_client_configure_connect_disconnect_timeout(self):
        self.iot_mqtt_shadow_client.configureConnectDisconnectTimeout(DUMMY_TIMEOUT_SEC)
        self.mqtt_core_mock.configure_connect_disconnect_timeout_sec.assert_called_once_with(DUMMY_TIMEOUT_SEC)

    def test_iot_mqtt_client_configure_mqtt_operation_timeout(self):
        self.iot_mqtt_shadow_client.configureMQTTOperationTimeout(DUMMY_TIMEOUT_SEC)
        self.mqtt_core_mock.configure_operation_timeout_sec.assert_called_once_with(DUMMY_TIMEOUT_SEC)

    def test_iot_mqtt_client_configure_user_name_password(self):
        self.iot_mqtt_shadow_client.configureUsernamePassword(DUMMY_USER_NAME, DUMMY_PASSWORD)
        self.mqtt_core_mock.configure_username_password.assert_called_once_with(DUMMY_USER_NAME, DUMMY_PASSWORD)

    def test_iot_mqtt_client_enable_metrics_collection(self):
        self.iot_mqtt_shadow_client.enableMetricsCollection()
        self.mqtt_core_mock.enable_metrics_collection.assert_called_once()

    def test_iot_mqtt_client_disable_metrics_collection(self):
        self.iot_mqtt_shadow_client.disableMetricsCollection()
        self.mqtt_core_mock.disable_metrics_collection.assert_called_once()

    def test_iot_mqtt_client_callback_registration_upon_connect(self):
        fake_on_online_callback = MagicMock()
        fake_on_offline_callback = MagicMock()

        self.iot_mqtt_shadow_client.onOnline = fake_on_online_callback
        self.iot_mqtt_shadow_client.onOffline = fake_on_offline_callback
        # `onMessage` is used internally by the SDK. We do not expose this callback configurable to the customer

        self.iot_mqtt_shadow_client.connect()

        assert self.mqtt_core_mock.on_online == fake_on_online_callback
        assert self.mqtt_core_mock.on_offline == fake_on_offline_callback
        self.mqtt_core_mock.connect.assert_called_once()

    def test_iot_mqtt_client_disconnect(self):
        self.iot_mqtt_shadow_client.disconnect()
        self.mqtt_core_mock.disconnect.assert_called_once()


class TestMqttLibMqttClient:

    def setup_method(self, test_method):
        self._use_mock_mqtt_core()

    def _use_mock_mqtt_core(self):
        self.mqtt_core_patcher =  patch(PATCH_MODULE_LOCATION + "MqttCore", spec=MqttCore)
        self.mock_mqtt_core_constructor = self.mqtt_core_patcher.start()
        self.mqtt_core_mock = MagicMock()
        self.mock_mqtt_core_constructor.return_value = self.mqtt_core_mock
        self.iot_mqtt_client = AWSIoTMQTTClient(CLIENT_ID)

    def teardown_method(self, test_method):
        self.mqtt_core_patcher.stop()

    def test_iot_mqtt_client_connect_default_keepalive(self):
        self.iot_mqtt_client.connect()
        self.mqtt_core_mock.connect.assert_called_once_with(DEFAULT_KEEPALIVE_SEC)

    def test_iot_mqtt_client_connect_async_default_keepalive(self):
        self.iot_mqtt_client.connectAsync()
        self.mqtt_core_mock.connect_async.assert_called_once_with(DEFAULT_KEEPALIVE_SEC, None)

    def test_iot_mqtt_client_alpn_auto_enable_when_use_cert_over_443(self):
        self.mqtt_core_mock.use_wss.return_value = False
        self.iot_mqtt_client.configureEndpoint(hostName=DUMMY_HOST, portNumber=PORT_443)
        self.mqtt_core_mock.configure_alpn_protocols.assert_called_once()

    def test_iot_mqtt_client_alpn_auto_disable_when_use_wss(self):
        self.mqtt_core_mock.use_wss.return_value = True
        self.iot_mqtt_client.configureEndpoint(hostName=DUMMY_HOST, portNumber=PORT_443)
        assert self.mqtt_core_mock.configure_alpn_protocols.called is False

    def test_iot_mqtt_client_alpn_auto_disable_when_use_cert_over_8883(self):
        self.mqtt_core_mock.use_wss.return_value = False
        self.iot_mqtt_client.configureEndpoint(hostName=DUMMY_HOST, portNumber=PORT_8883)
        assert self.mqtt_core_mock.configure_alpn_protocols.called is False

    def test_iot_mqtt_client_configure_last_will(self):
        self.iot_mqtt_client.configureLastWill(topic=DUMMY_TOPIC, payload=DUMMY_PAYLOAD, QoS=DUMMY_QOS)
        self.mqtt_core_mock.configure_last_will.assert_called_once_with(DUMMY_TOPIC, DUMMY_PAYLOAD, DUMMY_QOS, False)

    def test_iot_mqtt_client_clear_last_will(self):
        self.iot_mqtt_client.clearLastWill()
        self.mqtt_core_mock.clear_last_will.assert_called_once()

    def test_iot_mqtt_client_configure_endpoint(self):
        self.iot_mqtt_client.configureEndpoint(DUMMY_HOST, PORT_8883)
        self.mqtt_core_mock.configure_endpoint.assert_called_once()

    def test_iot_mqtt_client_configure_iam_credentials(self):
        self.iot_mqtt_client.configureIAMCredentials(DUMMY_AWS_ACCESS_KEY_ID, DUMMY_AWS_SECRET_KEY, DUMMY_AWS_TOKEN)
        self.mqtt_core_mock.configure_iam_credentials.assert_called_once()

    def test_iot_mqtt_client_configure_credentials(self):
        self.iot_mqtt_client.configureCredentials(DUMMY_CA_PATH, DUMMY_KEY_PATH, DUMMY_CERT_PATH)
        self.mqtt_core_mock.configure_cert_credentials.assert_called_once()

    def test_iot_mqtt_client_configure_auto_reconnect_backoff(self):
        self.iot_mqtt_client.configureAutoReconnectBackoffTime(DUMMY_BASE_RECONNECT_BACKOFF_SEC,
                                                               DUMMY_MAX_RECONNECT_BACKOFF_SEC,
                                                               DUMMY_STABLE_CONNECTION_SEC)
        self.mqtt_core_mock.configure_reconnect_back_off.assert_called_once_with(DUMMY_BASE_RECONNECT_BACKOFF_SEC,
                                                                                 DUMMY_MAX_RECONNECT_BACKOFF_SEC,
                                                                                 DUMMY_STABLE_CONNECTION_SEC)

    def test_iot_mqtt_client_configure_offline_publish_queueing(self):
        self.iot_mqtt_client.configureOfflinePublishQueueing(DUMMY_QUEUE_SIZE)
        self.mqtt_core_mock.configure_offline_requests_queue.assert_called_once_with(DUMMY_QUEUE_SIZE, DROP_NEWEST)

    def test_iot_mqtt_client_configure_draining_frequency(self):
        self.iot_mqtt_client.configureDrainingFrequency(DUMMY_DRAINING_FREQUENCY)
        self.mqtt_core_mock.configure_draining_interval_sec.assert_called_once_with(1/float(DUMMY_DRAINING_FREQUENCY))

    def test_iot_mqtt_client_configure_connect_disconnect_timeout(self):
        self.iot_mqtt_client.configureConnectDisconnectTimeout(DUMMY_TIMEOUT_SEC)
        self.mqtt_core_mock.configure_connect_disconnect_timeout_sec.assert_called_once_with(DUMMY_TIMEOUT_SEC)

    def test_iot_mqtt_client_configure_mqtt_operation_timeout(self):
        self.iot_mqtt_client.configureMQTTOperationTimeout(DUMMY_TIMEOUT_SEC)
        self.mqtt_core_mock.configure_operation_timeout_sec.assert_called_once_with(DUMMY_TIMEOUT_SEC)

    def test_iot_mqtt_client_configure_user_name_password(self):
        self.iot_mqtt_client.configureUsernamePassword(DUMMY_USER_NAME, DUMMY_PASSWORD)
        self.mqtt_core_mock.configure_username_password.assert_called_once_with(DUMMY_USER_NAME, DUMMY_PASSWORD)

    def test_iot_mqtt_client_enable_metrics_collection(self):
        self.iot_mqtt_client.enableMetricsCollection()
        self.mqtt_core_mock.enable_metrics_collection.assert_called_once()

    def test_iot_mqtt_client_disable_metrics_collection(self):
        self.iot_mqtt_client.disableMetricsCollection()
        self.mqtt_core_mock.disable_metrics_collection.assert_called_once()

    def test_iot_mqtt_client_callback_registration_upon_connect(self):
        fake_on_online_callback = MagicMock()
        fake_on_offline_callback = MagicMock()
        fake_on_message_callback = MagicMock()

        self.iot_mqtt_client.onOnline = fake_on_online_callback
        self.iot_mqtt_client.onOffline = fake_on_offline_callback
        self.iot_mqtt_client.onMessage = fake_on_message_callback

        self.iot_mqtt_client.connect()

        assert self.mqtt_core_mock.on_online == fake_on_online_callback
        assert self.mqtt_core_mock.on_offline == fake_on_offline_callback
        assert self.mqtt_core_mock.on_message == fake_on_message_callback
        self.mqtt_core_mock.connect.assert_called_once()

    def test_iot_mqtt_client_disconnect(self):
        self.iot_mqtt_client.disconnect()
        self.mqtt_core_mock.disconnect.assert_called_once()

    def test_iot_mqtt_client_publish(self):
        self.iot_mqtt_client.publish(DUMMY_TOPIC, DUMMY_PAYLOAD, DUMMY_QOS)
        self.mqtt_core_mock.publish.assert_called_once_with(DUMMY_TOPIC, DUMMY_PAYLOAD, DUMMY_QOS, False)

    def test_iot_mqtt_client_subscribe(self):
        message_callback = MagicMock()
        self.iot_mqtt_client.subscribe(DUMMY_TOPIC, DUMMY_QOS, message_callback)
        self.mqtt_core_mock.subscribe.assert_called_once_with(DUMMY_TOPIC, DUMMY_QOS, message_callback)

    def test_iot_mqtt_client_unsubscribe(self):
        self.iot_mqtt_client.unsubscribe(DUMMY_TOPIC)
        self.mqtt_core_mock.unsubscribe.assert_called_once_with(DUMMY_TOPIC)

    def test_iot_mqtt_client_connect_async(self):
        connack_callback = MagicMock()
        self.iot_mqtt_client.connectAsync(ackCallback=connack_callback)
        self.mqtt_core_mock.connect_async.assert_called_once_with(DEFAULT_KEEPALIVE_SEC, connack_callback)

    def test_iot_mqtt_client_disconnect_async(self):
        disconnect_callback = MagicMock()
        self.iot_mqtt_client.disconnectAsync(ackCallback=disconnect_callback)
        self.mqtt_core_mock.disconnect_async.assert_called_once_with(disconnect_callback)

    def test_iot_mqtt_client_publish_async(self):
        puback_callback = MagicMock()
        self.iot_mqtt_client.publishAsync(DUMMY_TOPIC, DUMMY_PAYLOAD, DUMMY_QOS, puback_callback)
        self.mqtt_core_mock.publish_async.assert_called_once_with(DUMMY_TOPIC, DUMMY_PAYLOAD, DUMMY_QOS,
                                                                  False, puback_callback)

    def test_iot_mqtt_client_subscribe_async(self):
        suback_callback = MagicMock()
        message_callback = MagicMock()
        self.iot_mqtt_client.subscribeAsync(DUMMY_TOPIC, DUMMY_QOS, suback_callback, message_callback)
        self.mqtt_core_mock.subscribe_async.assert_called_once_with(DUMMY_TOPIC, DUMMY_QOS,
                                                                    suback_callback, message_callback)

    def test_iot_mqtt_client_unsubscribe_async(self):
        unsuback_callback = MagicMock()
        self.iot_mqtt_client.unsubscribeAsync(DUMMY_TOPIC, unsuback_callback)
        self.mqtt_core_mock.unsubscribe_async.assert_called_once_with(DUMMY_TOPIC, unsuback_callback)
