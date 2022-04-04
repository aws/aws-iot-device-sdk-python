import random
import string
import traceback
from ssl import SSLError

import TestToolLibrary.SDKPackage.AWSIoTPythonSDK.core.protocol.paho.client as paho
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.core.util.providers import CertificateCredentialsProvider
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.core.util.providers import CiphersProvider
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.core.util.enums import DropBehaviorTypes
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.core.util.providers import EndpointProvider
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.core.protocol.mqtt_core import MqttCore
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.exception.AWSIoTExceptions import connectError
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.exception.AWSIoTExceptions import connectTimeoutException


CERT_MUTUAL_AUTH = "MutualAuth"
WEBSOCKET = 'Websocket'
CERT_ALPN = "ALPN"


# Class that manages the creation, configuration and connection of MQTT Client
class MQTTClientManager:

    def create_connected_mqtt_client(self, mode, client_id, host, credentials_data, callbacks=None):
        client = self.create_nonconnected_mqtt_client(mode, client_id, host, credentials_data, callbacks)
        return self._connect_client(client)

    def create_nonconnected_mqtt_client(self, mode, client_id, host, credentials_data, callbacks=None):
        if mode == CERT_MUTUAL_AUTH:
            sdk_mqtt_client = self._create_nonconnected_mqtt_client_with_cert(client_id, host, 8883, credentials_data)
        elif mode == WEBSOCKET:
            root_ca, certificate, private_key = credentials_data
            sdk_mqtt_client = AWSIoTMQTTClient(clientID=client_id + "_" + self._random_string(3), useWebsocket=True)
            sdk_mqtt_client.configureEndpoint(host, 443)
            sdk_mqtt_client.configureCredentials(CAFilePath=root_ca)
        elif mode == CERT_ALPN:
            sdk_mqtt_client = self._create_nonconnected_mqtt_client_with_cert(client_id, host, 443, credentials_data)
        else:
            raise RuntimeError("Test mode: " + str(mode) + " not supported!")

        sdk_mqtt_client.configureConnectDisconnectTimeout(10)
        sdk_mqtt_client.configureMQTTOperationTimeout(5)

        if callbacks is not None:
            sdk_mqtt_client.onOnline = callbacks.on_online
            sdk_mqtt_client.onOffline = callbacks.on_offline
            sdk_mqtt_client.onMessage = callbacks.on_message

        return sdk_mqtt_client

    def _create_nonconnected_mqtt_client_with_cert(self, client_id, host, port, credentials_data):
        root_ca, certificate, private_key = credentials_data
        sdk_mqtt_client = AWSIoTMQTTClient(clientID=client_id + "_" + self._random_string(3))
        sdk_mqtt_client.configureEndpoint(host, port)
        sdk_mqtt_client.configureCredentials(CAFilePath=root_ca, KeyPath=private_key, CertificatePath=certificate)

        return sdk_mqtt_client

    def create_connected_mqtt_core(self, client_id, host, root_ca, certificate, private_key, mode):
        client = self.create_nonconnected_mqtt_core(client_id, host, root_ca, certificate, private_key, mode)
        return self._connect_client(client)

    def create_nonconnected_mqtt_core(self, client_id, host, root_ca, certificate, private_key, mode):
        client = None
        protocol = None
        port = None
        is_websocket = False
        is_alpn = False

        if mode == CERT_MUTUAL_AUTH:
            protocol = paho.MQTTv311
            port = 8883
        elif mode == WEBSOCKET:
            protocol = paho.MQTTv31
            port = 443
            is_websocket = True
        elif mode == CERT_ALPN:
            protocol = paho.MQTTv311
            port = 443
            is_alpn = True
        else:
            print("Error in creating the client")

        if protocol is None or port is None:
            print("Not enough input parameters")
            return client  # client is None is the necessary params are not there

        try:
            client = MqttCore(client_id + "_" + self._random_string(3), True, protocol, is_websocket)

            endpoint_provider = EndpointProvider()
            endpoint_provider.set_host(host)
            endpoint_provider.set_port(port)

            # Once is_websocket is True, certificate_credentials_provider will NOT be used
            # by the client even if it is configured
            certificate_credentials_provider = CertificateCredentialsProvider()
            certificate_credentials_provider.set_ca_path(root_ca)
            certificate_credentials_provider.set_cert_path(certificate)
            certificate_credentials_provider.set_key_path(private_key)

            cipher_provider = CiphersProvider()
            cipher_provider.set_ciphers(None)
            
            client.configure_endpoint(endpoint_provider)
            client.configure_cert_credentials(certificate_credentials_provider, cipher_provider)
            client.configure_connect_disconnect_timeout_sec(10)
            client.configure_operation_timeout_sec(5)
            client.configure_offline_requests_queue(10, DropBehaviorTypes.DROP_NEWEST)

            if is_alpn:
                client.configure_alpn_protocols()
        except Exception as e:
            print("Unknown exception in creating the client: " + str(e))
        finally:
            return client

    def _random_string(self, length):
        return "".join(random.choice(string.ascii_lowercase) for i in range(length))

    def _connect_client(self, client):
        if client is None:
            return client

        try:
            client.connect(1)
        except connectTimeoutException as e:
            print("Connect timeout: " + str(e))
            return None
        except connectError as e:
            print("Connect error:" + str(e))
            return None
        except SSLError as e:
            print("Connect SSL error: " + str(e))
            return None
        except IOError as e:
            print("Credentials not found: " + str(e))
            return None
        except Exception as e:
            print("Unknown exception in connect: ")
            traceback.print_exc()
            return None

        return client
