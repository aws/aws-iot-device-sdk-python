from AWSIoTPythonSDK.core.greengrass.discovery.providers import DiscoveryInfoProvider
from AWSIoTPythonSDK.exception.AWSIoTExceptions import DiscoveryInvalidRequestException
from AWSIoTPythonSDK.exception.AWSIoTExceptions import DiscoveryUnauthorizedException
from AWSIoTPythonSDK.exception.AWSIoTExceptions import DiscoveryDataNotFoundException
from AWSIoTPythonSDK.exception.AWSIoTExceptions import DiscoveryThrottlingException
from AWSIoTPythonSDK.exception.AWSIoTExceptions import DiscoveryTimeoutException
from AWSIoTPythonSDK.exception.AWSIoTExceptions import DiscoveryFailure
import pytest
try:
    from mock import patch
    from mock import MagicMock
except:
    from unittest.mock import patch
    from unittest.mock import MagicMock


DUMMY_CA_PATH = "dummy/ca/path"
DUMMY_CERT_PATH = "dummy/cert/path"
DUMMY_KEY_PATH = "dummy/key/path"
DUMMY_HOST = "dummy.host.amazonaws.com"
DUMMY_PORT = "8443"
DUMMY_TIME_OUT_SEC = 3
DUMMY_GGAD_THING_NAME = "CoolGGAD"
FORMAT_REQUEST = "GET /greengrass/discover/thing/%s HTTP/1.1\r\nHost: " + DUMMY_HOST + ":" + DUMMY_PORT + "\r\n\r\n"
FORMAT_RESPONSE_HEADER = "HTTP/1.1 %s %s\r\n" \
                         "content-type: application/json\r\n" \
                         "content-length: %d\r\n" \
                         "date: Wed, 05 Jul 2017 22:17:19 GMT\r\n" \
                         "x-amzn-RequestId: 97408dd9-06a0-73bb-8e00-c4fc6845d555\r\n" \
                         "connection: Keep-Alive\r\n\r\n"

SERVICE_ERROR_MESSAGE_FORMAT = "{\"errorMessage\":\"%s\"}"
SERVICE_ERROR_MESSAGE_400 = SERVICE_ERROR_MESSAGE_FORMAT % "Invalid input detected for this request"
SERVICE_ERROR_MESSAGE_401 = SERVICE_ERROR_MESSAGE_FORMAT % "Unauthorized request"
SERVICE_ERROR_MESSAGE_404 = SERVICE_ERROR_MESSAGE_FORMAT % "Resource not found"
SERVICE_ERROR_MESSAGE_429 = SERVICE_ERROR_MESSAGE_FORMAT % "Too many requests"
SERVICE_ERROR_MESSAGE_500 = SERVICE_ERROR_MESSAGE_FORMAT % "Internal server error"
PAYLOAD_200 = "{\"GGGroups\":[{\"GGGroupId\":\"627bf63d-ae64-4f58-a18c-80a44fcf4088\"," \
              "\"Cores\":[{\"thingArn\":\"arn:aws:iot:us-east-1:003261610643:thing/DRS_GGC_0kegiNGA_0\"," \
              "\"Connectivity\":[{\"Id\":\"Id-0\",\"HostAddress\":\"192.168.101.0\",\"PortNumber\":8080," \
              "\"Metadata\":\"Description-0\"}," \
              "{\"Id\":\"Id-1\",\"HostAddress\":\"192.168.101.1\",\"PortNumber\":8081,\"Metadata\":\"Description-1\"}," \
              "{\"Id\":\"Id-2\",\"HostAddress\":\"192.168.101.2\",\"PortNumber\":8082,\"Metadata\":\"Description-2\"}]}]," \
              "\"CAs\":[\"-----BEGIN CERTIFICATE-----\\n" \
              "MIIEFTCCAv2gAwIBAgIVAPZfc4GMLZPmXbnoaZm6jRDqDs4+MA0GCSqGSIb3DQEB\\n" \
              "CwUAMIGoMQswCQYDVQQGEwJVUzEYMBYGA1UECgwPQW1hem9uLmNvbSBJbmMuMRww\\n" \
              "GgYDVQQLDBNBbWF6b24gV2ViIFNlcnZpY2VzMRMwEQYDVQQIDApXYXNoaW5ndG9u\\n" \
              "MRAwDgYDVQQHDAdTZWF0dGxlMTowOAYDVQQDDDEwMDMyNjE2MTA2NDM6NjI3YmY2\\n" \
              "M2QtYWU2NC00ZjU4LWExOGMtODBhNDRmY2Y0MDg4MCAXDTE3MDUyNTE4NDI1OVoY\\n" \
              "DzIwOTcwNTI1MTg0MjU4WjCBqDELMAkGA1UEBhMCVVMxGDAWBgNVBAoMD0FtYXpv\\n" \
              "bi5jb20gSW5jLjEcMBoGA1UECwwTQW1hem9uIFdlYiBTZXJ2aWNlczETMBEGA1UE\\n" \
              "CAwKV2FzaGluZ3RvbjEQMA4GA1UEBwwHU2VhdHRsZTE6MDgGA1UEAwwxMDAzMjYx\\n" \
              "NjEwNjQzOjYyN2JmNjNkLWFlNjQtNGY1OC1hMThjLTgwYTQ0ZmNmNDA4ODCCASIw\\n" \
              "DQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAKEWtZtKyJUg2VUwZkbkVtltrfam\\n" \
              "s9LMIdKNA3Wz4zSLhZjKHiTSkQmpZwKle5ziYs6Q5hfeT8WC0FNAVv1JhnwsuGfT\\n" \
              "sG0UO5dSn7wqXOJigKC1CaSGqeFpKB0/a3wR1L6pCGVbLZ86/sPCEPHHJDieQ+Ps\\n" \
              "RnOcUGb4CuIBnI2N+lafWNa4F4KRSVJCEeZ6u4iWVVdIEcDLKlakY45jtVvQqwnz\\n" \
              "3leFsN7PTLEkVq5u1PXSbT5DWv6p+5NoDnGAT7j7Wbr2yJw7DtpBOL6oWkAdbFAQ\\n" \
              "2097e8mIxNYE9xAzRlb5wEr6jZl/8K60v9P83OapMeuOg4JS8FGulHXbDg0CAwEA\\n" \
              "AaMyMDAwDwYDVR0TAQH/BAUwAwEB/zAdBgNVHQ4EFgQU21ELaPCH9Oh001OS0JMv\\n" \
              "n8hU8dYwDQYJKoZIhvcNAQELBQADggEBABW66eH/+/v9Nq5jtJzflfrqAfBOzWLj\\n" \
              "UTEv6szkYzV5Crr8vnu2P5OlyA0NdiKGiAm0AgoDkf+n9HU3Hc0zm3G/QaAO2UmN\\n" \
              "9MwtIp29BSRf+gd1bX/WZTtl5I5xl290BDfr5o08I6TOf0A4P8IAkGwku5j0IQjM\\n" \
              "ns2HH5UVki155dtmWDEGX6q35KABbsmv3tO1+geJVYnd1QkHzR5IXA12gxlMw9GJ\\n" \
              "+cOw+rwJJ2ZcXo3HFoXBcsPqPOa1SO3vTl3XWQ+jX3vyDsxh/VGoJ4epsjwmJ+dW\\n" \
              "sHJoqsa3ZPDW0LcEuYgdzYWRhumGwH9fJJUx0GS4Tdg4ud+6jpuyflU=\\n" \
              "-----END CERTIFICATE-----\\n\"]}]}"


class TestDiscoveryInfoProvider:

    def setup_class(cls):
        cls.service_error_message_dict = {
            "400" : SERVICE_ERROR_MESSAGE_400,
            "401" : SERVICE_ERROR_MESSAGE_401,
            "404" : SERVICE_ERROR_MESSAGE_404,
            "429" : SERVICE_ERROR_MESSAGE_429
        }
        cls.client_exception_dict = {
            "400" : DiscoveryInvalidRequestException,
            "401" : DiscoveryUnauthorizedException,
            "404" : DiscoveryDataNotFoundException,
            "429" : DiscoveryThrottlingException
        }

    def setup_method(self, test_method):
        self.mock_sock = MagicMock()
        self.mock_ssl_sock = MagicMock()

    def test_200_drs_response_should_succeed(self):
        with patch.object(DiscoveryInfoProvider, "_create_tcp_connection") as mock_method_create_tcp_connection, \
                patch.object(DiscoveryInfoProvider, "_create_ssl_connection") as mock_method_create_ssl_connection:
            mock_method_create_tcp_connection.return_value = self.mock_sock
            mock_method_create_ssl_connection.return_value = self.mock_ssl_sock
            raw_outbound_request = FORMAT_REQUEST % DUMMY_GGAD_THING_NAME
            self._create_test_target()
            self.mock_ssl_sock.write.return_value = len(raw_outbound_request)
            self.mock_ssl_sock.read.side_effect = \
                list((FORMAT_RESPONSE_HEADER % ("200", "OK", len(PAYLOAD_200)) + PAYLOAD_200).encode("utf-8"))

            discovery_info = self.discovery_info_provider.discover(DUMMY_GGAD_THING_NAME)
            self.mock_ssl_sock.write.assert_called_with(raw_outbound_request.encode("utf-8"))
            assert discovery_info.rawJson == PAYLOAD_200

    def test_400_drs_response_should_raise(self):
        self._internal_test_non_200_drs_response_should_raise("400", "Bad request")

    def test_401_drs_response_should_raise(self):
        self._internal_test_non_200_drs_response_should_raise("401", "Unauthorized")

    def test_404_drs_response_should_raise(self):
        self._internal_test_non_200_drs_response_should_raise("404", "Not found")

    def test_429_drs_response_should_raise(self):
        self._internal_test_non_200_drs_response_should_raise("429", "Throttled")

    def test_unexpected_drs_response_should_raise(self):
        self._internal_test_non_200_drs_response_should_raise("500", "Internal server error")
        self._internal_test_non_200_drs_response_should_raise("1234", "Gibberish")

    def _internal_test_non_200_drs_response_should_raise(self, http_status_code, http_status_message):
        with patch.object(DiscoveryInfoProvider, "_create_tcp_connection") as mock_method_create_tcp_connection, \
                patch.object(DiscoveryInfoProvider, "_create_ssl_connection") as mock_method_create_ssl_connection:
            mock_method_create_tcp_connection.return_value = self.mock_sock
            mock_method_create_ssl_connection.return_value = self.mock_ssl_sock
            self._create_test_target()
            service_error_message = self.service_error_message_dict.get(http_status_code)
            if service_error_message is None:
                service_error_message = SERVICE_ERROR_MESSAGE_500
            client_exception_type = self.client_exception_dict.get(http_status_code)
            if client_exception_type is None:
                client_exception_type = DiscoveryFailure
            self.mock_ssl_sock.write.return_value = len(FORMAT_REQUEST % DUMMY_GGAD_THING_NAME)
            self.mock_ssl_sock.read.side_effect = \
                list((FORMAT_RESPONSE_HEADER % (http_status_code, http_status_message, len(service_error_message)) +
                     service_error_message).encode("utf-8"))

            with pytest.raises(client_exception_type):
                self.discovery_info_provider.discover(DUMMY_GGAD_THING_NAME)

    def test_request_time_out_should_raise(self):
        with patch.object(DiscoveryInfoProvider, "_create_tcp_connection") as mock_method_create_tcp_connection, \
                patch.object(DiscoveryInfoProvider, "_create_ssl_connection") as mock_method_create_ssl_connection:
            mock_method_create_tcp_connection.return_value = self.mock_sock
            mock_method_create_ssl_connection.return_value = self.mock_ssl_sock
            self._create_test_target()

            # We do not configure any return value and simply let request part time out
            with pytest.raises(DiscoveryTimeoutException):
                self.discovery_info_provider.discover(DUMMY_GGAD_THING_NAME)

    def test_response_time_out_should_raise(self):
        with patch.object(DiscoveryInfoProvider, "_create_tcp_connection") as mock_method_create_tcp_connection, \
                patch.object(DiscoveryInfoProvider, "_create_ssl_connection") as mock_method_create_ssl_connection:
            mock_method_create_tcp_connection.return_value = self.mock_sock
            mock_method_create_ssl_connection.return_value = self.mock_ssl_sock
            self._create_test_target()

            # We configure the request to succeed and let the response part time out
            self.mock_ssl_sock.write.return_value = len(FORMAT_REQUEST % DUMMY_GGAD_THING_NAME)
            with pytest.raises(DiscoveryTimeoutException):
                self.discovery_info_provider.discover(DUMMY_GGAD_THING_NAME)

    def _create_test_target(self):
        self.discovery_info_provider = DiscoveryInfoProvider(caPath=DUMMY_CA_PATH,
                                                             certPath=DUMMY_CERT_PATH,
                                                             keyPath=DUMMY_KEY_PATH,
                                                             host=DUMMY_HOST,
                                                             timeoutSec=DUMMY_TIME_OUT_SEC)
