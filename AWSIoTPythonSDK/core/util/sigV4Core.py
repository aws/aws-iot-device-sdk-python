# /*
# * Copyright 2010-2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

# This class implements the sigV4 signing process and return the signed URL for connection

import os
import datetime
import hashlib
import hmac
try:
    from urllib.parse import quote  # Python 3+
except ImportError:
    from urllib import quote
import logging
# INI config file handling
try:
    from configparser import ConfigParser  # Python 3+
    from configparser import NoOptionError
    from configparser import NoSectionError
except ImportError:
    from ConfigParser import ConfigParser
    from ConfigParser import NoOptionError
    from ConfigParser import NoSectionError

class sigV4Core:

    _logger = logging.getLogger(__name__)

    def __init__(self):
        self._aws_access_key_id = ""
        self._aws_secret_access_key = ""
        self._aws_session_token = ""
        self._credentialConfigFilePath = "~/.aws/credentials"

    def setIAMCredentials(self, srcAWSAccessKeyID, srcAWSSecretAccessKey, srcAWSSessionToken):
        self._aws_access_key_id = srcAWSAccessKeyID
        self._aws_secret_access_key = srcAWSSecretAccessKey
        self._aws_session_token = srcAWSSessionToken

    def _createAmazonDate(self):
        # Returned as a unicode string in Py3.x
        amazonDate = []
        currentTime = datetime.datetime.utcnow()
        YMDHMS = currentTime.strftime('%Y%m%dT%H%M%SZ')
        YMD = YMDHMS[0:YMDHMS.index('T')]
        amazonDate.append(YMD)
        amazonDate.append(YMDHMS)
        return amazonDate

    def _sign(self, key, message):
        # Returned as a utf-8 byte string in Py3.x
        return hmac.new(key, message.encode('utf-8'), hashlib.sha256).digest()

    def _getSignatureKey(self, key, dateStamp, regionName, serviceName):
        # Returned as a utf-8 byte string in Py3.x
        kDate = self._sign(('AWS4' + key).encode('utf-8'), dateStamp)
        kRegion = self._sign(kDate, regionName)
        kService = self._sign(kRegion, serviceName)
        kSigning = self._sign(kService, 'aws4_request')
        return kSigning

    def _checkIAMCredentials(self):
        # Check custom config
        ret = self._checkKeyInCustomConfig()
        # Check environment variables
        if not ret:
            ret = self._checkKeyInEnv()
        # Check files
        if not ret:
            ret = self._checkKeyInFiles()
        # All credentials returned as unicode strings in Py3.x
        return ret

    def _checkKeyInEnv(self):
        ret = dict()
        self._aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        self._aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        self._aws_session_token = os.environ.get('AWS_SESSION_TOKEN')
        if self._aws_access_key_id is not None and self._aws_secret_access_key is not None:
            ret["aws_access_key_id"] = self._aws_access_key_id
            ret["aws_secret_access_key"] = self._aws_secret_access_key
        # We do not necessarily need session token...
        if self._aws_session_token is not None:
            ret["aws_session_token"] = self._aws_session_token
        self._logger.debug("IAM credentials from env var.")
        return ret

    def _checkKeyInINIDefault(self, srcConfigParser, sectionName):
        ret = dict()
        # Check aws_access_key_id and aws_secret_access_key
        try:
            ret["aws_access_key_id"] = srcConfigParser.get(sectionName, "aws_access_key_id")
            ret["aws_secret_access_key"] = srcConfigParser.get(sectionName, "aws_secret_access_key")
        except NoOptionError:
            self._logger.warn("Cannot find IAM keyID/secretKey in credential file.")
        # We do not continue searching if we cannot even get IAM id/secret right
        if len(ret) == 2:
            # Check aws_session_token, optional
            try:
                ret["aws_session_token"] = srcConfigParser.get(sectionName, "aws_session_token")
            except NoOptionError:
                self._logger.debug("No AWS Session Token found.")
        return ret

    def _checkKeyInFiles(self):
        credentialFile = None
        credentialConfig = None
        ret = dict()
        # Should be compatible with aws cli default credential configuration
        # *NIX/Windows
        try:
            # See if we get the file
            credentialConfig = ConfigParser()
            credentialFilePath = os.path.expanduser(self._credentialConfigFilePath)  # Is it compatible with windows? \/
            credentialConfig.read(credentialFilePath)
            # Now we have the file, start looking for credentials...
            # 'default' section
            ret = self._checkKeyInINIDefault(credentialConfig, "default")
            if not ret:
                # 'DEFAULT' section
                ret = self._checkKeyInINIDefault(credentialConfig, "DEFAULT")
            self._logger.debug("IAM credentials from file.")
        except IOError:
            self._logger.debug("No IAM credential configuration file in " + credentialFilePath)
        except NoSectionError:
            self._logger.error("Cannot find IAM 'default' section.")
        return ret

    def _checkKeyInCustomConfig(self):
        ret = dict()
        if self._aws_access_key_id != "" and self._aws_secret_access_key != "":
            ret["aws_access_key_id"] = self._aws_access_key_id
            ret["aws_secret_access_key"] = self._aws_secret_access_key
        # We do not necessarily need session token...
        if self._aws_session_token != "":
            ret["aws_session_token"] = self._aws_session_token
        self._logger.debug("IAM credentials from custom config.")
        return ret

    def createWebsocketEndpoint(self, host, port, region, method, awsServiceName, path):
        # Return the endpoint as unicode string in 3.x
        # Gather all the facts
        amazonDate = self._createAmazonDate()
        amazonDateSimple = amazonDate[0]  # Unicode in 3.x
        amazonDateComplex = amazonDate[1]  # Unicode in 3.x
        allKeys = self._checkIAMCredentials()  # Unicode in 3.x
        hasCredentialsNecessaryForWebsocket = "aws_access_key_id" in allKeys.keys() and "aws_secret_access_key" in allKeys.keys()
        if not hasCredentialsNecessaryForWebsocket:
            return ""
        else:
            keyID = allKeys["aws_access_key_id"]
            secretKey = allKeys["aws_secret_access_key"]
            queryParameters = "X-Amz-Algorithm=AWS4-HMAC-SHA256" + \
                "&X-Amz-Credential=" + keyID + "%2F" + amazonDateSimple + "%2F" + region + "%2F" + awsServiceName + "%2Faws4_request" + \
                "&X-Amz-Date=" + amazonDateComplex + \
                "&X-Amz-Expires=86400" + \
                "&X-Amz-SignedHeaders=host"  # Unicode in 3.x
            hashedPayload = hashlib.sha256(str("").encode('utf-8')).hexdigest()  # Unicode in 3.x
            # Create the string to sign
            signedHeaders = "host"
            canonicalHeaders = "host:" + host + "\n"
            canonicalRequest = method + "\n" + path + "\n" + queryParameters + "\n" + canonicalHeaders + "\n" + signedHeaders + "\n" + hashedPayload  # Unicode in 3.x
            hashedCanonicalRequest = hashlib.sha256(str(canonicalRequest).encode('utf-8')).hexdigest()  # Unicoede in 3.x
            stringToSign = "AWS4-HMAC-SHA256\n" + amazonDateComplex + "\n" + amazonDateSimple + "/" + region + "/" + awsServiceName + "/aws4_request\n" + hashedCanonicalRequest  # Unicode in 3.x
            # Sign it
            signingKey = self._getSignatureKey(secretKey, amazonDateSimple, region, awsServiceName)
            signature = hmac.new(signingKey, (stringToSign).encode("utf-8"), hashlib.sha256).hexdigest()
            # generate url
            url = "wss://" + host + ":" + str(port) + path + '?' + queryParameters + "&X-Amz-Signature=" + signature
            # See if we have STS token, if we do, add it
            if "aws_session_token" in allKeys.keys():
                aws_session_token = allKeys["aws_session_token"]
                url += "&X-Amz-Security-Token=" + quote(aws_session_token.encode("utf-8"))  # Unicode in 3.x
            self._logger.debug("createWebsocketEndpoint: Websocket URL: " + url)
            return url
