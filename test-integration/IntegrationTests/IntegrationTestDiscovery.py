import sys
sys.path.insert(0, "./test-integration/IntegrationTests/TestToolLibrary")
sys.path.insert(0, "./test-integration/IntegrationTests/TestToolLibrary/SDKPackage")

from TestToolLibrary.SDKPackage.AWSIoTPythonSDK.core.greengrass.discovery.providers import DiscoveryInfoProvider
from TestToolLibrary.checkInManager import checkInManager
from TestToolLibrary.skip import skip_when_match
from TestToolLibrary.skip import ModeIsWebSocket


PORT = 8443
CA = "./test-integration/Credentials/rootCA.crt"
CERT = "./test-integration/Credentials/certificate_drs.pem.crt"
KEY = "./test-integration/Credentials/privateKey_drs.pem.key"
TIME_OUT_SEC = 30
# This is a pre-generated test data from DRS integration tests
ID_PREFIX = "Id-"
GGC_ARN = "arn:aws:iot:us-east-1:180635532705:thing/CI_Greengrass_Discovery_Thing"
GGC_PORT_NUMBER_BASE = 8080
GGC_HOST_ADDRESS_PREFIX = "192.168.101."
METADATA_PREFIX = "Description-"
GROUP_ID = "627bf63d-ae64-4f58-a18c-80a44fcf4088"
THING_NAME = "CI_Greengrass_Discovery_Thing"
EXPECTED_CA_CONTENT = "-----BEGIN CERTIFICATE-----\n" \
                "MIIEFTCCAv2gAwIBAgIVAPZfc4GMLZPmXbnoaZm6jRDqDs4+MA0GCSqGSIb3DQEB\n" \
                "CwUAMIGoMQswCQYDVQQGEwJVUzEYMBYGA1UECgwPQW1hem9uLmNvbSBJbmMuMRww\n" \
                "GgYDVQQLDBNBbWF6b24gV2ViIFNlcnZpY2VzMRMwEQYDVQQIDApXYXNoaW5ndG9u\n" \
                "MRAwDgYDVQQHDAdTZWF0dGxlMTowOAYDVQQDDDEwMDMyNjE2MTA2NDM6NjI3YmY2\n" \
                "M2QtYWU2NC00ZjU4LWExOGMtODBhNDRmY2Y0MDg4MCAXDTE3MDUyNTE4NDI1OVoY\n" \
                "DzIwOTcwNTI1MTg0MjU4WjCBqDELMAkGA1UEBhMCVVMxGDAWBgNVBAoMD0FtYXpv\n" \
                "bi5jb20gSW5jLjEcMBoGA1UECwwTQW1hem9uIFdlYiBTZXJ2aWNlczETMBEGA1UE\n" \
                "CAwKV2FzaGluZ3RvbjEQMA4GA1UEBwwHU2VhdHRsZTE6MDgGA1UEAwwxMDAzMjYx\n" \
                "NjEwNjQzOjYyN2JmNjNkLWFlNjQtNGY1OC1hMThjLTgwYTQ0ZmNmNDA4ODCCASIw\n" \
                "DQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAKEWtZtKyJUg2VUwZkbkVtltrfam\n" \
                "s9LMIdKNA3Wz4zSLhZjKHiTSkQmpZwKle5ziYs6Q5hfeT8WC0FNAVv1JhnwsuGfT\n" \
                "sG0UO5dSn7wqXOJigKC1CaSGqeFpKB0/a3wR1L6pCGVbLZ86/sPCEPHHJDieQ+Ps\n" \
                "RnOcUGb4CuIBnI2N+lafWNa4F4KRSVJCEeZ6u4iWVVdIEcDLKlakY45jtVvQqwnz\n" \
                "3leFsN7PTLEkVq5u1PXSbT5DWv6p+5NoDnGAT7j7Wbr2yJw7DtpBOL6oWkAdbFAQ\n" \
                "2097e8mIxNYE9xAzRlb5wEr6jZl/8K60v9P83OapMeuOg4JS8FGulHXbDg0CAwEA\n" \
                "AaMyMDAwDwYDVR0TAQH/BAUwAwEB/zAdBgNVHQ4EFgQU21ELaPCH9Oh001OS0JMv\n" \
                "n8hU8dYwDQYJKoZIhvcNAQELBQADggEBABW66eH/+/v9Nq5jtJzflfrqAfBOzWLj\n" \
                "UTEv6szkYzV5Crr8vnu2P5OlyA0NdiKGiAm0AgoDkf+n9HU3Hc0zm3G/QaAO2UmN\n" \
                "9MwtIp29BSRf+gd1bX/WZTtl5I5xl290BDfr5o08I6TOf0A4P8IAkGwku5j0IQjM\n" \
                "ns2HH5UVki155dtmWDEGX6q35KABbsmv3tO1+geJVYnd1QkHzR5IXA12gxlMw9GJ\n" \
                "+cOw+rwJJ2ZcXo3HFoXBcsPqPOa1SO3vTl3XWQ+jX3vyDsxh/VGoJ4epsjwmJ+dW\n" \
                "sHJoqsa3ZPDW0LcEuYgdzYWRhumGwH9fJJUx0GS4Tdg4ud+6jpuyflU=\n" \
                "-----END CERTIFICATE-----\n"
# The expected response from DRS should be:
'''
{
  "GGGroups": [
    {
      "GGGroupId": "627bf63d-ae64-4f58-a18c-80a44fcf4088",
      "Cores": [
        {
          "thingArn": "arn:aws:iot:us-east-1:003261610643:thing\/DRS_GGC_0kegiNGA_0",
          "Connectivity": [
            {
              "Id": "Id-0",
              "HostAddress": "192.168.101.0",
              "PortNumber": 8080,
              "Metadata": "Description-0"
            },
            {
              "Id": "Id-1",
              "HostAddress": "192.168.101.1",
              "PortNumber": 8081,
              "Metadata": "Description-1"
            },
            {
              "Id": "Id-2",
              "HostAddress": "192.168.101.2",
              "PortNumber": 8082,
              "Metadata": "Description-2"
            }
          ]
        }
      ],
      "CAs": [
        "-----BEGIN CERTIFICATE-----\n
        MIIEFTCCAv2gAwIBAgIVAPZfc4GMLZPmXbnoaZm6jRDqDs4+MA0GCSqGSIb3DQEB\n
        CwUAMIGoMQswCQYDVQQGEwJVUzEYMBYGA1UECgwPQW1hem9uLmNvbSBJbmMuMRww\n
        GgYDVQQLDBNBbWF6b24gV2ViIFNlcnZpY2VzMRMwEQYDVQQIDApXYXNoaW5ndG9u\n
        MRAwDgYDVQQHDAdTZWF0dGxlMTowOAYDVQQDDDEwMDMyNjE2MTA2NDM6NjI3YmY2\n
        M2QtYWU2NC00ZjU4LWExOGMtODBhNDRmY2Y0MDg4MCAXDTE3MDUyNTE4NDI1OVoY\n
        DzIwOTcwNTI1MTg0MjU4WjCBqDELMAkGA1UEBhMCVVMxGDAWBgNVBAoMD0FtYXpv\n
        bi5jb20gSW5jLjEcMBoGA1UECwwTQW1hem9uIFdlYiBTZXJ2aWNlczETMBEGA1UE\n
        CAwKV2FzaGluZ3RvbjEQMA4GA1UEBwwHU2VhdHRsZTE6MDgGA1UEAwwxMDAzMjYx\n
        NjEwNjQzOjYyN2JmNjNkLWFlNjQtNGY1OC1hMThjLTgwYTQ0ZmNmNDA4ODCCASIw\n
        DQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAKEWtZtKyJUg2VUwZkbkVtltrfam\n
        s9LMIdKNA3Wz4zSLhZjKHiTSkQmpZwKle5ziYs6Q5hfeT8WC0FNAVv1JhnwsuGfT\n
        sG0UO5dSn7wqXOJigKC1CaSGqeFpKB0\/a3wR1L6pCGVbLZ86\/sPCEPHHJDieQ+Ps\n
        RnOcUGb4CuIBnI2N+lafWNa4F4KRSVJCEeZ6u4iWVVdIEcDLKlakY45jtVvQqwnz\n
        3leFsN7PTLEkVq5u1PXSbT5DWv6p+5NoDnGAT7j7Wbr2yJw7DtpBOL6oWkAdbFAQ\n
        2097e8mIxNYE9xAzRlb5wEr6jZl\/8K60v9P83OapMeuOg4JS8FGulHXbDg0CAwEA\n
        AaMyMDAwDwYDVR0TAQH\/BAUwAwEB\/zAdBgNVHQ4EFgQU21ELaPCH9Oh001OS0JMv\n
        n8hU8dYwDQYJKoZIhvcNAQELBQADggEBABW66eH\/+\/v9Nq5jtJzflfrqAfBOzWLj\n
        UTEv6szkYzV5Crr8vnu2P5OlyA0NdiKGiAm0AgoDkf+n9HU3Hc0zm3G\/QaAO2UmN\n
        9MwtIp29BSRf+gd1bX\/WZTtl5I5xl290BDfr5o08I6TOf0A4P8IAkGwku5j0IQjM\n
        ns2HH5UVki155dtmWDEGX6q35KABbsmv3tO1+geJVYnd1QkHzR5IXA12gxlMw9GJ\n
        +cOw+rwJJ2ZcXo3HFoXBcsPqPOa1SO3vTl3XWQ+jX3vyDsxh\/VGoJ4epsjwmJ+dW\n
        sHJoqsa3ZPDW0LcEuYgdzYWRhumGwH9fJJUx0GS4Tdg4ud+6jpuyflU=\n
        -----END CERTIFICATE-----\n"
      ]
    }
  ]
}
'''

my_check_in_manager = checkInManager(2)
my_check_in_manager.verify(sys.argv)
mode = my_check_in_manager.mode
host = my_check_in_manager.host

def create_discovery_info_provider():
    discovery_info_provider = DiscoveryInfoProvider()
    discovery_info_provider.configureEndpoint(host, PORT)
    discovery_info_provider.configureCredentials(CA, CERT, KEY)
    discovery_info_provider.configureTimeout(TIME_OUT_SEC)
    return discovery_info_provider


def perform_integ_test_discovery():
    discovery_info_provider = create_discovery_info_provider()
    return discovery_info_provider.discover(THING_NAME)


def _verify_connectivity_info(actual_connectivity_info):
    info_id = actual_connectivity_info.id
    sequence_number_string = info_id[-1:]
    assert actual_connectivity_info.host == GGC_HOST_ADDRESS_PREFIX + sequence_number_string
    assert actual_connectivity_info.port == GGC_PORT_NUMBER_BASE + int(sequence_number_string)
    assert actual_connectivity_info.metadata == METADATA_PREFIX + sequence_number_string


def _verify_connectivity_info_list(actual_connectivity_info_list):
    for actual_connectivity_info in actual_connectivity_info_list:
        _verify_connectivity_info(actual_connectivity_info)


def _verify_ggc_info(actual_ggc_info):
    assert actual_ggc_info.coreThingArn == GGC_ARN
    assert actual_ggc_info.groupId == GROUP_ID
    _verify_connectivity_info_list(actual_ggc_info.connectivityInfoList)


def _verify_ca_list(ca_list):
    assert len(ca_list) == 1
    try:
        group_id, ca = ca_list[0]
        assert group_id == GROUP_ID
        assert ca == EXPECTED_CA_CONTENT
    except:
        assert ca_list[0] == EXPECTED_CA_CONTENT


def verify_all_cores(discovery_info):
    ggc_info_list = discovery_info.getAllCores()
    print("Verifying \"getAllCores\"... {0}".format(len(ggc_info_list)))
    _verify_ggc_info(ggc_info_list[0])
    print("Pass!")


def verify_all_cas(discovery_info):
    print("Verifying \"getAllCas\"...")
    ca_list = discovery_info.getAllCas()
    _verify_ca_list(ca_list)
    print("Pass!")


def verify_all_groups(discovery_info):
    print("Verifying \"getAllGroups\"...")
    group_list = discovery_info.getAllGroups()
    assert len(group_list) == 1
    group_info = group_list[0]
    _verify_ca_list(group_info.caList)
    _verify_ggc_info(group_info.coreConnectivityInfoList[0])
    print("Pass!")


def verify_group_object(discovery_info):
    print("Verifying \"toObjectAtGroupLevel\"...")
    group_info_object = discovery_info.toObjectAtGroupLevel()
    _verify_connectivity_info(group_info_object
                              .get(GROUP_ID)
                              .getCoreConnectivityInfo(GGC_ARN)
                              .getConnectivityInfo(ID_PREFIX + "0"))
    _verify_connectivity_info(group_info_object
                              .get(GROUP_ID)
                              .getCoreConnectivityInfo(GGC_ARN)
                              .getConnectivityInfo(ID_PREFIX + "1"))
    _verify_connectivity_info(group_info_object
                              .get(GROUP_ID)
                              .getCoreConnectivityInfo(GGC_ARN)
                              .getConnectivityInfo(ID_PREFIX + "2"))
    print("Pass!")


############################################################################
# Main #

skip_when_match(ModeIsWebSocket(mode), "This test is not applicable for mode: %s. Skipping..." % mode)

# GG Discovery only applies mutual auth with cert
try:
    discovery_info = perform_integ_test_discovery()

    verify_all_cores(discovery_info)
    verify_all_cas(discovery_info)
    verify_all_groups(discovery_info)
    verify_group_object(discovery_info)
except BaseException as e:
    print("Failed! " + e.message)
    exit(4)
