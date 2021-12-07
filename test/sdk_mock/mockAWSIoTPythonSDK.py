import sys
import mockMQTTCore
import mockMQTTCoreQuiet
from AWSIoTPythonSDK import MQTTLib
import AWSIoTPythonSDK.core.shadow.shadowManager as shadowManager

class mockAWSIoTMQTTClient(MQTTLib.AWSIoTMQTTClient):
	def __init__(self, clientID, protocolType, useWebsocket=False, cleanSession=True):
		self._mqttCore = mockMQTTCore.mockMQTTCore(clientID, cleanSession, protocolType, useWebsocket)

class mockAWSIoTMQTTClientWithSubRecords(MQTTLib.AWSIoTMQTTClient):
	def __init__(self, clientID, protocolType, useWebsocket=False, cleanSession=True):
		self._mqttCore = mockMQTTCore.mockMQTTCoreWithSubRecords(clientID, cleanSession, protocolType, useWebsocket)

class mockAWSIoTMQTTClientQuiet(MQTTLib.AWSIoTMQTTClient):
	def __init__(self, clientID, protocolType, useWebsocket=False, cleanSession=True):
		self._mqttCore = mockMQTTCoreQuiet.mockMQTTCoreQuiet(clientID, cleanSession, protocolType, useWebsocket)

class mockAWSIoTMQTTClientQuietWithSubRecords(MQTTLib.AWSIoTMQTTClient):
	def __init__(self, clientID, protocolType, useWebsocket=False, cleanSession=True):
		self._mqttCore = mockMQTTCoreQuiet.mockMQTTCoreQuietWithSubRecords(clientID, cleanSession, protocolType, useWebsocket)

class mockAWSIoTMQTTShadowClient(MQTTLib.AWSIoTMQTTShadowClient):
	def __init__(self, clientID, protocolType, useWebsocket=False, cleanSession=True):
		# AWSIOTMQTTClient instance
		self._AWSIoTMQTTClient = mockAWSIoTMQTTClientQuiet(clientID, protocolType, useWebsocket, cleanSession)
		# Configure it to disable offline Publish Queueing
		self._AWSIoTMQTTClient.configureOfflinePublishQueueing(0)
		self._AWSIoTMQTTClient.configureDrainingFrequency(10)
		# Now retrieve the configured mqttCore and init a shadowManager instance
		self._shadowManager = shadowManager.shadowManager(self._AWSIoTMQTTClient._mqttCore)


		
