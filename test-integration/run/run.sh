#!/bin/bash
#
# This script manages the start of integration
# tests for Python core in AWS IoT Arduino Yun
# SDK. The tests should be able to run both in
# Brazil and ToD Worker environment.
# The script will perform the following tasks:
# 1. Retrieve credentials as needed from Odin
# 2. Obtain ZIP package and unzip it locally
# 3. Obtain Python executable
# 4. Start the integration tests and check results
# 5. Report any status returned.
# To start the tests as TodWorker:
# > run.sh <whichSDK> MutualAuth 1000 100 7
# or
# > run.sh <which SDK> Websocket 1000 100 7
# or
# > run.sh <which SDK> ALPN 1000 100 7
#
# To start the tests from desktop:
# > run.sh <which SDK> MutualAuthT 1000 100 7
# or
# > run.sh <which SDK> WebsocketT 1000 100 7
# or
# > run.sh <which SDK> ALPNT 1000 100 7
#
# 1000 MQTT messages, 100 bytes of random string
# in length and 7 rounds of network failure for 
# progressive backoff.
# Test mode (MutualAuth/Websocket) must be
# specified.
# Scale number must also be specified (see usage)

# Define const
USAGE="usage: run.sh <whichSDK> <testMode> <NumberOfMQTTMessages> <LengthOfShadowRandomString> <NumberOfNetworkFailure>"
OdinSetForMutualAuth_Desktop="com.amazon.aws.iot.sdk.desktop.certificate"
OdinSetForWebsocket_Desktop="com.amazon.aws.iot.sdk.desktop.websockets"
OdinSetForMutualAuth_TodWorker="com.amazonaws.iot.device.sdk.credentials.testing.certificates.us-east-1"
AWSMutualAuth_TodWorker_private_key="arn:aws:secretsmanager:us-east-1:123124136734:secret:V1IotSdkIntegrationTestPrivateKey-vNUQU8"
AWSMutualAuth_TodWorker_certificate="arn:aws:secretsmanager:us-east-1:123124136734:secret:V1IotSdkIntegrationTestCertificate-vTRwjE"

OdinSetForGGDiscovery_TodWorker="com.amazonaws.iot.device.sdk.credentials.testing.gg.discovery.us-east-1"
OdinSetForWebsocket_TodWorker="com.amazonaws.iot.device.sdk.credentials.testing.websocket"
RetrieveOdinMaterial="./test-integration/Tools/retrieve-material.sh"
RetrieveAWSKeys="./test-integration/Tools/retrieve-key.py"
CREDENTIAL_DIR="./test-integration/Credentials/"
TEST_DIR="./test-integration/IntegrationTests/"
CA_CERT_URL="https://www.amazontrust.com/repository/AmazonRootCA1.pem"
CA_CERT_PATH=${CREDENTIAL_DIR}rootCA.crt
ACCESS_KEY_ID_ARN="arn:aws:secretsmanager:us-east-1:123124136734:secret:V1IotSdkIntegrationTestWebsocketAccessKeyId-1YdB9z"
ACCESS_KEY_ARN="arn:aws:secretsmanager:us-east-1:123124136734:secret:V1IotSdkIntegrationTestWebsocketSecretAccessKey-MKTSaV"



# If input args not correct, echo usage
if [ $# -ne 5 ]; then
    echo ${USAGE}
else
# Description
    echo "[STEP] Start run.sh"
    echo "***************************************************"
    echo "About to start integration tests for $1..."
    echo "Test Mode: $2"
# Determine the Python versions need to test for this SDK
    pythonExecutableArray=()
    if [ "$1"x == "IoTYunSDK"x ]; then
        pythonExecutableArray[0]="2"
    elif [ "$1"x == "IoTPySDK"x ]; then
        pythonExecutableArray[0]="3"
    else
        echo "Cannot determine Python executables for this unrecognized SDK!"
        exit 1
    fi
# Retrieve credentials as needed from Odin
    TestMode=""
    echo "[STEP] Retrieve credentials from Odin"
    echo "***************************************************"
    if [ "$2"x == "MutualAuth"x -o "$2"x == "MutualAuthT"x ]; then
    	OdinSetName=${OdinSetForMutualAuth_TodWorker}
        AWSSetName_privatekey=${AWSMutualAuth_TodWorker_private_key}
    	AWSSetName_certificate=${AWSMutualAuth_TodWorker_certificate}
    	OdinSetDRSName=${OdinSetForGGDiscovery_TodWorker}
        TestMode="MutualAuth"
        if [ "$2"x == "MutualAuthT"x ]; then
            OdinSetName=${OdinSetForMutualAuth_Desktop}
        fi
    	OdinMaterialTypeCertificate="Certificate"
    	OdinMaterialTypeKey="PrivateKey"
    	python ${RetrieveAWSKeys} ${AWSSetName_certificate} > ${CREDENTIAL_DIR}certificate.pem.crt
    	python ${RetrieveAWSKeys} ${AWSSetName_privatekey} > ${CREDENTIAL_DIR}privateKey.pem.key
        curl -s "${CA_CERT_URL}" > ${CA_CERT_PATH}
        echo -e "URL retrieved certificate data:\n$(cat ${CA_CERT_PATH})\n"
    	#${RetrieveOdinMaterial} ${OdinSetDRSName} ${OdinMaterialTypeCertificate} > ${CREDENTIAL_DIR}certificate_drs.pem.crt
    	#${RetrieveOdinMaterial} ${OdinSetDRSName} ${OdinMaterialTypeKey} > ${CREDENTIAL_DIR}privateKey_drs.pem.key
    elif [ "$2"x == "Websocket"x -o "$2"x == "WebsocketT"x ]; then
    	OdinSetName=${OdinSetForWebsocket_TodWorker}
        TestMode="Websocket"
        if [ "$2"x == "WebsocketT"x ]; then
            OdinSetName=${OdinSetForWebsocket_Desktop}
        fi
    	OdinMaterialTypeID="Principal"
    	OdinMaterialTypeSecret="Credential"
        python ${RetrieveAWSKeys} ${ACCESS_KEY_ID_ARN} > KEY_ID
        python ${RetrieveAWSKeys} ${ACCESS_KEY_ARN} > SECRET_KEY
    	#SECRET_KEY=$(${RetrieveOdinMaterial} ${OdinSetName} ${OdinMaterialTypeSecret})
        export AWS_ACCESS_KEY_ID=${KEY_ID}
        export AWS_SECRET_ACCESS_KEY=${SECRET_KEY}
        curl -s "${CA_CERT_URL}" > ${CA_CERT_PATH}
        echo -e "URL retrieved certificate data:\n$(cat ${CA_CERT_PATH})\n"
    elif [ "$2"x == "ALPN"x -o "$2"x == "ALPNT"x ]; then
        OdinSetName=${OdinSetForMutualAuth_TodWorker}
    	OdinSetDRSName=${OdinSetForGGDiscovery_TodWorker}
        TestMode="ALPN"
        if [ "$2"x == "ALPNT"x ]; then
            OdinSetName=${OdinSetForMutualAuth_Desktop}
        fi
        OdinMaterialTypeCertificate="Certificate"
    	OdinMaterialTypeKey="PrivateKey"
    	${RetrieveOdinMaterial} ${OdinSetName} ${OdinMaterialTypeCertificate} > ${CREDENTIAL_DIR}certificate.pem.crt
    	${RetrieveOdinMaterial} ${OdinSetName} ${OdinMaterialTypeKey} > ${CREDENTIAL_DIR}privateKey.pem.key
        curl -s "${CA_CERT_URL}" > ${CA_CERT_PATH}
        echo -e "URL retrieved certificate data:\n$(cat ${CA_CERT_PATH})\n"
    	#${RetrieveOdinMaterial} ${OdinSetDRSName} ${OdinMaterialTypeCertificate} > ${CREDENTIAL_DIR}certificate_drs.pem.crt
    	#${RetrieveOdinMaterial} ${OdinSetDRSName} ${OdinMaterialTypeKey} > ${CREDENTIAL_DIR}privateKey_drs.pem.key
    else
    	echo "Mode not supported"
    	exit 1
    fi
# Obtain ZIP package and unzip it locally
    echo ${TestMode}
    echo "[STEP] Obtain ZIP package"
    echo "***************************************************"
    ZIPLocation="./AWSIoTPythonSDK"
    if [ $? -eq "-1" ]; then
    	echo "Cannot find SDK ZIP package"
    	exit 2
    fi
    if [ "$1"x ==  "IoTYunSDK"x ]; then
        unzip -q ${ZIPLocation} -d ./test-integration/IntegrationTests/TestToolLibrary/SDKPackage/
    elif [ "$1"x == "IoTPySDK"x ]; then
        cp -R ${ZIPLocation} ./test-integration/IntegrationTests/TestToolLibrary/SDKPackage/
    else
        echo "Error in getSDKZIP"
        exit 2
    fi
# Obtain Python executable
    for iii in "${pythonExecutableArray[@]}"
    do
        echo "***************************************************"
        for file in `ls ${TEST_DIR}`
        do
            # if [ ${file}x == "IntegrationTestMQTTConnection.py"x ]; then
            if [ ${file##*.}x == "py"x ]; then
                echo "[SUB] Running test: ${file}..."

                Scale=10
                case "$file" in
                    "IntegrationTestMQTTConnection.py") Scale=$3
                    ;;
                    "IntegrationTestShadow.py") Scale=$4
                    ;;
                    "IntegrationTestAutoReconnectResubscribe.py") Scale=""
                    ;;
                    "IntegrationTestProgressiveBackoff.py") Scale=$5
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

                python3 ${TEST_DIR}${file} ${TestMode} ${Scale}
                currentTestStatus=$?
                echo "[SUB] Test: ${file} completed. Exiting with status: ${currentTestStatus}"
                if [ ${currentTestStatus} -ne 0 ]; then
                    echo "!!!!!!!!!!!!!Test: ${file} in Python version ${iii}.x failed.!!!!!!!!!!!!!"
                    exit ${currentTestStatus}
                fi
                echo ""
            fi
        done
        echo "All integration tests passed for Python version ${iii}.x."
    done
fi
