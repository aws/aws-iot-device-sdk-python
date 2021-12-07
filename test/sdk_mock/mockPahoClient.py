import sys
import AWSIoTPythonSDK.core.protocol.paho.client as mqtt
import logging

class mockPahoClient(mqtt.Client):
    _log = logging.getLogger(__name__)
    _returnTuple = (-1, -1)
    # Callback handlers
    on_connect = None
    on_disconnect = None
    on_message = None
    on_publish = None
    on_subsribe = None
    on_unsubscribe = None

    def setReturnTuple(self, srcTuple):
        self._returnTuple = srcTuple

    # Tool function
    def tls_set(self, ca_certs=None, certfile=None, keyfile=None, cert_reqs=None, tls_version=None):
        self._log.debug("tls_set called.")

    def loop_start(self):
        self._log.debug("Socket thread started.")

    def loop_stop(self):
        self._log.debug("Socket thread stopped.")

    def message_callback_add(self, sub, callback):
        self._log.debug("Add a user callback. Topic: " + str(sub))
    
    # MQTT API
    def connect(self, host, port, keepalive):
        self._log.debug("Connect called.")

    def disconnect(self):
        self._log.debug("Disconnect called.")

    def publish(self, topic, payload, qos, retain):
        self._log.debug("Publish called.")
        return self._returnTuple

    def subscribe(self, topic, qos):
        self._log.debug("Subscribe called.")
        return self._returnTuple

    def unsubscribe(self, topic):
        self._log.debug("Unsubscribe called.")
        return self._returnTuple
