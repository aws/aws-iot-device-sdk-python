#!/bin/bash
#
# This script manages the start of integration
# tests for Python core in AWS IoT Arduino Yun
# SDK. The tests should be able to run both in
# Brazil and ToD Worker environment.
# The script will perform the following tasks:
# 1. Retrieve credentials as needed from AWS
# 2. Obtain ZIP package and unzip it locally
# 3. Start the integration tests and check results
# 4. Report any status returned.
# To start the tests as TodWorker:
# > run.sh MutualAuth 1000 100 7
# or
# > run.sh Websocket 1000 100 7
# or
# > run.sh ALPN 1000 100 7
#
# To start the tests from desktop:
# > run.sh MutualAuthT 1000 100 7
# or
# > run.sh WebsocketT 1000 100 7
# or
# > run.sh ALPNT 1000 100 7
#
# 1000 MQTT messages, 100 bytes of random string
# in length and 7 rounds of network failure for 
# progressive backoff.
# Test mode (MutualAuth/Websocket) must be
# specified.
# Scale number must also be specified (see usage)

# Define const
USAGE="usage: run.sh <testMode> <NumberOfMQTTMessages> <LengthOfShadowRandomString> <NumberOfNetworkFailure>"

AWSHost="arn:aws:secretsmanager:us-east-1:180635532705:secret:unit-test/endpoint-HSpeEu"

AWSMutualAuth_TodWorker_private_key="arn:aws:secretsmanager:us-east-1:180635532705:secret:ci/mqtt5/us/Mqtt5Prod/key-kqgyvf"
AWSMutualAuth_TodWorker_certificate="arn:aws:secretsmanager:us-east-1:180635532705:secret:ci/mqtt5/us/Mqtt5Prod/cert-VDI1Gd"

# AWSGGDiscovery_TodWorker_private_key="arn:aws:secretsmanager:us-east-1:180635532705:secret:ci/greengrassv1/key-QEWWRI"
# AWSGGDiscovery_TodWorker_certificate="arn:aws:secretsmanager:us-east-1:180635532705:secret:ci/greengrassv1/cert-2GJc26"

# AWSGGDiscovery_TodWorker_private_key="arn:aws:secretsmanager:us-east-1:180635532705:secret:ci/GreengrassDiscovery/key-Ki81FY"
# AWSGGDiscovery_TodWorker_certificate="arn:aws:secretsmanager:us-east-1:180635532705:secret:ci/GreengrassDiscovery/cert-bxUN3i"

AWSGGDiscovery_TodWorker_private_key="arn:aws:secretsmanager:us-east-1:180635532705:secret:ci/Greengrass/key-tHGj1k"
AWSGGDiscovery_TodWorker_certificate="arn:aws:secretsmanager:us-east-1:180635532705:secret:ci/Greengrass/cert-6RYeYf"


# AWSSecretForWebsocket_TodWorker_KeyId="arn:aws:secretsmanager:us-east-1:123124136734:secret:V1IotSdkIntegrationTestWebsocketAccessKeyId-1YdB9z"
# AWSSecretForWebsocket_TodWorker_SecretKey="arn:aws:secretsmanager:us-east-1:123124136734:secret:V1IotSdkIntegrationTestWebsocketSecretAccessKey-MKTSaV"


SDKLocation="./AWSIoTPythonSDK"
RetrieveAWSKeys="./test-integration/Tools/retrieve-key.py"
CREDENTIAL_DIR="./test-integration/Credentials/"
TEST_DIR="./test-integration/IntegrationTests/"
CA_CERT_URL="https://www.amazontrust.com/repository/AmazonRootCA1.pem"
CA_CERT_PATH=${CREDENTIAL_DIR}rootCA.crt
TestHost=$(python3 ${RetrieveAWSKeys} ${AWSHost})
echo ${TestHost}




# If input args not correct, echo usage
if [ $# -ne 4 ]; then
    echo ${USAGE}
else
# Description
    echo "[STEP] Start run.sh"
    echo "***************************************************"
    echo "About to start integration tests for IoTPySDK..."
    echo "Test Mode: $1"
# Determine the Python versions need to test for this SDK
    pythonExecutableArray=()
    pythonExecutableArray[0]="3"
# Retrieve credentials as needed from AWS
    TestMode=""
    echo "[STEP] Retrieve credentials from AWS"
    echo "***************************************************"
    if [ "$1"x == "MutualAuth"x ]; then
        AWSSetName_privatekey=${AWSMutualAuth_TodWorker_private_key}
    	  AWSSetName_certificate=${AWSMutualAuth_TodWorker_certificate}
    	  AWSDRSName_privatekey=${AWSGGDiscovery_TodWorker_private_key}
        AWSDRSName_certificate=${AWSGGDiscovery_TodWorker_certificate}
        TestMode="MutualAuth"
    	  python ${RetrieveAWSKeys} ${AWSSetName_certificate} > ${CREDENTIAL_DIR}certificate.pem.crt
    	  python ${RetrieveAWSKeys} ${AWSSetName_privatekey} > ${CREDENTIAL_DIR}privateKey.pem.key
        curl -s "${CA_CERT_URL}" > ${CA_CERT_PATH}
        echo -e "URL retrieved certificate data\n"
    	  python ${RetrieveAWSKeys} ${AWSDRSName_certificate} > ${CREDENTIAL_DIR}certificate_drs.pem.crt
    	  python ${RetrieveAWSKeys} ${AWSDRSName_privatekey} > ${CREDENTIAL_DIR}privateKey_drs.pem.key
    elif [ "$1"x == "Websocket"x ]; then
        TestMode="Websocket"
        curl -s "${CA_CERT_URL}" > ${CA_CERT_PATH}
        echo -e "URL retrieved certificate data\n"
    elif [ "$1"x == "ALPN"x ]; then
        AWSSetName_privatekey=${AWSMutualAuth_TodWorker_private_key}
    	  AWSSetName_certificate=${AWSMutualAuth_TodWorker_certificate}
    	  AWSDRSName_privatekey=${AWSGGDiscovery_TodWorker_private_key}
        AWSDRSName_certificate=${AWSGGDiscovery_TodWorker_certificate}
        TestMode="ALPN"
        python ${RetrieveAWSKeys} ${AWSSetName_certificate} > ${CREDENTIAL_DIR}certificate.pem.crt
    	  python ${RetrieveAWSKeys} ${AWSSetName_privatekey} > ${CREDENTIAL_DIR}privateKey.pem.key
        curl -s "${CA_CERT_URL}" > ${CA_CERT_PATH}
        echo -e "URL retrieved certificate data\n"
    	  python ${RetrieveAWSKeys} ${AWSDRSName_certificate} > ${CREDENTIAL_DIR}certificate_drs.pem.crt
    	  python ${RetrieveAWSKeys} ${AWSDRSName_privatekey} > ${CREDENTIAL_DIR}privateKey_drs.pem.key
    else
    	  echo "Mode not supported"
    	  exit 1
    fi
# Obtain ZIP package and unzip it locally
    echo ${TestMode}
    echo "[STEP] Obtain ZIP package"
    echo "***************************************************"
    cp -R ${SDKLocation} ./test-integration/IntegrationTests/TestToolLibrary/SDKPackage/
# Obtain Python executable

    echo "***************************************************"
    for file in `ls ${TEST_DIR}`
    do
        # SKIP discovery for now
        if [ ${file}x != "IntegrationTestDiscovery.py"x ]; then
            continue;
        fi
        if [ ${file##*.}x == "py"x ]; then
            echo "[SUB] Running test: ${file}..."
            
            Scale=10
            case "$file" in
                "IntegrationTestMQTTConnection.py") Scale=$2
                ;;
                "IntegrationTestShadow.py") Scale=$3
                ;;
                "IntegrationTestAutoReconnectResubscribe.py") Scale=""
                ;;
                "IntegrationTestProgressiveBackoff.py") Scale=$4
                ;;
                "IntegrationTestConfigurablePublishMessageQueueing.py") Scale=""
                ;;
                "IntegrationTestDiscovery.py") Scale=""
                ;;
                "IntegrationTestAsyncAPIGeneralNotificationCallbacks.py") Scale=""
                ;;
                "IntegrationTestOfflineQueueingForSubscribeUnsubscribe.py") Scale=""
                ;;
                "IntegrationTestClientReusability.py") Scale=""
                ;;
                "IntegrationTestJobsClient.py") Scale=""
            esac

            python ${TEST_DIR}${file} ${TestMode} ${TestHost} ${Scale}
            currentTestStatus=$?
            echo "[SUB] Test: ${file} completed. Exiting with status: ${currentTestStatus}"
            if [ ${currentTestStatus} -ne 0 ]; then
                echo "!!!!!!!!!!!!!Test: ${file} failed.!!!!!!!!!!!!!"
                exit ${currentTestStatus}
            fi
            echo ""
        fi
    done
    echo "All integration tests passed"
fi
