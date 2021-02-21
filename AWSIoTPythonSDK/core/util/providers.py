# /*
# * Copyright 2010-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# *
# * Licensed under the Apache License, Version 2.0 (the "License").
# * You may not use this file except in compliance with the License.
# * A copy of the License is located at
# *
# *  http://aws.amazon.com/apache2.0
# *
# * or in the "license" file accompanying this file. This file is distributed
# * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# * express or implied. See the License for the specific language governing
# * permissions and limitations under the License.
# */


class CredentialsProvider(object):

    def __init__(self):
        self._ca_path = ""

    def set_ca_path(self, ca_path):
        self._ca_path = ca_path

    def get_ca_path(self):
        return self._ca_path


class CertificateCredentialsProvider(CredentialsProvider):

    def __init__(self):
        CredentialsProvider.__init__(self)
        self._cert_path = ""
        self._key_path = ""

    def set_cert_path(self,cert_path):
        self._cert_path = cert_path

    def set_key_path(self, key_path):
        self._key_path = key_path

    def get_cert_path(self):
        return self._cert_path

    def get_key_path(self):
        return self._key_path


class IAMCredentialsProvider(CredentialsProvider):

    def __init__(self):
        CredentialsProvider.__init__(self)
        self._aws_access_key_id = ""
        self._aws_secret_access_key = ""
        self._aws_session_token = ""

    def set_access_key_id(self, access_key_id):
        self._aws_access_key_id = access_key_id

    def set_secret_access_key(self, secret_access_key):
        self._aws_secret_access_key = secret_access_key

    def set_session_token(self, session_token):
        self._aws_session_token = session_token

    def get_access_key_id(self):
        return self._aws_access_key_id

    def get_secret_access_key(self):
        return self._aws_secret_access_key

    def get_session_token(self):
        return self._aws_session_token


class EndpointProvider(object):

    def __init__(self):
        self._host = ""
        self._port = -1

    def set_host(self, host):
        self._host = host

    def set_port(self, port):
        self._port = port

    def get_host(self):
        return self._host

    def get_port(self):
        return self._port


class CiphersProvider(object):
    def __init__(self):
        self._ciphers = None
        self.aws_iot_valid_ciphers = [
            "ECDHE-ECDSA-AES128-GCM-SHA256", "ECDHE-RSA-AES128-GCM-SHA256", "ECDHE-ECDSA-AES128-SHA256",
            "ECDHE-RSA-AES128-SHA256", "ECDHE-ECDSA-AES128-SHA", "ECDHE-RSA-AES128-SHA",
            "ECDHE-ECDSA-AES256-GCM-SHA384", "ECDHE-RSA-AES256-GCM-SHA384", "ECDHE-ECDSA-AES256-SHA384",
            "ECDHE-RSA-AES256-SHA384", "ECDHE-RSA-AES256-SHA", "ECDHE-ECDSA-AES256-SHA",
            "AES128-GCM-SHA256", "AES128-SHA256", "AES128-SHA", "AES256-GCM-SHA384", "AES256-SHA256", "AES256-SHA"
        ]

    def set_ciphers(self, ciphers=None):
        self._ciphers = ciphers

    def get_ciphers(self):
        return self._ciphers

    # Not in use right now because lack of necessity of validate AWS IoT SSL Ciphers
    def validate_ciphers(self):
        # Getting intersection of valid ciphers between ciphers defined by user and AWS IoT valid ciphers.
        try:
            self._ciphers = ":".join(list(set(self._ciphers.split(":")) & set(self.aws_iot_valid_ciphers)))
        except Exception as e:
            print(e)
            self._ciphers = None
