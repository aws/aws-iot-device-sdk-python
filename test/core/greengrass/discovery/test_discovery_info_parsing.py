from AWSIoTPythonSDK.core.greengrass.discovery.models import DiscoveryInfo


DRS_INFO_JSON = "{\"GGGroups\":[{\"GGGroupId\":\"627bf63d-ae64-4f58-a18c-80a44fcf4088\"," \
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

EXPECTED_CORE_THING_ARN = "arn:aws:iot:us-east-1:003261610643:thing/DRS_GGC_0kegiNGA_0"
EXPECTED_GROUP_ID = "627bf63d-ae64-4f58-a18c-80a44fcf4088"
EXPECTED_CONNECTIVITY_INFO_ID_0 = "Id-0"
EXPECTED_CONNECTIVITY_INFO_ID_1 = "Id-1"
EXPECTED_CONNECTIVITY_INFO_ID_2 = "Id-2"
EXPECTED_CA = "-----BEGIN CERTIFICATE-----\n" \
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


class TestDiscoveryInfoParsing:

    def setup_method(self, test_method):
        self.discovery_info = DiscoveryInfo(DRS_INFO_JSON)

    def test_parsing_ggc_list_ca_list(self):
        ggc_list = self.discovery_info.getAllCores()
        ca_list = self.discovery_info.getAllCas()

        self._verify_core_connectivity_info_list(ggc_list)
        self._verify_ca_list(ca_list)

    def test_parsing_group_object(self):
        group_object = self.discovery_info.toObjectAtGroupLevel()
        self._verify_connectivity_info(group_object
                                       .get(EXPECTED_GROUP_ID)
                                       .getCoreConnectivityInfo(EXPECTED_CORE_THING_ARN)
                                       .getConnectivityInfo(EXPECTED_CONNECTIVITY_INFO_ID_0))
        self._verify_connectivity_info(group_object
                                       .get(EXPECTED_GROUP_ID)
                                       .getCoreConnectivityInfo(EXPECTED_CORE_THING_ARN)
                                       .getConnectivityInfo(EXPECTED_CONNECTIVITY_INFO_ID_1))
        self._verify_connectivity_info(group_object
                                       .get(EXPECTED_GROUP_ID)
                                       .getCoreConnectivityInfo(EXPECTED_CORE_THING_ARN)
                                       .getConnectivityInfo(EXPECTED_CONNECTIVITY_INFO_ID_2))

    def test_parsing_group_list(self):
        group_list = self.discovery_info.getAllGroups()

        assert len(group_list) == 1
        group_info = group_list[0]
        assert group_info.groupId == EXPECTED_GROUP_ID
        self._verify_ca_list(group_info.caList)
        self._verify_core_connectivity_info_list(group_info.coreConnectivityInfoList)

    def _verify_ca_list(self, actual_ca_list):
        assert len(actual_ca_list) == 1
        try:
            actual_group_id, actual_ca = actual_ca_list[0]
            assert actual_group_id == EXPECTED_GROUP_ID
            assert actual_ca == EXPECTED_CA
        except:
            assert actual_ca_list[0] == EXPECTED_CA

    def _verify_core_connectivity_info_list(self, actual_core_connectivity_info_list):
        assert len(actual_core_connectivity_info_list) == 1
        actual_core_connectivity_info = actual_core_connectivity_info_list[0]
        assert actual_core_connectivity_info.coreThingArn == EXPECTED_CORE_THING_ARN
        assert actual_core_connectivity_info.groupId == EXPECTED_GROUP_ID
        self._verify_connectivity_info_list(actual_core_connectivity_info.connectivityInfoList)

    def _verify_connectivity_info_list(self, actual_connectivity_info_list):
        for actual_connectivity_info in actual_connectivity_info_list:
            self._verify_connectivity_info(actual_connectivity_info)

    def _verify_connectivity_info(self, actual_connectivity_info):
        info_id = actual_connectivity_info.id
        sequence_number_string = info_id[-1:]
        assert actual_connectivity_info.host == "192.168.101." + sequence_number_string
        assert actual_connectivity_info.port == int("808" + sequence_number_string)
        assert actual_connectivity_info.metadata == "Description-" + sequence_number_string
