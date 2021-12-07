from AWSIoTPythonSDK.core.util.providers import CertificateCredentialsProvider
from AWSIoTPythonSDK.core.util.providers import IAMCredentialsProvider
from AWSIoTPythonSDK.core.util.providers import EndpointProvider


DUMMY_PATH = "/dummy/path/"
DUMMY_CERT_PATH = DUMMY_PATH + "cert.pem"
DUMMY_CA_PATH = DUMMY_PATH + "ca.crt"
DUMMY_KEY_PATH = DUMMY_PATH + "key.pem"
DUMMY_ACCESS_KEY_ID = "AccessKey"
DUMMY_SECRET_KEY = "SecretKey"
DUMMY_SESSION_TOKEN = "SessionToken"
DUMMY_HOST = "dummy.host.com"
DUMMY_PORT = 8888


class TestProviders:

    def setup_method(self, test_method):
        self.certificate_credentials_provider = CertificateCredentialsProvider()
        self.iam_credentials_provider = IAMCredentialsProvider()
        self.endpoint_provider = EndpointProvider()

    def test_certificate_credentials_provider(self):
        self.certificate_credentials_provider.set_ca_path(DUMMY_CA_PATH)
        self.certificate_credentials_provider.set_cert_path(DUMMY_CERT_PATH)
        self.certificate_credentials_provider.set_key_path(DUMMY_KEY_PATH)
        assert self.certificate_credentials_provider.get_ca_path() == DUMMY_CA_PATH
        assert self.certificate_credentials_provider.get_cert_path() == DUMMY_CERT_PATH
        assert self.certificate_credentials_provider.get_key_path() == DUMMY_KEY_PATH

    def test_iam_credentials_provider(self):
        self.iam_credentials_provider.set_ca_path(DUMMY_CA_PATH)
        self.iam_credentials_provider.set_access_key_id(DUMMY_ACCESS_KEY_ID)
        self.iam_credentials_provider.set_secret_access_key(DUMMY_SECRET_KEY)
        self.iam_credentials_provider.set_session_token(DUMMY_SESSION_TOKEN)
        assert self.iam_credentials_provider.get_ca_path() == DUMMY_CA_PATH
        assert self.iam_credentials_provider.get_access_key_id() == DUMMY_ACCESS_KEY_ID
        assert self.iam_credentials_provider.get_secret_access_key() == DUMMY_SECRET_KEY
        assert self.iam_credentials_provider.get_session_token() == DUMMY_SESSION_TOKEN

    def test_endpoint_provider(self):
        self.endpoint_provider.set_host(DUMMY_HOST)
        self.endpoint_provider.set_port(DUMMY_PORT)
        assert self.endpoint_provider.get_host() == DUMMY_HOST
        assert self.endpoint_provider.get_port() == DUMMY_PORT
