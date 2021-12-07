import sys
import mockPahoClient
import AWSIoTPythonSDK.core.protocol.mqttCore as mqttCore

class mockMQTTCore(mqttCore.mqttCore):
    def createPahoClient(self, clientID, cleanSession, userdata, protocol, useWebsocket):
        return mockPahoClient.mockPahoClient(clientID, cleanSession, userdata, protocol, useWebsocket)

    def setReturnTupleForPahoClient(self, srcReturnTuple):
        self._pahoClient.setReturnTuple(srcReturnTuple)

class mockMQTTCoreWithSubRecords(mockMQTTCore):
    def reinitSubscribePool(self):
        self._subscribePoolRecords = dict()

    def subscribe(self, topic, qos, callback):
        self._subscribePoolRecords[topic] = qos
