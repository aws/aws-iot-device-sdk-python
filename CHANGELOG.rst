=========
CHANGELOG
=========

1.4.9
=====
* bugfix: Fixing possible race condition with timer in deviceShadow.

1.4.8
=====
* improvement: Added support for subscription acknowledgement callbacks while offline or resubscribing
  
1.4.7
=====
* improvement: Added connection establishment control through client socket factory option

1.4.6
=====
* bugfix: Use non-deprecated ssl API to specify ALPN when doing Greengrass discovery 

1.4.5
=====
* improvement: Added validation to mTLS arguments in basicDiscovery

1.4.3
=====
* bugfix: [Issue #150](https://github.com/aws/aws-iot-device-sdk-python/issues/150)Fix for ALPN in Python 3.7

1.4.2
=====
* bugfix: Websocket handshake supports Amazon Trust Store (ats) endpoints
* bugfix: Remove default port number in samples, which prevented WebSocket mode from using 443
* bugfix: jobsSample print statements compatible with Python 3.x
* improvement: Small fixes to IoT Jobs documentation


1.4.0
=====
* bugfix:Issue `#136 <https://github.com/aws/aws-iot-device-sdk-python/issues/136>`
* bugfix:Issue:`#124 <https://github.com/aws/aws-iot-device-sdk-python/issues/124>`
* improvement:Expose the missing getpeercert() from SecuredWebsocket class
* improvement:Enforce sending host header in the outbound discovery request
* improvement:Ensure credentials non error are properly handled and communicated to application level when creating wss endpoint
* feature:Add support for ALPN, along with API docs, sample and updated README
* feature:Add support for IoT Jobs, along with API docs, sample and updated README
* feature:Add command line option to allow port number override

1.3.1
=====
* bugfix:Issue:`#67 <https://github.com/aws/aws-iot-device-sdk-python/issues/67>`__
* bugfix:Fixed a dead lock issue when client async API is called within the event callback
* bugfix:Updated README and API documentation to provide clear usage information on sync/async API and callbacks
* improvement:Added a new sample to show API usage within callbacks

1.3.0
=====
* bugfix:WebSocket handshake response timeout and error escalation
* bugfix:Prevent GG discovery from crashing if Metadata field is None
* bugfix:Fix the client object reusability issue
* bugfix:Prevent NPE due to shadow operation token not found in the pool
* improvement:Split the publish and subscribe operations in basicPubSub.py sample
* improvement:Updated default connection keep-alive interval to 600 seconds
* feature:AWSIoTMQTTClient:New API for username and password configuration
* feature:AWSIoTMQTTShadowClient:New API for username and password configuration
* feature:AWSIoTMQTTClient:New API for enabling/disabling metrics collection
* feature:AWSIoTMQTTShadowClient:New API for enabling/disabling metrics collection

1.2.0
=====
* improvement:AWSIoTMQTTClient:Improved synchronous API backend for ACK tracking
* feature:AWSIoTMQTTClient:New API for asynchronous API
* feature:AWSIoTMQTTClient:Expose general notification callbacks for online, offline and message arrival
* feature:AWSIoTMQTTShadowClient:Expose general notification callbacks for online, offline and message arrival
* feature:AWSIoTMQTTClient:Extend offline queueing to include offline subscribe/unsubscribe requests
* feature:DiscoveryInfoProvider:Support for Greengrass discovery
* bugfix:Pull request:`#50 <https://github.com/aws/aws-iot-device-sdk-python/pull/50>`__
* bugfix:Pull request:`#51 <https://github.com/aws/aws-iot-device-sdk-python/pull/51>`__
* bugfix:Issue:`#52 <https://github.com/aws/aws-iot-device-sdk-python/issues/52>`__

1.1.2
=====
* bugfix:Issue:`#28 <https://github.com/aws/aws-iot-device-sdk-python/issues/28>`__
* bugfix:Issue:`#29 <https://github.com/aws/aws-iot-device-sdk-python/issues/29>`__
* bugfix:Pull request:`#32 <https://github.com/aws/aws-iot-device-sdk-python/pull/32>`__
* improvement:Pull request:`#38 <https://github.com/aws/aws-iot-device-sdk-python/pull/38>`__
* bugfix:Pull request:`#45 <https://github.com/aws/aws-iot-device-sdk-python/pull/45>`__
* improvement:Pull request:`#46 <https://github.com/aws/aws-iot-device-sdk-python/pull/46>`__

1.1.1
=====
* bugfix:Issue:`#23 <https://github.com/aws/aws-iot-device-sdk-python/issues/23>`__
* bugfix:README documentation


1.1.0
=====
* feature:AWSIoTMQTTClient:last will configuration APIs
* bugfix:Pull request:`#12 <https://github.com/aws/aws-iot-device-sdk-python/pull/12>`__
* bugfix:Pull request:`#14 <https://github.com/aws/aws-iot-device-sdk-python/pull/14>`__
* Addressed issue:`#15 <https://github.com/aws/aws-iot-device-sdk-python/issues/15>`__

1.0.1
=====
* bugfix:Pull request:`#9 <https://github.com/aws/aws-iot-device-sdk-python/pull/9>`__

1.0.0
=====
* feature:AWSIoTMQTTClient:basic MQTT APIs
* feature:AWSIoTMQTTClient:auto-reconnection/resubscribe
* feature:AWSIoTMQTTClient:offline publish requests queueing and draining
* feature:AWSIoTMQTTShadowClient:basic Shadow APIs
