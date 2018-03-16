# /*
# * Copyright 2010-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import json
import logging
import uuid
from threading import Timer, Lock, Thread


class _jobRequestToken:

    URN_PREFIX_LENGTH = 9

    def getNextToken(self):
        return uuid.uuid4().urn[self.URN_PREFIX_LENGTH:]  # We only need the uuid digits, not the urn prefix


class _basicJSONParser:

    def setString(self, srcString):
        self._rawString = srcString
        self._dictionObject = None

    def regenerateString(self):
        return json.dumps(self._dictionaryObject)

    def getAttributeValue(self, srcAttributeKey):
        return self._dictionaryObject.get(srcAttributeKey)

    def setAttributeValue(self, srcAttributeKey, srcAttributeValue):
        self._dictionaryObject[srcAttributeKey] = srcAttributeValue

    def validateJSON(self):
        try:
            self._dictionaryObject = json.loads(self._rawString)
        except ValueError:
            return False
        return True


class deviceJob:
    _logger = logging.getLogger(__name__)

    def __init__(self, srcJobName, srcIsPersistentSubscribe, srcJobManager):
        """

        The class that denotes a local/client-side device job instance.

        Users can perform job operations on this instance to retrieve and modify the 
        corresponding job JSON document in AWS IoT Cloud. The following job operations 
        are available:

        - Get
        
        - Update

        - Delete

        - Listen on delta

        - Cancel listening on delta

        This is returned from :code:`AWSIoTPythonSDK.MQTTLib.AWSIoTMQTTJobClient.createJobWithName` function call. 
        No need to call directly from user scripts.

        """
        if srcJobName is None or srcIsPersistentSubscribe is None or srcJobManager is None:
            raise TypeError("None type inputs detected.")
        self._jobName = srcJobName
        # Tool handler
        self._jobManagerHandler = srcJobManager
        self._basicJSONParserHandler = _basicJSONParser()
        self._tokenHandler = _jobRequestToken()
        # Properties
        self._isPersistentSubscribe = srcIsPersistentSubscribe
        self._lastVersionInSync = -1  # -1 means not initialized
        self._isGetSubscribed = False
        self._isUpdateSubscribed = False
        self._isDeleteSubscribed = False
        self._jobSubscribeCallbackTable = dict()
        self._jobSubscribeCallbackTable["get"] = None
        self._jobSubscribeCallbackTable["delete"] = None
        self._jobSubscribeCallbackTable["update"] = None
        self._jobSubscribeCallbackTable["delta"] = None
        self._jobSubscribeStatusTable = dict()
        self._jobSubscribeStatusTable["get"] = 0
        self._jobSubscribeStatusTable["delete"] = 0
        self._jobSubscribeStatusTable["update"] = 0
        self._tokenPool = dict()
        self._dataStructureLock = Lock()

    def _doNonPersistentUnsubscribe(self, currentAction):
        self._jobManagerHandler.basicJobUnsubscribe(self._jobName, currentAction)
        self._logger.info("Unsubscribed to " + currentAction + " accepted/rejected topics for deviceJob: " + self._jobName)

    def generalCallback(self, client, userdata, message):
        # In Py3.x, message.payload comes in as a bytes(string)
        # json.loads needs a string input
        with self._dataStructureLock:
            currentTopic = message.topic
            currentAction = self._parseTopicAction(currentTopic)  # get/delete/update/delta
            currentType = self._parseTopicType(currentTopic)  # accepted/rejected/delta
            payloadUTF8String = message.payload.decode('utf-8')
            # get/delete/update: Need to deal with token, timer and unsubscribe
            if currentAction in ["get", "delete", "update"]:
                # Check for token
                self._basicJSONParserHandler.setString(payloadUTF8String)
                if self._basicJSONParserHandler.validateJSON():  # Filter out invalid JSON
                    currentToken = self._basicJSONParserHandler.getAttributeValue(u"clientToken")
                    if currentToken is not None:
                        self._logger.debug("job message clientToken: " + currentToken)
                    if currentToken is not None and currentToken in self._tokenPool.keys():  # Filter out JSON without the desired token
                        # Sync local version when it is an accepted response
                        self._logger.debug("Token is in the pool. Type: " + currentType)
                        if currentType == "accepted":
                            incomingVersion = self._basicJSONParserHandler.getAttributeValue(u"version")
                            # If it is get/update accepted response, we need to sync the local version
                            if incomingVersion is not None and incomingVersion > self._lastVersionInSync and currentAction != "delete":
                                self._lastVersionInSync = incomingVersion
                            # If it is a delete accepted, we need to reset the version
                            else:
                                self._lastVersionInSync = -1  # The version will always be synced for the next incoming delta/GU-accepted response
                        # Cancel the timer and clear the token
                        self._tokenPool[currentToken].cancel()
                        del self._tokenPool[currentToken]
                        # Need to unsubscribe?
                        self._jobSubscribeStatusTable[currentAction] -= 1
                        if not self._isPersistentSubscribe and self._jobSubscribeStatusTable.get(currentAction) <= 0:
                            self._jobSubscribeStatusTable[currentAction] = 0
                            processNonPersistentUnsubscribe = Thread(target=self._doNonPersistentUnsubscribe, args=[currentAction])
                            processNonPersistentUnsubscribe.start()
                        # Custom callback
                        if self._jobSubscribeCallbackTable.get(currentAction) is not None:
                            processCustomCallback = Thread(target=self._jobSubscribeCallbackTable[currentAction], args=[payloadUTF8String, currentType, currentToken])
                            processCustomCallback.start()
            # delta: Watch for version
            else:
                currentType += "/" + self._parseTopicJobName(currentTopic)
                # Sync local version
                self._basicJSONParserHandler.setString(payloadUTF8String)
                if self._basicJSONParserHandler.validateJSON():  # Filter out JSON without version
                    incomingVersion = self._basicJSONParserHandler.getAttributeValue(u"version")
                    if incomingVersion is not None and incomingVersion > self._lastVersionInSync:
                        self._lastVersionInSync = incomingVersion
                        # Custom callback
                        if self._jobSubscribeCallbackTable.get(currentAction) is not None:
                            processCustomCallback = Thread(target=self._jobSubscribeCallbackTable[currentAction], args=[payloadUTF8String, currentType, None])
                            processCustomCallback.start()

    def _parseTopicAction(self, srcTopic):
        ret = None
        fragments = srcTopic.split('/')
        if fragments[5] == "delta":
            ret = "delta"
        else:
            ret = fragments[4]
        return ret

    def _parseTopicType(self, srcTopic):
        fragments = srcTopic.split('/')
        return fragments[5]

    def _parseTopicJobName(self, srcTopic):
        fragments = srcTopic.split('/')
        return fragments[2]

    def _timerHandler(self, srcActionName, srcToken):
        with self._dataStructureLock:
            # Don't crash if we try to remove an unknown token
            if srcToken not in self._tokenPool:
                self._logger.warn('Tried to remove non-existent token from pool: %s' % str(srcToken))
                return
            # Remove the token
            del self._tokenPool[srcToken]
            # Need to unsubscribe?
            self._jobSubscribeStatusTable[srcActionName] -= 1
            if not self._isPersistentSubscribe and self._jobSubscribeStatusTable.get(srcActionName) <= 0:
                self._jobSubscribeStatusTable[srcActionName] = 0
                self._jobManagerHandler.basicJobUnsubscribe(self._jobName, srcActionName)
            # Notify time-out issue
            if self._jobSubscribeCallbackTable.get(srcActionName) is not None:
                self._logger.info("Job request with token: " + str(srcToken) + " has timed out.")
                self._jobSubscribeCallbackTable[srcActionName]("REQUEST TIME OUT", "timeout", srcToken)

    def jobGet(self, srcCallback, srcTimeout):
        """
        **Description**

        Retrieve the device job JSON document from AWS IoT by publishing an empty JSON document to the 
        corresponding job topics. Job response topics will be subscribed to receive responses from 
        AWS IoT regarding the result of the get operation. Retrieved job JSON document will be available 
        in the registered callback. If no response is received within the provided timeout, a timeout 
        notification will be passed into the registered callback.

        **Syntax**

        .. code:: python

          # Retrieve the job JSON document from AWS IoT, with a timeout set to 5 seconds
          BotJob.jobGet(customCallback, 5)

        **Parameters**

        *srcCallback* - Function to be called when the response for this job request comes back. Should 
        be in form :code:`customCallback(payload, responseStatus, token)`, where :code:`payload` is the 
        JSON document returned, :code:`responseStatus` indicates whether the request has been accepted, 
        rejected or is a delta message, :code:`token` is the token used for tracing in this request.

        *srcTimeout* - Timeout to determine whether the request is invalid. When a request gets timeout, 
        a timeout notification will be generated and put into the registered callback to notify users.

        **Returns**

        The token used for tracing in this job request.

        """
        with self._dataStructureLock:
            # Update callback data structure
            self._jobSubscribeCallbackTable["get"] = srcCallback
            # Update number of pending feedback
            self._jobSubscribeStatusTable["get"] += 1
            # clientToken
            currentToken = self._tokenHandler.getNextToken()
            self._tokenPool[currentToken] = Timer(srcTimeout, self._timerHandler, ["get", currentToken])
            self._basicJSONParserHandler.setString("{}")
            self._basicJSONParserHandler.validateJSON()
            self._basicJSONParserHandler.setAttributeValue("clientToken", currentToken)
            currentPayload = self._basicJSONParserHandler.regenerateString()
        # Two subscriptions
        if not self._isPersistentSubscribe or not self._isGetSubscribed:
            self._jobManagerHandler.basicJobSubscribe(self._jobName, "get", self.generalCallback)
            self._isGetSubscribed = True
            self._logger.info("Subscribed to get accepted/rejected topics for deviceJob: " + self._jobName)
        # One publish
        self._jobManagerHandler.basicJobPublish(self._jobName, "get", currentPayload)
        # Start the timer
        self._tokenPool[currentToken].start()
        return currentToken

    def jobDelete(self, srcCallback, srcTimeout):
        """
        **Description**

        Delete the device job from AWS IoT by publishing an empty JSON document to the corresponding 
        job topics. Job response topics will be subscribed to receive responses from AWS IoT 
        regarding the result of the get operation. Responses will be available in the registered callback. 
        If no response is received within the provided timeout, a timeout notification will be passed into 
        the registered callback.

        **Syntax**

        .. code:: python

          # Delete the device job from AWS IoT, with a timeout set to 5 seconds
          BotJob.jobDelete(customCallback, 5)

        **Parameters**

        *srcCallback* - Function to be called when the response for this job request comes back. Should 
        be in form :code:`customCallback(payload, responseStatus, token)`, where :code:`payload` is the 
        JSON document returned, :code:`responseStatus` indicates whether the request has been accepted, 
        rejected or is a delta message, :code:`token` is the token used for tracing in this request.

        *srcTimeout* - Timeout to determine whether the request is invalid. When a request gets timeout, 
        a timeout notification will be generated and put into the registered callback to notify users.

        **Returns**

        The token used for tracing in this job request.

        """
        with self._dataStructureLock:
            # Update callback data structure
            self._jobSubscribeCallbackTable["delete"] = srcCallback
            # Update number of pending feedback
            self._jobSubscribeStatusTable["delete"] += 1
            # clientToken
            currentToken = self._tokenHandler.getNextToken()
            self._tokenPool[currentToken] = Timer(srcTimeout, self._timerHandler, ["delete", currentToken])
            self._basicJSONParserHandler.setString("{}")
            self._basicJSONParserHandler.validateJSON()
            self._basicJSONParserHandler.setAttributeValue("clientToken", currentToken)
            currentPayload = self._basicJSONParserHandler.regenerateString()
        # Two subscriptions
        if not self._isPersistentSubscribe or not self._isDeleteSubscribed:
            self._jobManagerHandler.basicJobSubscribe(self._jobName, "delete", self.generalCallback)
            self._isDeleteSubscribed = True
            self._logger.info("Subscribed to delete accepted/rejected topics for deviceJob: " + self._jobName)
        # One publish
        self._jobManagerHandler.basicJobPublish(self._jobName, "delete", currentPayload)
        # Start the timer
        self._tokenPool[currentToken].start()
        return currentToken

    def jobUpdate(self, srcJSONPayload, srcCallback, srcTimeout):
        """
        **Description**

        Update the device job JSON document string from AWS IoT by publishing the provided JSON 
        document to the corresponding job topics. Job response topics will be subscribed to 
        receive responses from AWS IoT regarding the result of the get operation. Response will be 
        available in the registered callback. If no response is received within the provided timeout, 
        a timeout notification will be passed into the registered callback.

        **Syntax**

        .. code:: python

          # Update the job JSON document from AWS IoT, with a timeout set to 5 seconds
          BotJob.jobUpdate(newJobJSONDocumentString, customCallback, 5)

        **Parameters**

        *srcJSONPayload* - JSON document string used to update job JSON document in AWS IoT.

        *srcCallback* - Function to be called when the response for this job request comes back. Should 
        be in form :code:`customCallback(payload, responseStatus, token)`, where :code:`payload` is the 
        JSON document returned, :code:`responseStatus` indicates whether the request has been accepted, 
        rejected or is a delta message, :code:`token` is the token used for tracing in this request.

        *srcTimeout* - Timeout to determine whether the request is invalid. When a request gets timeout, 
        a timeout notification will be generated and put into the registered callback to notify users.

        **Returns**

        The token used for tracing in this job request.

        """
        # Validate JSON
        self._basicJSONParserHandler.setString(srcJSONPayload)
        if self._basicJSONParserHandler.validateJSON():
            with self._dataStructureLock:
                # clientToken
                currentToken = self._tokenHandler.getNextToken()
                self._tokenPool[currentToken] = Timer(srcTimeout, self._timerHandler, ["update", currentToken])
                self._basicJSONParserHandler.setAttributeValue("clientToken", currentToken)
                JSONPayloadWithToken = self._basicJSONParserHandler.regenerateString()
                # Update callback data structure
                self._jobSubscribeCallbackTable["update"] = srcCallback
                # Update number of pending feedback
                self._jobSubscribeStatusTable["update"] += 1
            # Two subscriptions
            if not self._isPersistentSubscribe or not self._isUpdateSubscribed:
                self._jobManagerHandler.basicJobSubscribe(self._jobName, "update", self.generalCallback)
                self._isUpdateSubscribed = True
                self._logger.info("Subscribed to update accepted/rejected topics for deviceJob: " + self._jobName)
            # One publish
            self._jobManagerHandler.basicJobPublish(self._jobName, "update", JSONPayloadWithToken)
            # Start the timer
            self._tokenPool[currentToken].start()
        else:
            raise ValueError("Invalid JSON file.")
        return currentToken

    def jobRegisterDeltaCallback(self, srcCallback):
        """
        **Description**

        Listen on delta topics for this device job by subscribing to delta topics. Whenever there 
        is a difference between the desired and reported state, the registered callback will be called 
        and the delta payload will be available in the callback.

        **Syntax**

        .. code:: python

          # Listen on delta topics for BotJob
          BotJob.jobRegisterDeltaCallback(customCallback)

        **Parameters**

        *srcCallback* - Function to be called when the response for this job request comes back. Should 
        be in form :code:`customCallback(payload, responseStatus, token)`, where :code:`payload` is the 
        JSON document returned, :code:`responseStatus` indicates whether the request has been accepted, 
        rejected or is a delta message, :code:`token` is the token used for tracing in this request.

        **Returns**

        None

        """
        with self._dataStructureLock:
            # Update callback data structure
            self._jobSubscribeCallbackTable["delta"] = srcCallback
        # One subscription
        self._jobManagerHandler.basicJobSubscribe(self._jobName, "delta", self.generalCallback)
        self._logger.info("Subscribed to delta topic for deviceJob: " + self._jobName)

    def jobUnregisterDeltaCallback(self):
        """
        **Description**

        Cancel listening on delta topics for this device job by unsubscribing to delta topics. There will 
        be no delta messages received after this API call even though there is a difference between the 
        desired and reported state.

        **Syntax**

        .. code:: python

          # Cancel listening on delta topics for BotJob
          BotJob.jobUnregisterDeltaCallback()

        **Parameters**

        None

        **Returns**

        None

        """
        with self._dataStructureLock:
            # Update callback data structure
            del self._jobSubscribeCallbackTable["delta"]
        # One unsubscription
        self._jobManagerHandler.basicJobUnsubscribe(self._jobName, "delta")
        self._logger.info("Unsubscribed to delta topics for deviceJob: " + self._jobName)
