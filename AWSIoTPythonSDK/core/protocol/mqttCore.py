# /*
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

import sys
import ssl
import time
import logging
import threading
import AWSIoTPythonSDK.core.protocol.paho.client as mqtt
import AWSIoTPythonSDK.core.util.offlinePublishQueue as offlinePublishQueue
from threading import Lock
from AWSIoTPythonSDK.exception.AWSIoTExceptions import connectError
from AWSIoTPythonSDK.exception.AWSIoTExceptions import connectTimeoutException
from AWSIoTPythonSDK.exception.AWSIoTExceptions import disconnectError
from AWSIoTPythonSDK.exception.AWSIoTExceptions import disconnectTimeoutException
from AWSIoTPythonSDK.exception.AWSIoTExceptions import publishError
from AWSIoTPythonSDK.exception.AWSIoTExceptions import publishQueueFullException
from AWSIoTPythonSDK.exception.AWSIoTExceptions import publishQueueDisabledException
from AWSIoTPythonSDK.exception.AWSIoTExceptions import subscribeError
from AWSIoTPythonSDK.exception.AWSIoTExceptions import subscribeTimeoutException
from AWSIoTPythonSDK.exception.AWSIoTExceptions import unsubscribeError
from AWSIoTPythonSDK.exception.AWSIoTExceptions import unsubscribeTimeoutException

# Class that holds queued publish request details
class _publishRequest:
    def __init__(self, srcTopic, srcPayload, srcQos, srcRetain):
        self.topic = srcTopic
        self.payload = srcPayload
        self.qos = srcQos
        self.retain = srcRetain


class mqttCore:

    def getClientID(self):
        return self._clientID

    def setConnectDisconnectTimeoutSecond(self, srcConnectDisconnectTimeout):
        self._connectdisconnectTimeout = srcConnectDisconnectTimeout
        self._log.debug("Set maximum connect/disconnect timeout to be " + str(self._connectdisconnectTimeout) + " second.")

    def getConnectDisconnectTimeoutSecond(self):
        return self._connectdisconnectTimeout

    def setMQTTOperationTimeoutSecond(self, srcMQTTOperationTimeout):
        self._mqttOperationTimeout = srcMQTTOperationTimeout
        self._log.debug("Set maximum MQTT operation timeout to be " + str(self._mqttOperationTimeout) + " second")

    def getMQTTOperationTimeoutSecond(self):
        return self._mqttOperationTimeout

    def setUserData(self, srcUserData):
        self._pahoClient.user_data_set(srcUserData)

    def createPahoClient(self, clientID, cleanSession, userdata, protocol, useWebsocket):
        return mqtt.Client(clientID, cleanSession, userdata, protocol, useWebsocket)  # Throw exception when error happens

    def _doResubscribe(self):
        if self._subscribePool:
            self._resubscribeCount = len(self._subscribePool) # This is the only place where _resubscribeCount gets its count
            for key in self._subscribePool.keys():
                qos, callback = self._subscribePool.get(key)
                try:
                    self.subscribe(key, qos, callback)
                    time.sleep(self._drainingIntervalSecond)  # Subscribe requests should also be sent out using the draining interval
                except (subscribeError, subscribeTimeoutException):
                    self._log.warn("Error in re-subscription to topic: " + str(key))
                    pass  # Subscribe error resulted from network error, will redo subscription in the next re-connect

    # Performed in a seperate thread, draining the offlinePublishQueue at a given draining rate
    # Publish theses queued messages to Paho
    # Should always pop the queue since Paho has its own queueing and retry logic
    # Should exit immediately when there is an error in republishing queued message
    # Should leave it to the next round of reconnect/resubscribe/republish logic at mqttCore
    def _doPublishDraining(self):
        while True:
            self._offlinePublishQueueLock.acquire()
            # This should be a complete publish requests containing topic, payload, qos, retain information
            # This is the only thread that pops the offlinePublishQueue
            if self._offlinePublishQueue:
                queuedPublishRequest = self._offlinePublishQueue.pop(0)
                # Publish it (call paho API directly)
                (rc, mid) = self._pahoClient.publish(queuedPublishRequest.topic, queuedPublishRequest.payload, queuedPublishRequest.qos, queuedPublishRequest.retain)
                if rc != 0:
                    self._offlinePublishQueueLock.release()
                    break
            else:
                self._drainingComplete = True
                self._offlinePublishQueueLock.release()
                break
            self._offlinePublishQueueLock.release()
            time.sleep(self._drainingIntervalSecond)

    # Callbacks
    def on_connect(self, client, userdata, flags, rc):
        self._disconnectResultCode = sys.maxsize
        self._connectResultCode = rc
        if self._connectResultCode == 0:  # If this is a successful connect, do resubscribe
            processResubscription = threading.Thread(target=self._doResubscribe)
            processResubscription.start()
        # If we do not have any topics to resubscribe to, still start a new thread to process queued publish requests
        if not self._subscribePool:
            offlinePublishQueueDraining = threading.Thread(target=self._doPublishDraining)
            offlinePublishQueueDraining.start()
        self._log.debug("Connect result code " + str(rc))

    def on_disconnect(self, client, userdata, rc):
        self._connectResultCode = sys.maxsize
        self._disconnectResultCode = rc
        self._drainingComplete = False  # Draining status should be reset when disconnect happens
        self._log.debug("Disconnect result code " + str(rc))

    def on_subscribe(self, client, userdata, mid, granted_qos):
        # Execution of this callback is atomic, guaranteed by Paho
        # Check if we have got all SUBACKs for all resubscriptions
        self._log.debug("_resubscribeCount: " + str(self._resubscribeCount))
        if self._resubscribeCount > 0:  # Check if there is actually a need for resubscribe
            self._resubscribeCount -= 1  # collect SUBACK for all resubscriptions
            if self._resubscribeCount == 0:
                # start a thread draining the offline publish queue
                offlinePublishQueueDraining = threading.Thread(target=self._doPublishDraining)
                offlinePublishQueueDraining.start()
                self._resubscribeCount = -1  # Recover the context for resubscribe
        self._subscribeSent = True
        self._log.debug("Subscribe request " + str(mid) + " sent.")

    def on_unsubscribe(self, client, userdata, mid):
        self._unsubscribeSent = True
        self._log.debug("Unsubscribe request " + str(mid) + " sent.")

    def on_message(self, client, userdata, message):
        # Generic message callback
        self._log.warn("Received (No custom callback registered) : message: " + str(message.payload) + " from topic: " + str(message.topic))

    ####### API starts here #######
    def __init__(self, clientID, cleanSession, protocol, srcUseWebsocket=False):
        if clientID is None or cleanSession is None or protocol is None:
            raise TypeError("None type inputs detected.")
        # All internal data member should be unique per mqttCore intance
        # Tool handler
        self._log = logging.getLogger(__name__)
        self._clientID = clientID
        self._pahoClient = self.createPahoClient(clientID, cleanSession, None, protocol, srcUseWebsocket)  # User data is set to None as default
        self._log.debug("Paho MQTT Client init.")
        self._log.info("ClientID: " + str(clientID))
        protocolType = "MQTTv3.1.1"
        if protocol == 3:
            protocolType = "MQTTv3.1"
        self._log.info("Protocol: " + protocolType)
        self._pahoClient.on_connect = self.on_connect
        self._pahoClient.on_disconnect = self.on_disconnect
        self._pahoClient.on_message = self.on_message
        self._pahoClient.on_subscribe = self.on_subscribe
        self._pahoClient.on_unsubscribe = self.on_unsubscribe
        self._log.debug("Register Paho MQTT Client callbacks.")
        # Tool data structure
        self._connectResultCode = sys.maxsize
        self._disconnectResultCode = sys.maxsize
        self._subscribeSent = False
        self._unsubscribeSent = False
        self._connectdisconnectTimeout = 30  # Default connect/disconnect timeout set to 30 second
        self._mqttOperationTimeout = 5  # Default MQTT operation timeout set to 5 second
        # Use Websocket
        self._useWebsocket = srcUseWebsocket
        # Subscribe record
        self._subscribePool = dict()
        self._resubscribeCount = -1  # Ensure that initial value for _resubscribeCount does not trigger draining on each SUBACK
        # Broker information
        self._host = ""
        self._port = -1
        self._cafile = ""
        self._key = ""
        self._cert = ""
        self._stsToken = ""
        # Operation mutex
        self._publishLock = Lock()
        self._subscribeLock = Lock()
        self._unsubscribeLock = Lock()
        # OfflinePublishQueue
        self._offlinePublishQueueLock = Lock()
        self._offlinePublishQueue = offlinePublishQueue.offlinePublishQueue(20, 1)
        # Draining interval in seconds
        self._drainingIntervalSecond = 0.5
        # Is Draining complete
        self._drainingComplete = True
        self._log.debug("mqttCore init.")

    def configEndpoint(self, srcHost, srcPort):
        if srcHost is None or srcPort is None:
            self._log.error("configEndpoint: None type inputs detected.")
            raise TypeError("None type inputs detected.")
        self._host = srcHost
        self._port = srcPort

    def configCredentials(self, srcCAFile, srcKey, srcCert):
        if srcCAFile is None or srcKey is None or srcCert is None:
            self._log.error("configCredentials: None type inputs detected.")
            raise TypeError("None type inputs detected.")
        self._cafile = srcCAFile
        self._key = srcKey
        self._cert = srcCert
        self._log.debug("Load CAFile from: " + self._cafile)
        self._log.debug("Load Key from: " + self._key)
        self._log.debug("Load Cert from: " + self._cert)

    def configIAMCredentials(self, srcAWSAccessKeyID, srcAWSSecretAccessKey, srcAWSSessionToken):
        if srcAWSSecretAccessKey is None or srcAWSSecretAccessKey is None or srcAWSSessionToken is None:
            self._log.error("configIAMCredentials: None type inputs detected.")
            raise TypeError("None type inputs detected.")
        self._pahoClient.configIAMCredentials(srcAWSAccessKeyID, srcAWSSecretAccessKey, srcAWSSessionToken)

    def setLastWill(self, srcTopic, srcPayload, srcQos):
        if srcTopic is None or srcPayload is None or srcQos is None:
            self._log.error("setLastWill: None type inputs detected.")
            raise TypeError("None type inputs detected.")
        self._pahoClient.will_set(srcTopic, srcPayload, srcQos, False)

    def clearLastWill(self):
        self._pahoClient.will_clear()

    def setBackoffTime(self, srcBaseReconnectTimeSecond, srcMaximumReconnectTimeSecond, srcMinimumConnectTimeSecond):
        if srcBaseReconnectTimeSecond is None or srcMaximumReconnectTimeSecond is None or srcMinimumConnectTimeSecond is None:
            self._log.error("setBackoffTime: None type inputs detected.")
            raise TypeError("None type inputs detected.")
        # Below line could raise ValueError if input params are not properly selected
        self._pahoClient.setBackoffTiming(srcBaseReconnectTimeSecond, srcMaximumReconnectTimeSecond, srcMinimumConnectTimeSecond)
        self._log.debug("Custom setting for backoff timing: baseReconnectTime = " + str(srcBaseReconnectTimeSecond) + " sec")
        self._log.debug("Custom setting for backoff timing: maximumReconnectTime = " + str(srcMaximumReconnectTimeSecond) + " sec")
        self._log.debug("Custom setting for backoff timing: minimumConnectTime = " + str(srcMinimumConnectTimeSecond) + " sec")

    def setOfflinePublishQueueing(self, srcQueueSize, srcDropBehavior=mqtt.MSG_QUEUEING_DROP_NEWEST):
        if srcQueueSize is None or srcDropBehavior is None:
            self._log.error("setOfflinePublishQueueing: None type inputs detected.")
            raise TypeError("None type inputs detected.")
        self._offlinePublishQueue = offlinePublishQueue.offlinePublishQueue(srcQueueSize, srcDropBehavior)
        self._log.debug("Custom setting for publish queueing: queueSize = " + str(srcQueueSize))
        dropBehavior_word = "Drop Oldest"
        if srcDropBehavior == 1:
            dropBehavior_word = "Drop Newest"
        self._log.debug("Custom setting for publish queueing: dropBehavior = " + dropBehavior_word)

    def setDrainingIntervalSecond(self, srcDrainingIntervalSecond):
        if srcDrainingIntervalSecond is None:
            self._log.error("setDrainingIntervalSecond: None type inputs detected.")
            raise TypeError("None type inputs detected.")
        if srcDrainingIntervalSecond < 0:
            self._log.error("setDrainingIntervalSecond: Draining interval should not be negative.")
            raise ValueError("Draining interval should not be negative.")
        self._drainingIntervalSecond = srcDrainingIntervalSecond
        self._log.debug("Custom setting for draining interval: " + str(srcDrainingIntervalSecond) + " sec")

    # MQTT connection
    def connect(self, keepAliveInterval=30):
        if keepAliveInterval is None :
            self._log.error("connect: None type inputs detected.")
            raise TypeError("None type inputs detected.")
        if not isinstance(keepAliveInterval, int):
            self._log.error("connect: Wrong input type detected. KeepAliveInterval must be an integer.")
            raise TypeError("Non-integer type inputs detected.")
        # Return connect succeeded/failed
        ret = False
        # TLS configuration
        if self._useWebsocket:
            # History issue from Yun SDK where AR9331 embedded Linux only have Python 2.7.3 
            # pre-installed. In this version, TLSv1_2 is not even an option.
            # SSLv23 is a work-around which selects the highest TLS version between the client
            # and service. If user installs opensslv1.0.1+, this option will work fine for Mutal
            # Auth.
            # Note that we cannot force TLSv1.2 for Mutual Auth. in Python 2.7.3 and TLS support
            # in Python only starts from Python2.7.
            # See also: https://docs.python.org/2/library/ssl.html#ssl.PROTOCOL_SSLv23
            self._pahoClient.tls_set(ca_certs=self._cafile, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_SSLv23)
            self._log.info("Connection type: Websocket")
        else:
            self._pahoClient.tls_set(self._cafile, self._cert, self._key, ssl.CERT_REQUIRED, ssl.PROTOCOL_SSLv23)  # Throw exception...
            self._log.info("Connection type: TLSv1.2 Mutual Authentication")
        # Connect
        self._pahoClient.connect(self._host, self._port, keepAliveInterval)  # Throw exception...
        self._pahoClient.loop_start()
        TenmsCount = 0
        while(TenmsCount != self._connectdisconnectTimeout * 100 and self._connectResultCode == sys.maxsize):
            TenmsCount += 1
            time.sleep(0.01)
        if(self._connectResultCode == sys.maxsize):
            self._log.error("Connect timeout.")
            self._pahoClient.loop_stop()
            raise connectTimeoutException()
        elif(self._connectResultCode == 0):
            ret = True
            self._log.info("Connected to AWS IoT.")
            self._log.debug("Connect time consumption: " + str(float(TenmsCount) * 10) + "ms.")
        else:
            self._log.error("A connect error happened: " + str(self._connectResultCode))
            self._pahoClient.loop_stop()
            raise connectError(self._connectResultCode)
        return ret

    def disconnect(self):
        # Return disconnect succeeded/failed
        ret = False
        # Disconnect
        self._pahoClient.disconnect()  # Throw exception...
        TenmsCount = 0
        while(TenmsCount != self._connectdisconnectTimeout * 100 and self._disconnectResultCode == sys.maxsize):
            TenmsCount += 1
            time.sleep(0.01)
        if(self._disconnectResultCode == sys.maxsize):
            self._log.error("Disconnect timeout.")
            raise disconnectTimeoutException()
        elif(self._disconnectResultCode == 0):
            ret = True
            self._log.info("Disconnected.")
            self._log.debug("Disconnect time consumption: " + str(float(TenmsCount) * 10) + "ms.")
            self._pahoClient.loop_stop()  # Do NOT maintain a background thread for socket communication since it is a successful disconnect
        else:
            self._log.error("A disconnect error happened: " + str(self._disconnectResultCode))
            raise disconnectError(self._disconnectResultCode)
        return ret

    def publish(self, topic, payload, qos, retain):
        if(topic is None or payload is None or qos is None or retain is None):
            self._log.error("publish: None type inputs detected.")
            raise TypeError("None type inputs detected.")
        # Return publish succeeded/failed
        ret = False
        # Queueing should happen when disconnected or draining is in progress
        self._offlinePublishQueueLock.acquire()
        queuedPublishCondition = not self._drainingComplete or self._connectResultCode == sys.maxsize
        if queuedPublishCondition:
            if self._connectResultCode == sys.maxsize:
                self._log.info("Offline publish request detected.")
            # If the client is connected but draining is not completed...
            elif not self._drainingComplete:
                self._log.info("Drainging is still on-going.")
            self._log.info("Try queueing up this request...")
            # Publish to the queue and report error (raise Exception)
            currentQueuedPublishRequest = _publishRequest(topic, payload, qos, retain)
            # Try to append the element...
            appendResult = self._offlinePublishQueue.append(currentQueuedPublishRequest)
            # When the queue is full...
            if appendResult == self._offlinePublishQueue.APPEND_FAILURE_QUEUE_FULL:
                self._offlinePublishQueueLock.release()
                raise publishQueueFullException()
            # When the queue is disabled...
            elif appendResult == self._offlinePublishQueue.APPEND_FAILURE_QUEUE_DISABLED:
                self._offlinePublishQueueLock.release()
                raise publishQueueDisabledException()
            # When the queue is good...
            else:
                self._offlinePublishQueueLock.release()
        # Publish to Paho
        else:
            self._offlinePublishQueueLock.release()
            self._publishLock.acquire()
            # Publish
            (rc, mid) = self._pahoClient.publish(topic, payload, qos, retain)  # Throw exception...
            self._log.debug("Try to put a publish request " + str(mid) + " in the TCP stack.")
            ret = rc == 0
            if(ret):
                self._log.debug("Publish request " + str(mid) + " succeeded.")
            else:
                self._log.error("Publish request " + str(mid) + " failed with code: " + str(rc))
                self._publishLock.release()  # Release the lock when exception is raised
                raise publishError(rc)
            self._publishLock.release()
        return ret

    def subscribe(self, topic, qos, callback):
        if(topic is None or qos is None):
            self._log.error("subscribe: None type inputs detected.")
            raise TypeError("None type inputs detected.")
        # Return subscribe succeeded/failed
        ret = False
        self._subscribeLock.acquire()
        # Subscribe
        # Register callback
        if(callback is not None):
            self._pahoClient.message_callback_add(topic, callback)
        (rc, mid) = self._pahoClient.subscribe(topic, qos)  # Throw exception...
        self._log.debug("Started a subscribe request " + str(mid))
        TenmsCount = 0
        while(TenmsCount != self._mqttOperationTimeout * 100 and not self._subscribeSent):
            TenmsCount += 1
            time.sleep(0.01)
        if(self._subscribeSent):
            ret = rc == 0
            if(ret):
                self._subscribePool[topic] = (qos, callback)
                self._log.debug("Subscribe request " + str(mid) + " succeeded. Time consumption: " + str(float(TenmsCount) * 10) + "ms.")
            else:
                if(callback is not None):
                    self._pahoClient.message_callback_remove(topic)
                self._log.error("Subscribe request " + str(mid) + " failed with code: " + str(rc))
                self._log.debug("Callback cleaned up.")
                self._subscribeLock.release()  # Release the lock when exception is raised
                raise subscribeError(rc)
        else:
            # Subscribe timeout
            if(callback is not None):
                self._pahoClient.message_callback_remove(topic)
            self._log.error("No feedback detected for subscribe request " + str(mid) + ". Timeout and failed.")
            self._log.debug("Callback cleaned up.")
            self._subscribeLock.release()  # Release the lock when exception is raised
            raise subscribeTimeoutException()
        self._subscribeSent = False
        self._log.debug("Recover subscribe context for the next request: subscribeSent: " + str(self._subscribeSent))
        self._subscribeLock.release()
        return ret

    def unsubscribe(self, topic):
        if(topic is None):
            self._log.error("unsubscribe: None type inputs detected.")
            raise TypeError("None type inputs detected.")
        self._log.debug("unsubscribe from: " + topic)
        # Return unsubscribe succeeded/failed
        ret = False
        self._unsubscribeLock.acquire()
        # Unsubscribe
        (rc, mid) = self._pahoClient.unsubscribe(topic)  # Throw exception...
        self._log.debug("Started an unsubscribe request " + str(mid))
        TenmsCount = 0
        while(TenmsCount != self._mqttOperationTimeout * 100 and not self._unsubscribeSent):
            TenmsCount += 1
            time.sleep(0.01)
        if(self._unsubscribeSent):
            ret = rc == 0
            if(ret):
                try:
                    del self._subscribePool[topic]
                except KeyError:
                    pass  # Ignore topics that are never subscribed to
                self._log.debug("Unsubscribe request " + str(mid) + " succeeded. Time consumption: " + str(float(TenmsCount) * 10) + "ms.")
                self._pahoClient.message_callback_remove(topic)
                self._log.debug("Remove the callback.")
            else:
                self._log.error("Unsubscribe request " + str(mid) + " failed with code: " + str(rc))
                self._unsubscribeLock.release()  # Release the lock when exception is raised
                raise unsubscribeError(rc)
        else:
            # Unsubscribe timeout
            self._log.error("No feedback detected for unsubscribe request " + str(mid) + ". Timeout and failed.")
            self._unsubscribeLock.release()  # Release the lock when exception is raised
            raise unsubscribeTimeoutException()
        self._unsubscribeSent = False
        self._log.debug("Recover unsubscribe context for the next request: unsubscribeSent: " + str(self._unsubscribeSent))
        self._unsubscribeLock.release()
        return ret
