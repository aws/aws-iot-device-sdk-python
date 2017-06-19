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

For MQTT over TLS (port 8883), a valid certificate and a private key are
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

-  Python 2.7+ or Python 3.3+
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

Credentials
___________

The SDK supports two types of credentials that correspond to the two connection 
types:

-  X.509 certificate

   For the certificate-based mutual authentication connection
   type.
   Download the `AWS IoT root
   CA <https://www.symantec.com/content/en/us/enterprise/verisign/roots/VeriSign-Class%203-Public-Primary-Certification-Authority-G5.pem>`__.
   Use the AWS IoT console to create and download the certificate and private key. You must specify the location of these files 
   when you initialize the client.

-  IAM credentials

   For the Websocket with Signature Version 4 authentication type. You will need IAM credentials: an access key ID, a secret access
   key, and an optional session token. You must  also
   download the `AWS IoT root
   CA <https://www.symantec.com/content/en/us/enterprise/verisign/roots/VeriSign-Class%203-Public-Primary-Certification-Authority-G5.pem>`__.
   You can specify the IAM credentails by:

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

.. _Key_Features:

Key Features
~~~~~~~~~~~~

Progressive Reconnect Backoff
_____________________________

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

Offline Publish Requests Queueing with Draining
_______________________________________________

If the client is temporarily offline and disconnected due to 
network failure, publish requests will be added to an internal
queue until the number of queued-up requests reaches the size limit
of the queue. This functionality is for plain MQTT operations. Shadow
client contains time-sensitive data and is therefore not supported.

The following API is provided for configuration:

.. code-block:: python

    AWSIoTPythonSDK.MQTTLib.AWSIoTMQTTClient.configureOfflinePublishQueueing(queueSize, dropBehavior)

After the queue is full, offline publish requests will be discarded or
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
in the offline publish queue will be resent at the configured draining
rate:

.. code-block:: python

    AWSIoTPythonSDK.MQTTLib.AWSIoTMQTTClient.configureDrainingFrequency(frequencyInHz)

If no ``configOfflinePublishQueue`` or ``configureDrainingFrequency`` is
called, the following default configuration for offline publish queueing
and draining will be performed on the initialization:

.. code-block:: python

    offlinePublishQueueSize = 20
    dropBehavior = DROP_NEWEST
    drainingFrequency = 2Hz

Before the draining process is complete, any new publish request
within this time period will be added to the queue. Therefore, the draining rate
should be higher than the normal publish rate to avoid an endless
draining process after reconnect.

The disconnect event is detected based on PINGRESP MQTT
packet loss. Offline publish queueing will not be triggered until the
disconnect event is detected. Configuring a shorter keep-alive
interval allows the client to detect disconnects more quickly. Any QoS0
publish requests issued after the network failure and before the
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


Then, start the basicShadowUpdater:

.. code-block:: python

    # Certificate-based mutual authentication
    python basicShadowUpdater.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath>
    # MQTT over WebSocket
    python basicShadowUpdater.py -e <endpoint> -r <rootCAFilePath> -w


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

Now use the `AWS IoT console <https://console.aws.amazon.com/iot/>`__ or other MQTT
client to update the shadow desired state only. You should be able to see the reported state is updated to match
the changes you just made in desired state.

Source
******

The example is available in ``samples/ThingShadowEcho/``.

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
