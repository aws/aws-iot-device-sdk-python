# This integration test verifies that TLS hostname verification is enforced
# when connecting to AWS IoT Core.
#
# It tests two scenarios:
# 1. A connection to the correct endpoint hostname succeeds (hostname matches certificate).
# 2. A connection using the endpoint's IP address (hostname mismatch) fails with an SSL error
#    because the certificate's CN/SAN contains the DNS name but not the IP address.
#
# Without the hostname verification fix, scenario 2 would have succeeded because
# only the CA chain was validated, not the hostname. With the fix, it correctly rejects.


import random
import string
import time
import ssl
import socket
import sys
sys.path.insert(0, "./test-integration/IntegrationTests/TestToolLibrary")
sys.path.insert(0, "./test-integration/IntegrationTests/TestToolLibrary/SDKPackage")

import TestToolLibrary.checkInManager as checkInManager
import TestToolLibrary.MQTTClientManager as MQTTClientManager
from TestToolLibrary.skip import skip_when_match
from TestToolLibrary.skip import ModeIsALPN
from TestToolLibrary.skip import Python2VersionLowerThan
from TestToolLibrary.skip import Python3VersionLowerThan


CLIENT_ID = "integrationTestHostnameVerification_" + "".join(random.choice(string.ascii_lowercase) for i in range(4))


############################################################################
# Main #
# Check inputs
myCheckInManager = checkInManager.checkInManager(2)
myCheckInManager.verify(sys.argv)

host = myCheckInManager.host
rootCA = "./test-integration/Credentials/rootCA.crt"
certificate = "./test-integration/Credentials/certificate.pem.crt"
privateKey = "./test-integration/Credentials/privateKey.pem.key"
mode = myCheckInManager.mode

############################################################################
# Test 1: Connection to correct hostname should SUCCEED
############################################################################
print("=" * 60)
print("Test 1: Connection to correct hostname should SUCCEED")
print("=" * 60)

myMQTTClientManager = MQTTClientManager.MQTTClientManager()
client = myMQTTClientManager.create_connected_mqtt_core(CLIENT_ID, host, rootCA, certificate, privateKey, mode=mode)

if client is None:
    print("FAILED: Could not connect to correct hostname: " + host)
    exit(4)

print("PASSED: Successfully connected to: " + host)
client.disconnect()
time.sleep(1)

############################################################################
# Test 2: Connection using IP address (hostname mismatch) should FAIL
############################################################################
print("")
print("=" * 60)
print("Test 2: Connection using IP address (hostname mismatch) should FAIL")
print("=" * 60)

# Resolve the real endpoint to its IP address
try:
    real_ip = socket.gethostbyname(host)
    print("Resolved " + host + " to IP: " + real_ip)
except socket.gaierror:
    print("SKIPPED: Could not resolve hostname.")
    exit(0)

# Create an AWSIoTMQTTClient using the IP address as the endpoint.
# The server's certificate SAN has the DNS name (e.g., *.iot.us-east-1.amazonaws.com)
# but NOT the IP address.
# With hostname verification (our fix): TLS rejects because IP is not in certificate SAN.
# Without hostname verification (old bug): TLS accepts because only CA chain is checked.
mismatchClient = myMQTTClientManager.create_nonconnected_mqtt_core(CLIENT_ID, real_ip, rootCA, certificate, privateKey, mode=mode)

connection_failed = False
try:
    mismatchClient.connect(keepAliveIntervalSecond=600)
    print("FAILED: Connection using IP address should have been rejected by hostname verification!")
    mismatchClient.disconnect()
    exit(4)
except ssl.SSLCertVerificationError as e:
    print("PASSED: Connection correctly rejected with SSLCertVerificationError: " + str(e))
    connection_failed = True
except ssl.SSLError as e:
    print("PASSED: Connection correctly rejected with SSLError: " + str(e))
    connection_failed = True
except socket.error as e:
    if "SSL" in str(e) or "certificate" in str(e).lower() or "hostname" in str(e).lower():
        print("PASSED: Connection correctly rejected with socket error: " + str(e))
        connection_failed = True
    else:
        print("FAILED: Unexpected socket error (not SSL-related): " + str(e))
        exit(4)
except Exception as e:
    # The SDK wraps SSL errors in its own exception types
    error_msg = str(e).lower()
    if "ssl" in error_msg or "certificate" in error_msg or "hostname" in error_msg or "tls" in error_msg:
        print("PASSED: Connection correctly rejected: " + str(type(e).__name__) + ": " + str(e))
        connection_failed = True
    else:
        print("FAILED: Unexpected exception: " + str(type(e).__name__) + ": " + str(e))
        exit(4)

if not connection_failed:
    print("FAILED: Connection using IP address was not rejected by hostname verification!")
    exit(4)

print("")
print("=" * 60)
print("ALL TESTS PASSED: Hostname verification is working correctly.")
print("=" * 60)