New Version Available	
=============================
A new AWS IoT Device SDK is [now available](https://github.com/awslabs/aws-iot-device-sdk-python-v2). It is a complete rework, built to improve reliability, performance, and security. We invite your feedback!	

This SDK will no longer receive feature updates, but will receive security updates.	

AWS IoT Device SDK for Python
=============================

The AWS IoT Device SDK for Python allows developers to write Python
script to use their devices to access the AWS IoT platform through `MQTT or
MQTT over the  WebSocket
protocol <http://docs.aws.amazon.com/iot/latest/developerguide/protocols.html>`__.
By connecting their devices to AWS IoT, users can securely work with
the message broker, rules, and the device shadow (sometimes referred to as a thing shadow) provided by AWS IoT and
with other AWS services like AWS Lambda, Amazon Kinesis, Amazon S3, and more.

-  Overview_
-  Installation_
-  `Use the SDK`_
-  `Key Features`_
-  Examples_
-  `API Documentation`_
-  License_
-  Support_

--------------

.. _Overview:

Overview
~~~~~~~~

This document provides instructions for installing and configuring
the AWS IoT Device SDK for Python. It includes examples demonstrating the
use of the SDK APIs.

MQTT Connections
________________

The SDK is built on top of a modified `Paho MQTT Python client
library <https://eclipse.org/paho/clients/python/>`__. Developers can choose from two
types of connections to connect to AWS
IoT:

-  MQTT (over TLS 1.2) with X.509 certificate-based mutual
   authentication.
-  MQTT over the WebSocket protocol with AWS Signature Version 4 authentication.
-  MQTT (over TLS 1.2) with X.509 certificate-based mutual authentication with TLS ALPN extension.

For MQTT over TLS (port 8883 and port 443), a valid certificate and a private key are
required for authentication. For MQTT over the WebSocket protocol (port 443),
a valid AWS Identity and Access Management (IAM) access key ID and secret access key pair are required for
authentication.

Device Shadow
_____________

A device shadow, or thing shadow, is a JSON document that is used to
store and retrieve current state information for a thing (device, app,
and so on). A shadow can be created and maintained for each thing or device so that its state can be get and set
regardless of whether the thing or device is connected to the Internet. The
SDK implements the protocol for applications to retrieve, update, and
delete shadow documents. The SDK allows operations on shadow documents
of single or multiple shadow instances in one MQTT connection. The SDK
also allows the use of the same connection for shadow operations and non-shadow, simple MQTT operations.

.. _Installation:

Installation
~~~~~~~~~~~~

Minimum Requirements
____________________

-  Python 2.7+ or Python 3.3+ for X.509 certificate-based mutual authentication via port 8883
   and MQTT over WebSocket protocol with AWS Signature Version 4 authentication
-  Python 2.7.10+ or Python 3.5+ for X.509 certificate-based mutual authentication via port 443
-  OpenSSL version 1.0.1+ (TLS version 1.2) compiled with the Python executable for
   X.509 certificate-based mutual authentication

   To check your version of OpenSSL, use the following command in a Python interpreter:

   .. code-block:: python

       >>> import ssl
       >>> ssl.OPENSSL_VERSION

Install from pip
________________


.. code-block:: sh

    pip install AWSIoTPythonSDK

Build from source
_________________


.. code-block:: sh

    git clone https://github.com/aws/aws-iot-device-sdk-python.git
    cd aws-iot-device-sdk-python
    python setup.py install

Download the zip file
_____________________


The SDK zip file is available `here <https://s3.amazonaws.com/aws-iot-device-sdk-python/aws-iot-device-sdk-python-latest.zip>`__. Unzip the package and install the SDK like this:

.. code-block:: python

    python setup.py install

.. _Use_the_SDK:

Use the SDK
~~~~~~~~~~~

Collection of Metrics
_____________________

Beginning with Release v1.3.0 of the SDK, AWS collects usage metrics indicating which language and version of the SDK
is being used. This feature is enabled by default and allows us to prioritize our resources towards addressing issues
faster in SDKs that see the most and is an important data point. However, we do understand that not all customers would
want to report this data. In that case, the sending of usage metrics can be easily disabled by the user using the
corresponding API:

.. code-block:: python

    # AWS IoT MQTT Client
    AWSIoTPythonSDK.MQTTLib.AWSIoTMQTTClient.enableMetricsCollection()
    AWSIoTPythonSDK.MQTTLib.AWSIoTMQTTClient.disableMetricsCollection()
    # AWS IoT MQTT Shadow Client
    AWSIoTPythonSDK.MQTTLib.AWSIoTMQTTShadowClient.enableMetricsCollection()
    AWSIoTPythonSDK.MQTTLib.AWSIoTMQTTShadowClient.disableMetricsCollection()

Credentials
___________

The SDK supports two types of credentials that correspond to the two connection 
types:

-  X.509 certificate

   For the certificate-based mutual authentication connection
   type.
   Download the `AWS IoT root
   CA <https://docs.aws.amazon.com/iot/latest/developerguide/managing-device-certs.html#server-authentication>`__.
   Use the AWS IoT console to create and download the certificate and private key. You must specify the location of these files 
   when you initialize the client.

-  IAM credentials

   For the Websocket with Signature Version 4 authentication type. You will need IAM credentials: an access key ID, a secret access
   key, and an optional session token. You must  also
   download the `AWS IoT root
   CA <https://docs.aws.amazon.com/iot/latest/developerguide/managing-device-certs.html#server-authentication>`__.
   You can specify the IAM credentials by:

   -  Passing method parameters

      The SDK will first call the following method to check if there is any input for a custom IAM
      credentials configuration:

      .. code-block:: python

          # AWS IoT MQTT Client
          AWSIoTPythonSDK.MQTTLib.AWSIoTMQTTClient.configureIAMCredentials(obtainedAccessKeyID, obtainedSecretAccessKey, obtainedSessionToken)        
          # AWS IoT MQTT Shadow Client
          AWSIoTPythonSDK.MQTTLib.AWSIoTMQTTShadowClient.configureIAMCredentials(obtainedAccessKeyID, obtainedSecretAccessKey, obtainedSessionToken)

      Note: We do not recommend hard-coding credentials in a custom script. You can use `Amazon Cognito Identity
      <https://aws.amazon.com/cognito/>`__ or another credential
      provider.

   -  Exporting environment variables

      If there is no custom configuration through method calls, the SDK
      will then check these environment variables for credentials:

      ``AWS_ACCESS_KEY_ID``

      The access key for your AWS account.

      ``AWS_SECRET_ACCESS_KEY``

      The secret key for your AWS account.

      ``AWS_SESSION_TOKEN``
      
      The session key for your AWS account. This is required only when
      you are using temporary credentials. For more information, see
      `here <http://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html>`__.

      You can set your IAM credentials as environment variables by
      using the preconfigured names. For Unix systems, you can do the
      following:

      .. code-block:: sh

          export AWS_ACCESS_KEY_ID=<your aws access key id string>
          export AWS_SECRET_ACCESS_KEY=<your aws secret access key string>
          export AWS_SESSION_TOKEN=<your aws session token string>

      For Windows, open ``Control Panel`` and choose ``System``. In
      ``Advanced system settings`` choose ``Environment Variables`` and
      then configure the required environment variables.

   -  Configuring shared credentials file

      If there are no such environment variables specified, the SDK
      will check the **default** section for a shared
      credentials file (in Unix, ``~/.aws/credentials`` and in Windows, ``%UserProfile%\.aws\credentials``) as follows:

      .. code-block:: sh

          [default]
          aws_access_key_id=foo
          aws_secret_access_key=bar
          aws_session_token=baz

      You can use the AWS CLI to configure the shared credentials file <http://aws.amazon.com/cli/>`__:

      .. code-block:: sh

          aws configure

AWSIoTMQTTClient
________________

This is the client class used for plain MQTT communication with AWS IoT.
You can initialize and configure the client like this:

.. code-block:: python

    # Import SDK packages
    from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

    # For certificate based connection
    myMQTTClient = AWSIoTMQTTClient("myClientID")
    # For Websocket connection
    # myMQTTClient = AWSIoTMQTTClient("myClientID", useWebsocket=True)
    # Configurations
    # For TLS mutual authentication
    myMQTTClient.configureEndpoint("YOUR.ENDPOINT", 8883)
    # For Websocket
    # myMQTTClient.configureEndpoint("YOUR.ENDPOINT", 443)
    # For TLS mutual authentication with TLS ALPN extension
    # myMQTTClient.configureEndpoint("YOUR.ENDPOINT", 443)
    myMQTTClient.configureCredentials("YOUR/ROOT/CA/PATH", "PRIVATE/KEY/PATH", "CERTIFICATE/PATH")
    # For Websocket, we only need to configure the root CA
    # myMQTTClient.configureCredentials("YOUR/ROOT/CA/PATH")
    myMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
    myMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
    myMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
    myMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec
    ...

For basic MQTT operations, your script will look like this:

.. code-block:: python

    ...
    myMQTTClient.connect()
    myMQTTClient.publish("myTopic", "myPayload", 0)
    myMQTTClient.subscribe("myTopic", 1, customCallback)
    myMQTTClient.unsubscribe("myTopic")
    myMQTTClient.disconnect()
    ...

AWSIoTShadowClient
__________________

This is the client class used for device shadow operations with AWS IoT.
You can initialize and configure the client like this:

.. code-block:: python

    from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient

    # For certificate based connection
    myShadowClient = AWSIoTMQTTShadowClient("myClientID")
    # For Websocket connection
    # myMQTTClient = AWSIoTMQTTClient("myClientID", useWebsocket=True)
    # Configurations
    # For TLS mutual authentication
    myShadowClient.configureEndpoint("YOUR.ENDPOINT", 8883)
    # For Websocket
    # myShadowClient.configureEndpoint("YOUR.ENDPOINT", 443)
    # For TLS mutual authentication with TLS ALPN extension
    # myShadowClient.configureEndpoint("YOUR.ENDPOINT", 443)
    myShadowClient.configureCredentials("YOUR/ROOT/CA/PATH", "PRIVATE/KEY/PATH", "CERTIFICATE/PATH")
    # For Websocket, we only need to configure the root CA
    # myShadowClient.configureCredentials("YOUR/ROOT/CA/PATH")
    myShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
    myShadowClient.configureMQTTOperationTimeout(5)  # 5 sec
    ...

For shadow operations, your script will look like this:

.. code-block:: python

    ...
    myShadowClient.connect()
    # Create a device shadow instance using persistent subscription
    myDeviceShadow = myShadowClient.createShadowHandlerWithName("Bot", True)
    # Shadow operations
    myDeviceShadow.shadowGet(customCallback, 5)
    myDeviceShadow.shadowUpdate(myJSONPayload, customCallback, 5)
    myDeviceShadow.shadowDelete(customCallback, 5)
    myDeviceShadow.shadowRegisterDeltaCallback(customCallback)
    myDeviceShadow.shadowUnregisterDeltaCallback()
    ...

You can also retrieve the MQTTClient(MQTT connection) to perform plain
MQTT operations along with shadow operations:

.. code-block:: python

    myMQTTClient = myShadowClient.getMQTTConnection()
    myMQTTClient.publish("plainMQTTTopic", "Payload", 1)

AWSIoTMQTTThingJobsClient
__________________

This is the client class used for jobs operations with AWS IoT. See docs here:
https://docs.aws.amazon.com/iot/latest/developerguide/iot-jobs.html
You can initialize and configure the client like this:

.. code-block:: python

    from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTThingJobsClient

    # For certificate based connection
    myJobsClient = AWSIoTMQTTThingJobsClient("myClientID", "myThingName")
    # For Websocket connection
    # myJobsClient = AWSIoTMQTTThingJobsClient("myClientID", "myThingName", useWebsocket=True)
    # Configurations
    # For TLS mutual authentication
    myJobsClient.configureEndpoint("YOUR.ENDPOINT", 8883)
    # For Websocket
    # myJobsClient.configureEndpoint("YOUR.ENDPOINT", 443)
    myJobsClient.configureCredentials("YOUR/ROOT/CA/PATH", "PRIVATE/KEY/PATH", "CERTIFICATE/PATH")
    # For Websocket, we only need to configure the root CA
    # myJobsClient.configureCredentials("YOUR/ROOT/CA/PATH")
    myJobsClient.configureConnectDisconnectTimeout(10)  # 10 sec
    myJobsClient.configureMQTTOperationTimeout(5)  # 5 sec
    ...

For job operations, your script will look like this:

.. code-block:: python

    ...
    myJobsClient.connect()
    # Create a subsciption for $notify-next topic
    myJobsClient.createJobSubscription(notifyNextCallback, jobExecutionTopicType.JOB_NOTIFY_NEXT_TOPIC)
    # Create a subscription for update-job-execution accepted response topic
    myJobsClient.createJobSubscription(updateSuccessfulCallback, jobExecutionTopicType.JOB_UPDATE_TOPIC, jobExecutionTopicReplyType.JOB_ACCEPTED_REPLY_TYPE, '+')
    # Send a message to start the next pending job (if any)
    myJobsClient.sendJobsStartNext(statusDetailsDict)
    # Send a message to update a successfully completed job
    myJobsClient.sendJobsUpdate(jobId, jobExecutionStatus.JOB_EXECUTION_SUCCEEDED, statusDetailsDict)
    ...

You can also retrieve the MQTTClient(MQTT connection) to perform plain
MQTT operations along with shadow operations:

.. code-block:: python

    myMQTTClient = myJobsClient.getMQTTConnection()
    myMQTTClient.publish("plainMQTTTopic", "Payload", 1)

DiscoveryInfoProvider
_____________________

This is the client class for device discovery process with AWS IoT Greengrass.
You can initialize and configure the client like this:

.. code-block:: python

    from AWSIoTPythonSDK.core.greengrass.discovery.providers import DiscoveryInfoProvider

    discoveryInfoProvider = DiscoveryInfoProvider()
    discoveryInfoProvider.configureEndpoint("YOUR.IOT.ENDPOINT")
    discoveryInfoProvider.configureCredentials("YOUR/ROOT/CA/PATH", "CERTIFICATE/PATH", "PRIVATE/KEY/PATH")
    discoveryInfoProvider.configureTimeout(10)  # 10 sec

To perform the discovery process for a Greengrass Aware Device (GGAD) that belongs to a deployed group, your script
should look like this:

.. code-block:: python

    discoveryInfo = discoveryInfoProvider.discover("myGGADThingName")
    # I know nothing about the group/core I want to connect to. I want to iterate through all cores and find out.
    coreList = discoveryInfo.getAllCores()
    groupIdCAList = discoveryInfo.getAllCas()  # list([(groupId, ca), ...])
    # I know nothing about the group/core I want to connect to. I want to iterate through all groups and find out.
    groupList = discoveryInfo.getAllGroups()
    # I know exactly which group, which core and which connectivity info I need to connect.
    connectivityInfo = discoveryInfo.toObjectAtGroupLevel()["YOUR_GROUP_ID"]
                                    .getCoreConnectivityInfo("YOUR_CORE_THING_ARN")
                                    .getConnectivityInfo("YOUR_CONNECTIVITY_ID")
    # Connecting logic follows...
    ...

For more information about discovery information access at group/core/connectivity info set level, please refer to the
API documentation for ``AWSIoTPythonSDK.core.greengrass.discovery.models``,
`Greengrass Discovery documentation <http://docs.aws.amazon.com/greengrass/latest/developerguide/gg-discover-api.html>`__
or `Greengrass overall documentation <http://docs.aws.amazon.com/greengrass/latest/developerguide/what-is-gg.html>`__.


Synchronous APIs and Asynchronous APIs
______________________________________

Beginning with Release v1.2.0, SDK provides asynchronous APIs and enforces synchronous API behaviors for MQTT operations,
which includes:
- connect/connectAsync
- disconnect/disconnectAsync
- publish/publishAsync
- subscribe/subscribeAsync
- unsubscribe/unsubscribeAsync

- Asynchronous APIs
Asynchronous APIs translate the invocation into MQTT packet and forward it to the underneath connection to be sent out.
They return immediately once packets are out for delivery, regardless of whether the corresponding ACKs, if any, have
been received. Users can specify their own callbacks for ACK/message (server side PUBLISH) processing for each
individual request. These callbacks will be sequentially dispatched and invoked upon the arrival of ACK/message (server
side PUBLISH) packets.

- Synchronous APIs
Synchronous API behaviors are enforced by registering blocking ACK callbacks on top of the asynchronous APIs.
Synchronous APIs wait on their corresponding ACK packets, if there is any, before the invocation returns. For example,
a synchronous QoS1 publish call will wait until it gets its PUBACK back. A synchronous subscribe call will wait until
it gets its SUBACK back. Users can configure operation time out for synchronous APIs to stop the waiting.

Since callbacks are sequentially dispatched and invoked, calling synchronous APIs within callbacks will deadlock the
user application. If users are inclined to utilize the asynchronous mode and perform MQTT operations
within callbacks, asynchronous APIs should be used. For more details, please check out the provided samples at
``samples/basicPubSub/basicPubSub_APICallInCallback.py``

.. _Key_Features:

Key Features
~~~~~~~~~~~~

Progressive Reconnect Back Off
______________________________

When a non-client-side disconnect occurs, the SDK will reconnect automatically. The following APIs are provided for configuration:

.. code-block:: python

    # AWS IoT MQTT Client
    AWSIoTPythonSDK.MQTTLib.AWSIoTMQTTClient.configureAutoReconnectBackoffTime(baseReconnectQuietTimeSecond, maxReconnectQuietTimeSecond, stableConnectionTimeSecond)
    # AWS IoT MQTT Shadow Client
    AWSIoTPythonSDK.MQTTLib.AWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(baseReconnectQuietTimeSecond, maxReconnectQuietTimeSecond, stableConnectionTimeSecond)

The auto-reconnect occurs with a progressive backoff, which follows this
mechanism for reconnect backoff time calculation:

    t\ :sup:`current` = min(2\ :sup:`n` t\ :sup:`base`, t\ :sup:`max`)

where t\ :sup:`current` is the current reconnect backoff time, t\ :sup:`base` is the base
reconnect backoff time, t\ :sup:`max` is the maximum reconnect backoff time.

The reconnect backoff time will be doubled on disconnect and reconnect
attempt until it reaches the preconfigured maximum reconnect backoff
time. After the connection is stable for over the
``stableConnectionTime``, the reconnect backoff time will be reset to
the ``baseReconnectQuietTime``.

If no ``configureAutoReconnectBackoffTime`` is called, the following
default configuration for backoff timing will be performed on initialization:

.. code-block:: python

    baseReconnectQuietTimeSecond = 1
    maxReconnectQuietTimeSecond = 32
    stableConnectionTimeSecond = 20

Offline Requests Queueing with Draining
_______________________________________

If the client is temporarily offline and disconnected due to 
network failure, publish/subscribe/unsubscribe requests will be added to an internal
queue until the number of queued-up requests reaches the size limit
of the queue. This functionality is for plain MQTT operations. Shadow
client contains time-sensitive data and is therefore not supported.

The following API is provided for configuration:

.. code-block:: python

    AWSIoTPythonSDK.MQTTLib.AWSIoTMQTTClient.configureOfflinePublishQueueing(queueSize, dropBehavior)

After the queue is full, offline publish/subscribe/unsubscribe requests will be discarded or
replaced according to the configuration of the drop behavior:

.. code-block:: python

    # Drop the oldest request in the queue
    AWSIoTPythonSDK.MQTTLib.DROP_OLDEST = 0
    # Drop the newest request in the queue
    AWSIoTPythonSDK.MQTTLib.DROP_NEWEST = 1

Let's say we configure the size of offlinePublishQueue to 5 and we
have 7 incoming offline publish requests.

In a ``DROP_OLDEST`` configuration:

.. code-block:: python

    myClient.configureOfflinePublishQueueing(5, AWSIoTPythonSDK.MQTTLib.DROP_OLDEST);

The internal queue should be like this when the queue is just full:

.. code-block:: sh

    HEAD ['pub_req1', 'pub_req2', 'pub_req3', 'pub_req4', 'pub_req5']

When the 6th and the 7th publish requests are made offline, the internal
queue will be like this:

.. code-block:: sh

    HEAD ['pub_req3', 'pub_req4', 'pub_req5', 'pub_req6', 'pub_req7']

Because the queue is already full, the oldest requests ``pub_req1`` and
``pub_req2`` are discarded.

In a ``DROP_NEWEST`` configuration:

.. code-block:: python

    myClient.configureOfflinePublishQueueing(5, AWSIoTPythonSDK.MQTTLib.DROP_NEWEST);

The internal queue should be like this when the queue is just full:

.. code-block:: sh

    HEAD ['pub_req1', 'pub_req2', 'pub_req3', 'pub_req4', 'pub_req5']

When the 6th and the 7th publish requests are made offline, the internal
queue will be like this:

.. code-block:: sh

    HEAD ['pub_req1', 'pub_req2', 'pub_req3', 'pub_req4', 'pub_req5']

Because the queue is already full, the newest requests ``pub_req6`` and
``pub_req7`` are discarded.

When the client is back online, connected, and resubscribed to all topics
it has previously subscribed to, the draining starts. All requests
in the offline request queue will be resent at the configured draining
rate:

.. code-block:: python

    AWSIoTPythonSDK.MQTTLib.AWSIoTMQTTClient.configureDrainingFrequency(frequencyInHz)

If no ``configOfflinePublishQueue`` or ``configureDrainingFrequency`` is
called, the following default configuration for offline request queueing
and draining will be performed on the initialization:

.. code-block:: python

    offlinePublishQueueSize = 20
    dropBehavior = DROP_NEWEST
    drainingFrequency = 2Hz

Before the draining process is complete, any new publish/subscribe/unsubscribe request
within this time period will be added to the queue. Therefore, the draining rate
should be higher than the normal request rate to avoid an endless
draining process after reconnect.

The disconnect event is detected based on PINGRESP MQTT
packet loss. Offline request queueing will not be triggered until the
disconnect event is detected. Configuring a shorter keep-alive
interval allows the client to detect disconnects more quickly. Any QoS0
publish, subscribe and unsubscribe requests issued after the network failure and before the
detection of the PINGRESP loss will be lost.

Persistent/Non-Persistent Subscription
______________________________________

Device shadow operations are built on top of the publish/subscribe model
for the MQTT protocol, which provides an asynchronous request/response workflow. Shadow operations (Get, Update, Delete) are
sent as requests to AWS IoT. The registered callback will 
be executed after a response is returned. In order to receive
responses, the client must subscribe to the corresponding shadow
response topics. After the responses are received, the client might want
to unsubscribe from these response topics to avoid getting unrelated
responses for charges for other requests not issued by this client.

The SDK provides a persistent/non-persistent subscription selection on
the initialization of a device shadow. Developers can choose the type of subscription workflow they want to follow.

For a non-persistent subscription, you will need to create a device
shadow like this:

.. code-block:: python

    nonPersistentSubShadow = myShadowClient.createShadowHandlerWithName("NonPersistentSubShadow", False)

In this case, the request to subscribe to accepted/rejected topics will be
sent on each shadow operation. After a response is returned,
accepted/rejected topics will be unsubscribed to avoid getting unrelated
responses.

For a persistent subscription, you will need to create a device shadow
like this:

.. code-block:: python

    persistentSubShadow = myShadowClient.createShadowHandlerWithName("PersistentSubShadow", True)

In this case, the request to subscribe to the corresponding
accepted/rejected topics will be sent on the first shadow operation. For
example, on the first call of shadowGet API, the following topics will
be subscribed to on the first Get request:

.. code-block:: sh

    $aws/things/PersistentSubShadow/shadow/get/accepted
    $aws/things/PersistentSubShadow/shadow/get/rejected

Because it is a persistent subscription, no unsubscribe requests will be
sent when a response is returned. The SDK client is always listening on
accepted/rejected topics.

In all SDK examples, PersistentSubscription is used in consideration of its better performance.

.. _Examples:

Examples
~~~~~~~~

BasicPubSub
___________

This example demonstrates a simple MQTT publish/subscribe using AWS
IoT. It first subscribes to a topic and registers a callback to print
new messages and then publishes to the same topic in a loop.
New messages are printed upon receipt, indicating
the callback function has been called.

Instructions
************

Run the example like this:

.. code-block:: python

    # Certificate based mutual authentication
    python basicPubSub.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath>
    # MQTT over WebSocket
    python basicPubSub.py -e <endpoint> -r <rootCAFilePath> -w
    # Customize client id and topic
    python basicPubSub.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath> -id <clientId> -t <topic>
    # Customize the message
    python basicPubSub.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath> -id <clientId> -t <topic> -M <message>
    # Customize the port number
    python basicPubSub.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath> -p <portNumber>
    # change the run mode to subscribe or publish only (see python basicPubSub.py -h for the available options)
    python basicPubSub.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath> -m <mode>

Source
******

The example is available in ``samples/basicPubSub/``.

BasicPubSub with Amazon Cognito Session Token
_____________________________________________

This example demonstrates a simple MQTT publish/subscribe using an Amazon Cognito
Identity session token. It uses the AWS IoT Device SDK for
Python and the AWS SDK for Python (boto3). It first makes a request to
Amazon Cognito to retrieve the access ID, the access key, and the session token for temporary
authentication. It then uses these credentials to connect to AWS
IoT and communicate data/messages using MQTT over Websocket, just like
the BasicPubSub example.

Instructions
************

To run the example, you will need your **Amazon Cognito identity pool ID** and allow **unauthenticated
identities** to connect. Make sure that the policy attached to the
unauthenticated role has permissions to access the required AWS IoT
APIs. For more information about Amazon Cognito, see
`here <https://console.aws.amazon.com/cognito/>`__.

Run the example like this:

.. code-block:: python

    python basicPubSub_CognitoSTS.py -e <endpoint> -r <rootCAFilePath> -C <CognitoIdentityPoolID>
    # Customize client id and topic
    python basicPubsub_CognitoSTS.py -e <endpoint> -r <rootCAFilePath> -C <CognitoIdentityPoolID> -id <clientId> -t <topic>

Source
******

The example is available in ``samples/basicPubSub/``.

BasicPubSub Asynchronous version
________________________________

This example demonstrates a simple MQTT publish/subscribe with asynchronous APIs using AWS IoT.
It first registers general notification callbacks for CONNACK reception, disconnect reception and message arrival.
It then registers ACK callbacks for subscribe and publish requests to print out received ack packet ids.
It subscribes to a topic with no specific callback and then publishes to the same topic in a loop.
New messages are printed upon reception by the general message arrival callback, indicating
the callback function has been called.
New ack packet ids are printed upon reception of PUBACK and SUBACK through ACK callbacks registered with asynchronous
API calls, indicating that the the client received ACKs for the corresponding asynchronous API calls.

Instructions
************

Run the example like this:

.. code-block:: python

    # Certificate based mutual authentication
    python basicPubSubAsync.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath>
    # MQTT over WebSocket
    python basicPubSubAsync.py -e <endpoint> -r <rootCAFilePath> -w
    # Customize client id and topic
    python basicPubSubAsync.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath> -id <clientId> -t <topic>
    # Customize the port number
    python basicPubSubAsync.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath> -p <portNumber>

Source
******

The example is available in ``samples/basicPubSub/``.

BasicPubSub with API invocation in callback
___________

This example demonstrates the usage of asynchronous APIs within callbacks. It first connects to AWS IoT and subscribes
to 2 topics with the corresponding message callbacks registered. One message callback contains client asynchronous API
invocation that republishes the received message from <topic> to  <topic>/republish. The other message callback simply
prints out the received message. It then publishes messages to <topic> in an infinite loop. For every message received
from <topic>, it will be republished to <topic>/republish and be printed out as configured in the simple print-out
message callback.
New ack packet ids are printed upon reception of PUBACK and SUBACK through ACK callbacks registered with asynchronous
API calls, indicating that the the client received ACKs for the corresponding asynchronous API calls.

Instructions
************

Run the example like this:

.. code-block:: python

    # Certificate based mutual authentication
    python basicPubSub_APICallInCallback.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath>
    # MQTT over WebSocket
    python basicPubSub_APICallInCallback.py -e <endpoint> -r <rootCAFilePath> -w
    # Customize client id and topic
    python basicPubSub_APICallInCallback.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath> -id <clientId> -t <topic>
    # Customize the port number
    python basicPubSub_APICallInCallback.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath> -p <portNumber>

Source
******

The example is available in ``samples/basicPubSub/``.

BasicShadow
___________

This example demonstrates the use of basic shadow operations
(update/delta). It has two scripts, ``basicShadowUpdater.py`` and
``basicShadowDeltaListener.py``. The example shows how an shadow update
request triggers delta events.

``basicShadowUpdater.py`` performs a shadow update in a loop to
continuously modify the desired state of the shadow by changing the
value of the integer attribute.

``basicShadowDeltaListener.py`` subscribes to the delta topic
of the same shadow and receives delta messages when there is a
difference between the desired and reported states.

Because only the desired state is being updated by basicShadowUpdater, a
series of delta messages that correspond to the shadow update requests should be received in basicShadowDeltaListener.

Instructions
************

Run the example like this:

First, start the basicShadowDeltaListener:

.. code-block:: python

    # Certificate-based mutual authentication
    python basicShadowDeltaListener.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath>
    # MQTT over WebSocket
    python basicShadowDeltaListener.py -e <endpoint> -r <rootCAFilePath> -w
    # Customize the port number
    python basicShadowDeltaListener.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath> -p <portNumber>


Then, start the basicShadowUpdater:

.. code-block:: python

    # Certificate-based mutual authentication
    python basicShadowUpdater.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath>
    # MQTT over WebSocket
    python basicShadowUpdater.py -e <endpoint> -r <rootCAFilePath> -w
    # Customize the port number
    python basicShadowUpdater.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath> -p <portNumber>


After the basicShadowUpdater starts sending shadow update requests, you
should be able to see corresponding delta messages in the
basicShadowDeltaListener output.

Source
******

The example is available in ``samples/basicShadow/``.

ThingShadowEcho
_______________

This example demonstrates how a device communicates with AWS IoT,
syncing data into the device shadow in the cloud and receiving commands
from another app. Whenever there is a new command from the app side to
change the desired state of the device, the device receives this
request and applies the change by publishing it as the reported state. By
registering a delta callback function, users will be able to see this
incoming message and notice the syncing of the state.

Instructions
************

Run the example like this:

.. code-block:: python

    # Certificate based mutual authentication
    python ThingShadowEcho.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath>
    # MQTT over WebSocket
    python ThingShadowEcho.py -e <endpoint> -r <rootCAFilePath> -w
    # Customize client Id and thing name
    python ThingShadowEcho.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath> -id <clientId> -n <thingName>
    # Customize the port number
    python ThingShadowEcho.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath> -p <portNumber>

Now use the `AWS IoT console <https://console.aws.amazon.com/iot/>`__ or other MQTT
client to update the shadow desired state only. You should be able to see the reported state is updated to match
the changes you just made in desired state.

Source
******

The example is available in ``samples/ThingShadowEcho/``.

JobsSample
__________

This example demonstrates how a device communicates with AWS IoT while
also taking advantage of AWS IoT Jobs functionality. It shows how to
subscribe to Jobs topics in order to recieve Job documents on your
device. It also shows how to process those Jobs so that you can see in
the `AWS IoT console <https://console.aws.amazon.com/iot/>`__ which of your devices have received and processed
which Jobs. See the AWS IoT Device Management documentation `here <https://aws.amazon.com/documentation/iot-device-management/>`__
for more information on creating and deploying Jobs to your fleet of
devices to facilitate management tasks such deploying software updates
and running diagnostics.

Instructions
************

First use the `AWS IoT console <https://console.aws.amazon.com/iot/>`__ to create and deploy Jobs to your fleet of devices.

Then run the example like this:

.. code-block:: python

    # Certificate based mutual authentication
    python jobsSample.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath> -n <thingName>
    # MQTT over WebSocket
    python jobsSample.py -e <endpoint> -r <rootCAFilePath> -w -n <thingName>
    # Customize client Id and thing name
    python jobsSample.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath> -id <clientId> -n <thingName>
    # Customize the port number
    python jobsSample.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath> -n <thingName> -p <portNumber>

Source
******

The example is available in ``samples/jobs/``.

BasicDiscovery
______________

This example demonstrates how to perform a discovery process from a Greengrass Aware Device (GGAD) to obtain the required
connectivity/identity information to connect to the Greengrass Core (GGC) deployed within the same group. It uses the
discovery information provider to invoke discover call for a certain GGAD with its thing name. After it gets back a
success response, it picks up the first GGC and the first set of identity information (CA) for the first group, persists \
it locally and iterates through all connectivity info sets for this GGC to establish a MQTT connection to the designated
GGC. It then publishes messages to the topic, which, on the GGC side, is configured to route the messages back to the
same GGAD. Therefore, it receives the published messages and invokes the corresponding message callbacks.

Note that in order to get the sample up and running correctly, you need:

1. Have a successfully deployed Greengrass group.

2. Use the certificate and private key that have been deployed with the group for the GGAD to perform discovery process.

3. The subscription records for that deployed group should contain a route that routes messages from the targeted GGAD to itself via a dedicated MQTT topic.

4. The deployed GGAD thing name, the deployed GGAD certificate/private key and the dedicated MQTT topic should be used as the inputs for this sample.


Run the sample like this:

.. code-block:: python

    python basicDiscovery.py -e <endpoint> -r <IoTRootCAFilePath> -c <certFilePath> -k <privateKeyFilePath> -n <GGADThingName> -t <RoutingTopic>

If the group, GGC, GGAD and group subscription/routes are set up correctly, you should be able to see the sample running
on your GGAD, receiving messages that get published to GGC by itself.

.. _API_Documentation:

API Documentation
~~~~~~~~~~~~~~~~~

You can find the API documentation for the SDK `here <https://s3.amazonaws.com/aws-iot-device-sdk-python-docs/index.html>`__.

.. _License:

License
~~~~~~~

This SDK is distributed under the `Apache License, Version
2.0 <http://www.apache.org/licenses/LICENSE-2.0>`__, see LICENSE.txt
and NOTICE.txt for more information.

.. _Support:

Support
~~~~~~~

If you have technical questions about the AWS IoT Device SDK, use the `AWS
IoT Forum <https://forums.aws.amazon.com/forum.jspa?forumID=210>`__.
For any other questions about AWS IoT, contact `AWS
Support <https://aws.amazon.com/contact-us>`__.
