# This integration test verifies that TLS hostname verification is enforced
# when connecting to the Greengrass discovery endpoint on port 8443.
#
# It tests two scenarios:
# 1. A discovery request to the correct endpoint hostname completes the TLS handshake.
# 2. A discovery request using the endpoint's IP address (hostname mismatch) fails
#    because the certificate's CN/SAN contains the DNS name but not the IP address.
#
# Scenario 2 first performs a control handshake to the same IP with hostname checking
# disabled. If that succeeds, the server's certificate chain is trusted, so a rejection
# by the SDK can only come from hostname verification. This avoids depending on
# TLS-backend-specific error codes or messages.
#
# Without the hostname verification fix, scenario 2 would have succeeded on Python 3.7+
# because only the CA chain was validated, not the hostname.


import ssl
import socket
import sys
sys.path.insert(0, "./test-integration/IntegrationTests/TestToolLibrary")
sys.path.insert(0, "./test-integration/IntegrationTests/TestToolLibrary/SDKPackage")

from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.core.greengrass.discovery.providers import DiscoveryInfoProvider
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.exception.AWSIoTExceptions import DiscoveryFailure
from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.exception.AWSIoTExceptions import DiscoveryTimeoutException
from TestToolLibrary.checkInManager import checkInManager
from TestToolLibrary.skip import skip_when_match
from TestToolLibrary.skip import ModeIsWebSocket


PORT = 8443
CA = "./test-integration/Credentials/rootCA.crt"
CERT = "./test-integration/Credentials/certificate_drs.pem.crt"
KEY = "./test-integration/Credentials/privateKey_drs.pem.key"
TIME_OUT_SEC = 30
THING_NAME = "DRS_GGAD_0kegiNGA_0"


def create_discovery_info_provider(endpoint):
    discovery_info_provider = DiscoveryInfoProvider()
    discovery_info_provider.configureEndpoint(endpoint, PORT)
    discovery_info_provider.configureCredentials(CA, CERT, KEY)
    discovery_info_provider.configureTimeout(TIME_OUT_SEC)
    return discovery_info_provider


def handshake_without_hostname_check(ip):
    # Same CA and client credentials as the SDK, but only the certificate chain is verified
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    ssl_context.load_verify_locations(CA)
    ssl_context.load_cert_chain(CERT, KEY)
    sock = socket.create_connection((ip, PORT), timeout=TIME_OUT_SEC)
    try:
        ssl_context.wrap_socket(sock, server_hostname=ip).close()
    finally:
        sock.close()


############################################################################
# Main #
# Check inputs
my_check_in_manager = checkInManager(2)
my_check_in_manager.verify(sys.argv)
mode = my_check_in_manager.mode
host = my_check_in_manager.host

# GG Discovery only applies mutual auth with cert
skip_when_match(ModeIsWebSocket(mode), "This test is not applicable for mode: %s. Skipping..." % mode)

############################################################################
# Test 1: Discovery against the correct hostname should complete the TLS handshake
############################################################################
print("=" * 60)
print("Test 1: Discovery against correct hostname should SUCCEED")
print("=" * 60)

try:
    create_discovery_info_provider(host).discover(THING_NAME)
    print("PASSED: Discovery succeeded against: " + host)
except ssl.SSLError as e:
    print("FAILED: TLS handshake with correct hostname was rejected: " + str(e))
    exit(4)
except (DiscoveryFailure, DiscoveryTimeoutException) as e:
    # The TLS handshake completed; the service-level failure is covered by IntegrationTestDiscovery
    print("PASSED: TLS handshake succeeded against: " + host + " (discovery returned: " + type(e).__name__ + ")")

############################################################################
# Test 2: Discovery using the IP address (hostname mismatch) should FAIL
############################################################################
print("")
print("=" * 60)
print("Test 2: Discovery using IP address (hostname mismatch) should FAIL")
print("=" * 60)

try:
    real_ip = socket.gethostbyname(host)
    print("Resolved " + host + " to IP: " + real_ip)
except socket.gaierror:
    print("SKIPPED: Could not resolve hostname.")
    exit(0)

try:
    handshake_without_hostname_check(real_ip)
    print("Control: certificate chain from " + real_ip + " is trusted when the hostname is not checked")
except (ssl.SSLError, socket.error) as e:
    print("FAILED: Control handshake to " + real_ip + " failed, so a hostname mismatch cannot be isolated: " + str(e))
    exit(4)

try:
    create_discovery_info_provider(real_ip).discover(THING_NAME)
    print("FAILED: Discovery using IP address should have been rejected by hostname verification!")
    exit(4)
except ssl.SSLError as e:
    print("PASSED: Discovery correctly rejected by hostname verification: " + str(e))

print("")
print("=" * 60)
print("ALL TESTS PASSED: Discovery hostname verification is working correctly.")
print("=" * 60)
