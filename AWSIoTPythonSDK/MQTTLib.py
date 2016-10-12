#
#/*
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

# import mqttCore
import core.protocol.mqttCore as mqttCore
# import shadowManager
import core.shadow.shadowManager as shadowManager
# import deviceShadow
import core.shadow.deviceShadow as deviceShadow
# Constants
# - Protocol types:
MQTTv3_1 = 3
MQTTv3_1_1 = 4
# - OfflinePublishQueueing drop behavior:
DROP_OLDEST = 0
DROP_NEWEST = 1
#

class AWSIoTMQTTClient:

    def __init__(self, clientID, protocolType=MQTTv3_1_1, useWebsocket=False, cleanSession=True):
        """

        The client class that connects to and accesses AWS IoT over MQTT v3.1/3.1.1.

        The following connection types are available:

        - TLSv1.2 Mutual Authentication

        X.509 certificate-based secured MQTT connection to AWS IoT
        
        - Websocket SigV4

        IAM credential-based secured MQTT connection over Websocket to AWS IoT

        It provides basic synchronous MQTT operations in the classic MQTT publish-subscribe 
        model, along with configurations of on-top features:

        - Auto reconnect/resubscribe

        - Progressive reconnect backoff

        - Offline publish requests queueing with draining

        **Syntax**

        .. code:: python

          import AWSIoTPythonSDK.MQTTLib as AWSIoTPyMQTT

          # Create an AWS IoT MQTT Client using TLSv1.2 Mutual Authentication
          myAWSIoTMQTTClient = AWSIoTPyMQTT.AWSIoTMQTTClient("testIoTPySDK")
          # Create an AWS IoT MQTT Client using Websocket SigV4
          myAWSIoTMQTTClient = AWSIoTPyMQTT.AWSIoTMQTTClient("testIoTPySDK", useWebsocket=True)

        **Parameters**

        *clientID* - String that denotes the client identifier used to connect to AWS IoT.
        If empty string were provided, client id for this connection will be randomly generated 
        n server side.

        *protocolType* - MQTT version in use for this connection. Could be :code:`AWSIoTPythonSDK.MQTTLib.MQTTv3_1` or :code:`AWSIoTPythonSDK.MQTTLib.MQTTv3_1_1`

        *useWebsocket* - Boolean that denotes enabling MQTT over Websocket SigV4 or not.

        **Returns**

        AWSIoTPythonSDK.MQTTLib.AWSIoTMQTTClient object

        """
        # mqttCore(clientID, cleanSession, protocol, srcLogManager, srcUseWebsocket=False)
        self._mqttCore = mqttCore.mqttCore(clientID, cleanSession, protocolType, useWebsocket)

    # Configuration APIs
    def configureLastWill(self, topic, payload, QoS):
        """
        **Description**

        Used to configure the last will topic, payload and QoS of the client. Should be called before connect.

        **Syntax**

        .. code:: python
          myAWSIoTMQTTClient.configureLastWill("last/Will/Topic", "lastWillPayload", 0)

        **Parameters**

        *topic* - Topic name that last will publishes to.

        *payload* - Payload to publish for last will.

        *QoS* - Quality of Service. Could be 0 or 1.

        **Returns**

        None

        """
        # mqttCore.setLastWill(srcTopic, srcPayload, srcQos)
        self._mqttCore.setLastWill(topic, payload, QoS)

    def clearLastWill(self):
        """
        **Description**

        Used to clear the last will configuration that is previously set through configureLastWill.

        **Syntax**

        ..code:: python
          myAWSIoTMQTTClient.clearLastWill()

        **Parameter**

        None

        **Returns**

        None
        
        """
        #mqttCore.clearLastWill()
        self._mqttCore.clearLastWill()

    def configureEndpoint(self, hostName, portNumber):
        """
        **Description**

        Used to configure the host name and port number the client tries to connect to. Should be called
        before connect.

        **Syntax**

        .. code:: python

          myAWSIoTMQTTClient.configureEndpoint("random.iot.region.amazonaws.com", 8883)

        **Parameters**

        *hostName* - String that denotes the host name of the user-specific AWS IoT endpoint.

        *portNumber* - Integer that denotes the port number to connect to. Could be :code:`8883` for
        TLSv1.2 Mutual Authentication or :code:`443` for Websocket SigV4.

        **Returns**

        None

        """
        # mqttCore.configEndpoint(srcHost, srcPort)
        self._mqttCore.configEndpoint(hostName, portNumber)

    def configureIAMCredentials(self, AWSAccessKeyID, AWSSecretAccessKey, AWSSessionToken=""):
        """
        **Description**

        Used to configure/update the custom IAM credentials for Websocket SigV4 connection to 
        AWS IoT. Should be called before connect.

        **Syntax**

        .. code:: python

          myAWSIoTMQTTClient.configureIAMCredentials(obtainedAccessKeyID, obtainedSecretAccessKey, obtainedSessionToken)

        .. note::

          Hard-coding credentials into custom script is NOT recommended. Please use AWS Cognito identity service
          or other credential provider.

        **Parameters**

        *AWSAccessKeyID* - AWS Access Key Id from user-specific IAM credentials.

        *AWSSecretAccessKey* - AWS Secret Access Key from user-specific IAM credentials.

        *AWSSessionToken* - AWS Session Token for temporary authentication from STS.

        **Returns**

        None

        """
        # mqttCore.configIAMCredentials(srcAWSAccessKeyID, srcAWSSecretAccessKey, srcAWSSessionToken)
        self._mqttCore.configIAMCredentials(AWSAccessKeyID, AWSSecretAccessKey, AWSSessionToken)

    def configureCredentials(self, CAFilePath, KeyPath="", CertificatePath=""):  # Should be good for MutualAuth certs config and Websocket rootCA config
        """
        **Description**

        Used to configure the rootCA, private key and certificate files. Should be called before connect.

        **Syntax**

        .. code:: python

          myAWSIoTMQTTClient.configureCredentials("PATH/TO/ROOT_CA", "PATH/TO/PRIVATE_KEY", "PATH/TO/CERTIFICATE")

        **Parameters**

        *CAFilePath* - Path to read the root CA file. Required for all connection types.

        *KeyPath* - Path to read the private key. Required for X.509 certificate based connection.

        *CertificatePath* - Path to read the certificate. Required for X.509 certificate based connection.

        **Returns**

        None

        """
        # mqttCore.configCredentials(srcCAFile, srcKey, srcCert)
        self._mqttCore.configCredentials(CAFilePath, KeyPath, CertificatePath)

    def configureAutoReconnectBackoffTime(self, baseReconnectQuietTimeSecond, maxReconnectQuietTimeSecond, stableConnectionTimeSecond):
        """
        **Description**

        Used to configure the auto-reconnect backoff timing. Should be called before connect.

        **Syntax**

        .. code:: python

          # Configure the auto-reconnect backoff to start with 1 second and use 128 seconds as a maximum back off time.
          # Connection over 20 seconds is considered stable and will reset the back off time back to its base.
          myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 128, 20)

        **Parameters**

        *baseReconnectQuietTimeSecond* - The initial back off time to start with, in seconds. 
        Should be less than the stableConnectionTime.

        *maxReconnectQuietTimeSecond* - The maximum back off time, in seconds.

        *stableConnectionTimeSecond* - The number of seconds for a connection to last to be considered as stable. 
        Back off time will be reset to base once the connection is stable.

        **Returns**

        None

        """
        # mqttCore.setBackoffTime(srcBaseReconnectTimeSecond, srcMaximumReconnectTimeSecond, srcMinimumConnectTimeSecond)
        self._mqttCore.setBackoffTime(baseReconnectQuietTimeSecond, maxReconnectQuietTimeSecond, stableConnectionTimeSecond)

    def configureOfflinePublishQueueing(self, queueSize, dropBehavior=DROP_NEWEST):
        """
        **Description**

        Used to configure the queue size and drop behavior for the offline publish requests queueing. Should be 
        called before connect.

        **Syntax**

        .. code:: python

          import AWSIoTPythonSDK.MQTTLib as AWSIoTPyMQTT

          # Configure the offline queue for publish requests to be 20 in size and drop the oldest
           request when the queue is full.
          myAWSIoTMQTTClient.configureOfflinePublishQueueing(20, AWSIoTPyMQTT.DROP_OLDEST)

        **Parameters**

        *queueSize* - Size of the queue for offline publish requests queueing.
         If set to 0, the queue is disabled. If set to -1, the queue size is set to be infinite.

        *dropBehavior* - the type of drop behavior when the queue is full.
         Could be :code:`AWSIoTPythonSDK.MQTTLib.DROP_OLDEST` or :code:`AWSIoTPythonSDK.MQTTLib.DROP_NEWEST`.

        **Returns**

        None

        """
        # mqttCore.setOfflinePublishQueueing(srcQueueSize, srcDropBehavior=mqtt.MSG_QUEUEING_DROP_NEWEST)
        self._mqttCore.setOfflinePublishQueueing(queueSize, dropBehavior)

    def configureDrainingFrequency(self, frequencyInHz):
        """
        **Description**

        Used to configure the draining speed to clear up the queued requests when the connection is back.
        Should be called before connect.

        **Syntax**

        .. code:: python

          # Configure the draining speed to be 2 requests/second
          myAWSIoTMQTTClient.configureDrainingFrequency(2)

        .. note::

          Make sure the draining speed is fast enough and faster than the publish rate. Slow draining 
          could result in inifinite draining process.

        **Parameters**

        *frequencyInHz* - The draining speed to clear the queued requests, in requests/second.

        **Returns**

        None

        """
        # mqttCore.setDrainingIntervalSecond(srcDrainingIntervalSecond)
        self._mqttCore.setDrainingIntervalSecond(1/float(frequencyInHz))

    def configureConnectDisconnectTimeout(self, timeoutSecond):
        """
        **Description**

        Used to configure the time in seconds to wait for a CONNACK or a disconnect to complete. 
        Should be called before connect.

        **Syntax**

        .. code:: python

          # Configure connect/disconnect timeout to be 10 seconds
          myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)

        **Parameters**

        *timeoutSecond* - Time in seconds to wait for a CONNACK or a disconnect to complete.

        **Returns**

        None

        """
        # mqttCore.setConnectDisconnectTimeoutSecond(srcConnectDisconnectTimeout)
        self._mqttCore.setConnectDisconnectTimeoutSecond(timeoutSecond)

    def configureMQTTOperationTimeout(self, timeoutSecond):
        """
        **Description**

        Used to configure the timeout in seconds for MQTT QoS 1 publish, subscribe and unsubscribe. 
        Should be called before connect.

        **Syntax**

        .. code:: python

          # Configure MQTT operation timeout to be 5 seconds
          myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)

        **Parameters**

        *timeoutSecond* - Time in seconds to wait for a PUBACK/SUBACK/UNSUBACK.

        **Returns**

        None

        """
        # mqttCore.setMQTTOperationTimeoutSecond(srcMQTTOperationTimeout)
        self._mqttCore.setMQTTOperationTimeoutSecond(timeoutSecond)

    # MQTT functionality APIs
    def connect(self, keepAliveIntervalSecond=30):
        """
        **Description**

        Connect to AWS IoT, with user-specific keeoalive interval configuration.

        **Syntax**

        .. code:: python

          # Connect to AWS IoT with default keepalive set to 30 seconds
          myAWSIoTMQTTClient.connect()
          # Connect to AWS IoT with keepalive interval set to 55 seconds
          myAWSIoTMQTTClient.connect(55)

        **Parameters**

        *keepAliveIntervalSecond* - Time in seconds for interval of sending MQTT ping request. 
        Default set to 30 seconds.

        **Returns**

        True if the connect attempt succeeded. False if failed.

        """
        # mqttCore.connect(keepAliveInterval=30)
        return self._mqttCore.connect(keepAliveIntervalSecond)

    def disconnect(self):
        """
        **Description**

        Disconnect from AWS IoT.

        **Syntax**

        .. code:: python

          myAWSIoTMQTTClient.disconnect()

        **Parameters**

        None

        **Returns**

        True if the disconnect attempt succeeded. False if failed.

        """
        # mqttCore.disconnect()
        return self._mqttCore.disconnect()

    def publish(self, topic, payload, QoS):
        """
        **Description**

        Publish a new message to the desired topic with QoS.

        **Syntax**

        .. code:: python

          # Publish a QoS0 message "myPayload" to topic "myToppic"
          myAWSIoTMQTTClient.publish("myTopic", "myPayload", 0)
          # Publish a QoS1 message "myPayload2" to topic "myTopic/sub"
          myAWSIoTMQTTClient.publish("myTopic/sub", "myPayload", 1)

        **Parameters**

        *topic* - Topic name to publish to.

        *payload* - Payload to publish.

        *QoS* - Quality of Service. Could be 0 or 1.

        **Returns**

        True if the publish request has been sent to paho. False if the request did not reach paho.

        """
        # mqttCore.publish(topic, payload, qos, retain)
        return self._mqttCore.publish(topic, payload, QoS, False)  # Disable retain for publish by now

    def subscribe(self, topic, QoS, callback):
        """
        **Description**

        Subscribe to the desired topic and register a callback.

        **Syntax**

        .. code:: python

          # Subscribe to "myTopic" with QoS0 and register a callback
          myAWSIoTMQTTClient.subscribe("myTopic", 0, customCallback)
          # Subscribe to "myTopic/#" with QoS1 and register a callback
          myAWSIoTMQTTClient.subscribe("myTopic/#", 1, customCallback)

        **Parameters**

        *topic* - Topic name or filter to subscribe to.

        *QoS* - Quality of Service. Could be 0 or 1.

        *callback* - Function to be called when a new message for the subscribed topic 
        comes in. Should be in form :code:`customCallback(client, userdata, message)`, where
        :code:`message` contains :code:`topic` and :code:`payload`.

        **Returns**

        True if the subscribe attempt succeeded. False if failed.

        """
        # mqttCore.subscribe(topic, qos, callback)
        return self._mqttCore.subscribe(topic, QoS, callback)

    def unsubscribe(self, topic):
        """
        **Description**

        Unsubscribed to the desired topic.

        **Syntax**

        .. code:: python

          myAWSIoTMQTTClient.unsubscribe("myTopic")

        **Parameters**

        *topic* - Topic name or filter to unsubscribe to.

        **Returns**

        True if the unsubscribe attempt succeeded. False if failed.

        """
        # mqttCore.unsubscribe(topic)
        return self._mqttCore.unsubscribe(topic)


class AWSIoTMQTTShadowClient:

    def __init__(self, clientID, protocolType=MQTTv3_1_1, useWebsocket=False, cleanSession=True):
        """

        The client class that manages device shadow and accesses its functionality in AWS IoT over MQTT v3.1/3.1.1.

        It is built on top of the AWS IoT MQTT Client and exposes devive shadow related operations. 
        It shares the same connection types, synchronous MQTT operations and partial on-top features 
        with the AWS IoT MQTT Client:

        - Auto reconnect/resubscribe

        Same as AWS IoT MQTT Client.

        - Progressive reconnect backoff

        Same as AWS IoT MQTT Client.

        - Offline publish requests queueing with draining

        Disabled by default. Queueing is not allowed for time-sensitive shadow requests/messages.

        **Syntax**

        .. code:: python

          import AWSIoTPythonSDK.MQTTLib as AWSIoTPyMQTT

          # Create an AWS IoT MQTT Shadow Client using TLSv1.2 Mutual Authentication
          myAWSIoTMQTTShadowClient = AWSIoTPyMQTT.AWSIoTMQTTShadowClient("testIoTPySDK")
          # Create an AWS IoT MQTT Shadow Client using Websocket SigV4
          myAWSIoTMQTTShadowClient = AWSIoTPyMQTT.AWSIoTMQTTShadowClient("testIoTPySDK",  useWebsocket=True)

        **Parameters**

        *clientID* - String that denotes the client identifier used to connect to AWS IoT.
        If empty string were provided, client id for this connection will be randomly generated 
        n server side.

        *protocolType* - MQTT version in use for this connection. Could be :code:`AWSIoTPythonSDK.MQTTLib.MQTTv3_1` or :code:`AWSIoTPythonSDK.MQTTLib.MQTTv3_1_1`

        *useWebsocket* - Boolean that denotes enabling MQTT over Websocket SigV4 or not.

        **Returns**

        AWSIoTPythonSDK.MQTTLib.AWSIoTMQTTShadowClient object

        """
        # AWSIOTMQTTClient instance
        self._AWSIoTMQTTClient = AWSIoTMQTTClient(clientID, protocolType, useWebsocket, cleanSession)
        # Configure it to disable offline Publish Queueing
        self._AWSIoTMQTTClient.configureOfflinePublishQueueing(0)  # Disable queueing, no queueing for time-sentive shadow messages
        self._AWSIoTMQTTClient.configureDrainingFrequency(10)
        # Now retrieve the configured mqttCore and init a shadowManager instance
        self._shadowManager = shadowManager.shadowManager(self._AWSIoTMQTTClient._mqttCore)

    # Configuration APIs
    def configureLastWill(self, topic, payload, QoS):
        """
        **Description**

        Used to configure the last will topic, payload and QoS of the client. Should be called before connect.

        **Syntax**

        .. code:: python
          myAWSIoTMQTTClient.configureLastWill("last/Will/Topic", "lastWillPayload", 0)

        **Parameters**

        *topic* - Topic name that last will publishes to.

        *payload* - Payload to publish for last will.

        *QoS* - Quality of Service. Could be 0 or 1.

        **Returns**

        None

        """
        # AWSIoTMQTTClient.configureLastWill(srcTopic, srcPayload, srcQos)
        self._AWSIoTMQTTClient.configureLastWill(topic, payload, QoS)

    def clearLastWill(self):
        """
        **Description**

        Used to clear the last will configuration that is previously set through configureLastWill.

        **Syntax**

        ..code:: python
          myAWSIoTShadowMQTTClient.clearLastWill()

        **Parameter**

        None

        **Returns**

        None
        
        """
        # AWSIoTMQTTClient.clearLastWill()
        self._AWSIoTMQTTClient.clearLastWill()

    def configureEndpoint(self, hostName, portNumber):
        """
        **Description**

        Used to configure the host name and port number the underneath AWS IoT MQTT Client tries to connect to. Should be called
        before connect.

        **Syntax**

        .. code:: python

          myAWSIoTMQTTShadowClient.configureEndpoint("random.iot.region.amazonaws.com", 8883)

        **Parameters**

        *hostName* - String that denotes the host name of the user-specific AWS IoT endpoint.

        *portNumber* - Integer that denotes the port number to connect to. Could be :code:`8883` for
        TLSv1.2 Mutual Authentication or :code:`443` for Websocket SigV4.

        **Returns**

        None

        """
        # AWSIoTMQTTClient.configureEndpoint
        self._AWSIoTMQTTClient.configureEndpoint(hostName, portNumber)

    def configureIAMCredentials(self, AWSAccessKeyID, AWSSecretAccessKey, AWSSTSToken=""):
        """
        **Description**

        Used to configure/update the custom IAM credentials for the underneath AWS IoT MQTT Client 
        for Websocket SigV4 connection to AWS IoT. Should be called before connect.

        **Syntax**

        .. code:: python

          myAWSIoTMQTTShadowClient.configureIAMCredentials(obtainedAccessKeyID, obtainedSecretAccessKey, obtainedSessionToken)

        .. note::

          Hard-coding credentials into custom script is NOT recommended. Please use AWS Cognito identity service
          or other credential provider.

        **Parameters**

        *AWSAccessKeyID* - AWS Access Key Id from user-specific IAM credentials.

        *AWSSecretAccessKey* - AWS Secret Access Key from user-specific IAM credentials.

        *AWSSessionToken* - AWS Session Token for temporary authentication from STS.

        **Returns**

        None

        """
        # AWSIoTMQTTClient.configureIAMCredentials
        self._AWSIoTMQTTClient.configureIAMCredentials(AWSAccessKeyID, AWSSecretAccessKey, AWSSTSToken)

    def configureCredentials(self, CAFilePath, KeyPath="", CertificatePath=""):  # Should be good for MutualAuth and Websocket
        """
        **Description**

        **Syntax**

        **Parameters**

        **Returns**

        """
        # AWSIoTMQTTClient.configureCredentials
        self._AWSIoTMQTTClient.configureCredentials(CAFilePath, KeyPath, CertificatePath)

    def configureAutoReconnectBackoffTime(self, baseReconnectQuietTimeSecond, maxReconnectQuietTimeSecond, stableConnectionTimeSecond):
        """
        **Description**

        Used to configure the rootCA, private key and certificate files. Should be called before connect.

        **Syntax**

        .. code:: python

          myAWSIoTMQTTShadowClient.configureCredentials("PATH/TO/ROOT_CA", "PATH/TO/PRIVATE_KEY", "PATH/TO/CERTIFICATE")

        **Parameters**

        *CAFilePath* - Path to read the root CA file. Required for all connection types.

        *KeyPath* - Path to read the private key. Required for X.509 certificate based connection.

        *CertificatePath* - Path to read the certificate. Required for X.509 certificate based connection.

        **Returns**

        None

        """
        # AWSIoTMQTTClient.configureBackoffTime
        self._AWSIoTMQTTClient.configureAutoReconnectBackoffTime(baseReconnectQuietTimeSecond, maxReconnectQuietTimeSecond, stableConnectionTimeSecond)

    def configureConnectDisconnectTimeout(self, timeoutSecond):
        """
        **Description**

        Used to configure the time in seconds to wait for a CONNACK or a disconnect to complete. 
        Should be called before connect.

        **Syntax**

        .. code:: python

          # Configure connect/disconnect timeout to be 10 seconds
          myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10)

        **Parameters**

        *timeoutSecond* - Time in seconds to wait for a CONNACK or a disconnect to complete.

        **Returns**

        None

        """
        # AWSIoTMQTTClient.configureConnectDisconnectTimeout
        self._AWSIoTMQTTClient.configureConnectDisconnectTimeout(timeoutSecond)

    def configureMQTTOperationTimeout(self, timeoutSecond):
        """
        **Description**

        Used to configure the timeout in seconds for MQTT QoS 1 publish, subscribe and unsubscribe. 
        Should be called before connect.

        **Syntax**

        .. code:: python

          # Configure MQTT operation timeout to be 5 seconds
          myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5)

        **Parameters**

        *timeoutSecond* - Time in seconds to wait for a PUBACK/SUBACK/UNSUBACK.

        **Returns**

        None

        """
        # AWSIoTMQTTClient.configureMQTTOperationTimeout
        self._AWSIoTMQTTClient.configureMQTTOperationTimeout(timeoutSecond)

    # Start the MQTT connection
    def connect(self, keepAliveIntervalSecond=30):
        """
        **Description**

        Connect to AWS IoT, with user-specific keeoalive interval configuration.

        **Syntax**

        .. code:: python

          # Connect to AWS IoT with default keepalive set to 30 seconds
          myAWSIoTMQTTShadowClient.connect()
          # Connect to AWS IoT with keepalive interval set to 55 seconds
          myAWSIoTMQTTShadowClient.connect(55)

        **Parameters**

        *keepAliveIntervalSecond* - Time in seconds for interval of sending MQTT ping request. 
        Default set to 30 seconds.

        **Returns**

        True if the connect attempt succeeded. False if failed.

        """
        return self._AWSIoTMQTTClient.connect(keepAliveIntervalSecond)

    # End the MQTT connection
    def disconnect(self):
        """
        **Description**

        Disconnect from AWS IoT.

        **Syntax**

        .. code:: python

          myAWSIoTMQTTShadowClient.disconnect()

        **Parameters**

        None

        **Returns**

        True if the disconnect attempt succeeded. False if failed.

        """
        return self._AWSIoTMQTTClient.disconnect()

    # Shadow management API
    def createShadowHandlerWithName(self, shadowName, isPersistentSubscribe):
        """
        **Description**

        Create a device shadow handler using the specified shadow name and isPersistentSubscribe.

        **Syntax**

        .. code:: python

          # Create a device shadow handler for shadow named "Bot1", using persistent subscription
          Bot1Shadow = myAWSIoTMQTTShadowClient.createShadowHandlerWithName("Bot1", True)
          # Create a device shadow handler for shadow named "Bot2", using non-persistent subscription
          Bot2Shadow = myAWSIoTMQTTShadowClient.createShadowHandlerWithName("Bot2", False)

        **Parameters**

        *shadowName* - Name of the device shadow.

        *isPersistentSubscribe* - Whether to unsubscribe from shadow response (accepted/rejected) topics 
        when there is a response. Will subscribe at the first time the shadow request is made and will 
        not unsubscribe if isPersistentSubscribe is set.

        **Returns**

        AWSIoTPythonSDK.core.shadow.deviceShadow.deviceShadow object, which exposes the device shadow interface.

        """        
        # Create and return a deviceShadow instance
        return deviceShadow.deviceShadow(shadowName, isPersistentSubscribe, self._shadowManager)
        # Shadow APIs are accessible in deviceShadow instance":
        ###
        # deviceShadow.shadowGet
        # deviceShadow.shadowUpdate
        # deviceShadow.shadowDelete
        # deviceShadow.shadowRegisterDelta
        # deviceShadow.shadowUnregisterDelta

    # MQTT connection management API
    def getMQTTConnection(self):
        """
        **Description**

        Retrieve the AWS IoT MQTT Client used underneath for shadow operations, making it possible to perform 
        plain MQTT operations along with shadow operations using the same single connection.

        **Syntax**

        .. code:: python

          # Retrieve the AWS IoT MQTT Client used in the AWS IoT MQTT Shadow Client
          thisAWSIoTMQTTClient = myAWSIoTMQTTShadowClient.getMQTTConnection()
          # Perform plain MQTT operations using the same connection
          thisAWSIoTMQTTClient.publish("Topic", "Payload", 1)
          ...

        **Parameters**

        None

        **Returns**

        AWSIoTPythonSDK.MQTTLib.AWSIoTMQTTClient object

        """        
        # Return the internal AWSIoTMQTTClient instance
        return self._AWSIoTMQTTClient
