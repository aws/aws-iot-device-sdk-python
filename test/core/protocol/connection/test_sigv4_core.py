from AWSIoTPythonSDK.core.protocol.connection.cores import SigV4Core
from AWSIoTPythonSDK.exception.AWSIoTExceptions import wssNoKeyInEnvironmentError
import os
from datetime import datetime
try:
    from mock import patch
    from mock import MagicMock
except:
    from unittest.mock import patch
    from unittest.mock import MagicMock
import pytest
try:
    from configparser import ConfigParser  # Python 3+
    from configparser import NoOptionError
except ImportError:
    from ConfigParser import ConfigParser
    from ConfigParser import NoOptionError


CREDS_NOT_FOUND_MODE_NO_KEYS = "NoKeys"
CREDS_NOT_FOUND_MODE_EMPTY_VALUES = "EmptyValues"

PATCH_MODULE_LOCATION = "AWSIoTPythonSDK.core.protocol.connection.cores."
DUMMY_ACCESS_KEY_ID = "TRUSTMETHISIDISFAKE0"
DUMMY_SECRET_ACCESS_KEY = "trustMeThisSecretKeyIsSoFakeAaBbCc00Dd11"
DUMMY_SESSION_TOKEN = "FQoDYXdzEGcaDNSwicOypVyhiHj4JSLUAXTsOXu1YGT/Oaltz" \
                      "XujI+cwvEA3zPoUdebHOkaUmRBO3o34J/3r2/+hBqZZNSpyzK" \
                      "sBge1MXPwbM2G5ojz3aY4Qj+zD3hEMu9nxk3rhKkmTQWLoB4Z" \
                      "rPRG6GJGkoLMAL1sSEh9kqbHN6XIt3F2E+Wn2BhDoGA7ZsXSg" \
                      "+pgIntkSZcLT7pCX8pTEaEtRBhJQVc5GTYhG9y9mgjpeVRsbE" \
                      "j8yDJzSWDpLGgR7APSvCFX2H+DwsKM564Z4IzjpbntIlLXdQw" \
                      "Oytd65dgTlWZkmmYpTwVh+KMq+0MoF"
DUMMY_UTC_NOW_STRFTIME_RESULT = "20170628T204845Z"

EXPECTED_WSS_URL_WITH_TOKEN = "wss://data.iot.us-east-1.amazonaws.com:44" \
                              "3/mqtt?X-Amz-Algorithm=AWS4-HMAC-SHA256&X" \
                              "-Amz-Credential=TRUSTMETHISIDISFAKE0%2F20" \
                              "170628%2Fus-east-1%2Fiotdata%2Faws4_reque" \
                              "st&X-Amz-Date=20170628T204845Z&X-Amz-Expi" \
                              "res=86400&X-Amz-SignedHeaders=host&X-Amz-" \
                              "Signature=b79a4d7e31ccbf96b22d93cce1b500b" \
                              "9ee611ec966159547e140ae32e4dcebed&X-Amz-S" \
                              "ecurity-Token=FQoDYXdzEGcaDNSwicOypVyhiHj" \
                              "4JSLUAXTsOXu1YGT/OaltzXujI%2BcwvEA3zPoUde" \
                              "bHOkaUmRBO3o34J/3r2/%2BhBqZZNSpyzKsBge1MX" \
                              "PwbM2G5ojz3aY4Qj%2BzD3hEMu9nxk3rhKkmTQWLo" \
                              "B4ZrPRG6GJGkoLMAL1sSEh9kqbHN6XIt3F2E%2BWn" \
                              "2BhDoGA7ZsXSg%2BpgIntkSZcLT7pCX8pTEaEtRBh" \
                              "JQVc5GTYhG9y9mgjpeVRsbEj8yDJzSWDpLGgR7APS" \
                              "vCFX2H%2BDwsKM564Z4IzjpbntIlLXdQwOytd65dg" \
                              "TlWZkmmYpTwVh%2BKMq%2B0MoF"
EXPECTED_WSS_URL_WITHOUT_TOKEN = "wss://data.iot.us-east-1.amazonaws.com" \
                                 ":443/mqtt?X-Amz-Algorithm=AWS4-HMAC-SH" \
                                 "A256&X-Amz-Credential=TRUSTMETHISIDISF" \
                                 "AKE0%2F20170628%2Fus-east-1%2Fiotdata%" \
                                 "2Faws4_request&X-Amz-Date=20170628T204" \
                                 "845Z&X-Amz-Expires=86400&X-Amz-SignedH" \
                                 "eaders=host&X-Amz-Signature=b79a4d7e31" \
                                 "ccbf96b22d93cce1b500b9ee611ec966159547" \
                                 "e140ae32e4dcebed"


class TestSigV4Core:

    def setup_method(self, test_method):
        self._use_mock_datetime()
        self.mock_utc_now_result.strftime.return_value = DUMMY_UTC_NOW_STRFTIME_RESULT
        self.sigv4_core = SigV4Core()

    def _use_mock_datetime(self):
        self.datetime_patcher = patch(PATCH_MODULE_LOCATION + "datetime", spec=datetime)
        self.mock_datetime_constructor = self.datetime_patcher.start()
        self.mock_utc_now_result = MagicMock(spec=datetime)
        self.mock_datetime_constructor.utcnow.return_value = self.mock_utc_now_result

    def teardown_method(self, test_method):
        self.datetime_patcher.stop()

    def test_generate_url_with_env_credentials(self):
        self._use_mock_os_environ({
            "AWS_ACCESS_KEY_ID" : DUMMY_ACCESS_KEY_ID,
            "AWS_SECRET_ACCESS_KEY" : DUMMY_SECRET_ACCESS_KEY
        })
        assert self._invoke_create_wss_endpoint_api() == EXPECTED_WSS_URL_WITHOUT_TOKEN
        self.python_os_environ_patcher.stop()

    def test_generate_url_with_env_credentials_token(self):
        self._use_mock_os_environ({
            "AWS_ACCESS_KEY_ID" : DUMMY_ACCESS_KEY_ID,
            "AWS_SECRET_ACCESS_KEY" : DUMMY_SECRET_ACCESS_KEY,
            "AWS_SESSION_TOKEN" : DUMMY_SESSION_TOKEN
        })
        assert self._invoke_create_wss_endpoint_api() == EXPECTED_WSS_URL_WITH_TOKEN
        self.python_os_environ_patcher.stop()

    def _use_mock_os_environ(self, os_environ_map):
        self.python_os_environ_patcher = patch.dict(os.environ, os_environ_map)
        self.python_os_environ_patcher.start()

    def _use_mock_configparser(self):
        self.configparser_patcher = patch(PATCH_MODULE_LOCATION + "ConfigParser", spec=ConfigParser)
        self.mock_configparser_constructor = self.configparser_patcher.start()
        self.mock_configparser = MagicMock(spec=ConfigParser)
        self.mock_configparser_constructor.return_value = self.mock_configparser

    def test_generate_url_with_input_credentials(self):
        self._configure_mocks_credentials_not_found_in_env_config()
        self.sigv4_core.setIAMCredentials(DUMMY_ACCESS_KEY_ID, DUMMY_SECRET_ACCESS_KEY, "")

        assert self._invoke_create_wss_endpoint_api() == EXPECTED_WSS_URL_WITHOUT_TOKEN

        self._recover_mocks_for_env_config()

    def test_generate_url_with_input_credentials_token(self):
        self._configure_mocks_credentials_not_found_in_env_config()
        self.sigv4_core.setIAMCredentials(DUMMY_ACCESS_KEY_ID, DUMMY_SECRET_ACCESS_KEY, DUMMY_SESSION_TOKEN)

        assert self._invoke_create_wss_endpoint_api() == EXPECTED_WSS_URL_WITH_TOKEN

        self._recover_mocks_for_env_config()

    def _recover_mocks_for_env_config(self):
        self.python_os_environ_patcher.stop()
        self.configparser_patcher.stop()

    def test_generate_url_failure_when_credential_configured_with_none_values(self):
        self._use_mock_os_environ({})
        self._use_mock_configparser()
        self.mock_configparser.get.side_effect = NoOptionError("option", "section")
        self.sigv4_core.setIAMCredentials(None, None, None)

        with pytest.raises(wssNoKeyInEnvironmentError):
            self._invoke_create_wss_endpoint_api()

    def _configure_mocks_credentials_not_found_in_env_config(self, mode=CREDS_NOT_FOUND_MODE_NO_KEYS):
        if mode == CREDS_NOT_FOUND_MODE_NO_KEYS:
            self._use_mock_os_environ({})
        elif mode == CREDS_NOT_FOUND_MODE_EMPTY_VALUES:
            self._use_mock_os_environ({
                "AWS_ACCESS_KEY_ID" : "",
                "AWS_SECRET_ACCESS_KEY" : ""
            })
        self._use_mock_configparser()
        self.mock_configparser.get.side_effect = NoOptionError("option", "section")

    def _invoke_create_wss_endpoint_api(self):
        return self.sigv4_core.createWebsocketEndpoint("data.iot.us-east-1.amazonaws.com", 443, "us-east-1",
                                                       "GET", "iotdata", "/mqtt")
