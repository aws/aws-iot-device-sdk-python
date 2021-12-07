import AWSIoTPythonSDK.core.protocol.connection.alpn as alpn
from AWSIoTPythonSDK.core.protocol.connection.alpn import SSLContextBuilder
import sys
import pytest
try:
    from mock import patch
    from mock import MagicMock
except:
    from unittest.mock import patch
    from unittest.mock import MagicMock
if sys.version_info >= (3, 4):
    from importlib import reload


python3_5_above_only = pytest.mark.skipif(sys.version_info >= (3, 0) and sys.version_info < (3, 5), reason="Requires Python 3.5+")
python2_7_10_above_only = pytest.mark.skipif(sys.version_info < (2, 7, 10), reason="Requires Python 2.7.10+")

PATCH_MODULE_LOCATION = "AWSIoTPythonSDK.core.protocol.connection.alpn"
SSL_MODULE_NAME = "ssl"
SSL_CONTEXT_METHOD_NAME = "create_default_context"

DUMMY_SSL_PROTOCOL = "DummySSLProtocol"
DUMMY_CERT_REQ = "DummyCertReq"
DUMMY_CIPHERS = "DummyCiphers"
DUMMY_CA_FILE_PATH = "fake/path/to/ca"
DUMMY_CERT_FILE_PATH = "fake/path/to/cert"
DUMMY_KEY_FILE_PATH = "fake/path/to/key"
DUMMY_ALPN_PROTOCOLS = "x-amzn-mqtt-ca"


@python2_7_10_above_only
@python3_5_above_only
class TestALPNSSLContextBuilder:

    def test_check_supportability_no_ssl(self):
        self._preserve_ssl()
        try:
            self._none_ssl()
            with pytest.raises(RuntimeError):
                alpn.SSLContextBuilder().build()
        finally:
            self._unnone_ssl()

    def _none_ssl(self):
        # We always run the unit test with Python versions that have proper ssl support
        # We need to mock it out in this test
        sys.modules[SSL_MODULE_NAME] = None
        reload(alpn)

    def _unnone_ssl(self):
        sys.modules[SSL_MODULE_NAME] = self._normal_ssl_module
        reload(alpn)

    def test_check_supportability_no_ssl_context(self):
        self._preserve_ssl()
        try:
            self._mock_ssl()
            del self.ssl_mock.SSLContext
            with pytest.raises(NotImplementedError):
                SSLContextBuilder()
        finally:
            self._unmock_ssl()

    def test_check_supportability_no_alpn(self):
        self._preserve_ssl()
        try:
            self._mock_ssl()
            del self.ssl_mock.SSLContext.set_alpn_protocols
            with pytest.raises(NotImplementedError):
                SSLContextBuilder()
        finally:
            self._unmock_ssl()

    def _preserve_ssl(self):
        self._normal_ssl_module = sys.modules[SSL_MODULE_NAME]

    def _mock_ssl(self):
        self.ssl_mock = MagicMock()
        alpn.ssl = self.ssl_mock

    def _unmock_ssl(self):
        alpn.ssl = self._normal_ssl_module

    def test_with_ca_certs(self):
        self._use_mock_ssl_context()
        SSLContextBuilder().with_ca_certs(DUMMY_CA_FILE_PATH).build()
        self.mock_ssl_context.load_verify_locations.assert_called_once_with(DUMMY_CA_FILE_PATH)

    def test_with_cert_key_pair(self):
        self._use_mock_ssl_context()
        SSLContextBuilder().with_cert_key_pair(DUMMY_CERT_FILE_PATH, DUMMY_KEY_FILE_PATH).build()
        self.mock_ssl_context.load_cert_chain.assert_called_once_with(DUMMY_CERT_FILE_PATH, DUMMY_KEY_FILE_PATH)

    def test_with_cert_reqs(self):
        self._use_mock_ssl_context()
        SSLContextBuilder().with_cert_reqs(DUMMY_CERT_REQ).build()
        assert self.mock_ssl_context.verify_mode == DUMMY_CERT_REQ

    def test_with_check_hostname(self):
        self._use_mock_ssl_context()
        SSLContextBuilder().with_check_hostname(True).build()
        assert self.mock_ssl_context.check_hostname == True

    def test_with_ciphers(self):
        self._use_mock_ssl_context()
        SSLContextBuilder().with_ciphers(DUMMY_CIPHERS).build()
        self.mock_ssl_context.set_ciphers.assert_called_once_with(DUMMY_CIPHERS)

    def test_with_none_ciphers(self):
        self._use_mock_ssl_context()
        SSLContextBuilder().with_ciphers(None).build()
        assert not self.mock_ssl_context.set_ciphers.called

    def test_with_alpn_protocols(self):
        self._use_mock_ssl_context()
        SSLContextBuilder().with_alpn_protocols(DUMMY_ALPN_PROTOCOLS)
        self.mock_ssl_context.set_alpn_protocols.assert_called_once_with(DUMMY_ALPN_PROTOCOLS)

    def _use_mock_ssl_context(self):
        self.mock_ssl_context = MagicMock()
        self.ssl_create_default_context_patcher = patch("%s.%s.%s" % (PATCH_MODULE_LOCATION, SSL_MODULE_NAME, SSL_CONTEXT_METHOD_NAME))
        self.mock_ssl_create_default_context = self.ssl_create_default_context_patcher.start()
        self.mock_ssl_create_default_context.return_value = self.mock_ssl_context
