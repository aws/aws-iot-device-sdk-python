import sys
import mockPahoClient
import AWSIoTPythonSDK.core.protocol.mqttCore as mqttCore

class mockMQTTCoreQuiet(mqttCore.mqttCore):
    def createPahoClient(self, clientID, cleanSession, userdata, protocol, useWebsocket):
        return mockPahoClient.mockPahoClient(clientID, cleanSession, userdata, protocol, useWebsocket)

    def setReturnTupleForPahoClient(self, srcReturnTuple):
        self._pahoClient.setReturnTuple(srcReturnTuple)

    def connect(self, keepAliveInterval):
        pass

    def disconnect(self):
        pass

    def publish(self, topic, payload, qos, retain):
        pass

    def subscribe(self, topic, qos, callback):
        pass

    def unsubscribe(self, topic):
        pass

class mockMQTTCoreQuietWithSubRecords(mockMQTTCoreQuiet):

    def reinitSubscribePool(self):
        self._subscribePoolRecords = dict()

    def subscribe(self, topic, qos, callback):
        self._subscribePoolRecords[topic] = qos

