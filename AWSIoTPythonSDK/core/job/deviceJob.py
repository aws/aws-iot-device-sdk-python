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


# Flow:
# 1. Listen to notify or notify-next to trigger the next job
# 2. Call a function to get the next job to be executed and set its status to IN_PROGRESS
# 3. Set self._jobId accordingly
# 4. Pass the job description to the callback
# 5. Run job-handling logic
# 6. Call a function to update the job status to FAILED, SUCCESS, or REJECTED

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

    def __init__(self, srcThingName, srcIsPersistentSubscribe, srcJobManager):
        if srcThingName is None or srcIsPersistentSubscribe is None or srcJobManager is None:
            raise TypeError("None type inputs detected.")
        self._thingName = srcThingName
        # Tool handler
        self._jobManagerHandler = srcJobManager
        self._basicJSONParserHandler = _basicJSONParser()
        self._tokenHandler = _jobRequestToken()
        # Properties
        self._isPersistentSubscribe = srcIsPersistentSubscribe
        self._lastVersionInSync = -1  # -1 means not initialized
        self._isStartNextSubscribed = False
        self._isUpdateSubscribed = False
        self._currentJobId = None
        self._jobSubscribeCallbackTable = dict()
        self._jobSubscribeCallbackTable["update"] = None
        self._jobSubscribeCallbackTable["start-next"] = None
        self._jobSubscribeCallbackTable["notify"] = None
        self._jobSubscribeCallbackTable["notify-next"] = None
        self._jobSubscribeStatusTable = dict()
        self._jobSubscribeStatusTable["update"] = 0
        self._jobSubscribeStatusTable["start-next"] = 0
        self._tokenPool = dict()
        self._dataStructureLock = Lock()

    def _doNonPersistentUnsubscribe(self, currentAction):
        self._jobManagerHandler.basicJobUnsubscribe(self._thingName, currentAction)
        self._logger.info("Unsubscribed to " + currentAction + " accepted/rejected topics for device: " + self._thingName)

    def generalCallback(self, client, userdata, message):
        # In Py3.x, message.payload comes in as a bytes(string)
        # json.loads needs a string input
        with self._dataStructureLock:
            currentTopic = message.topic
            currentAction = self._parseTopicAction(currentTopic)  # start-next/update/notify-next
            currentType = self._parseTopicType(currentTopic)  # accepted/rejected/notify-next
            payloadUTF8String = message.payload.decode('utf-8')
            # start-next/update: Need to deal with token, timer and unsubscribe
            if currentAction in ["start-next", "update"]:
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
                            if currentAction == "start-next":
                                incomingExecution = self._basicJSONParserHandler.getAttributeValue(u"execution")
                                self._currentJobId = incomingExecution[u"jobId"]
                            else:
                                incomingExecution = self._basicJSONParserHandler.getAttributeValue(u"executionState")
                            incomingVersion = incomingExecution[u"versionNumber"]
                            incomingStatus = incomingExecution[u"status"]
                            # If it is accepted response, we need to sync the local version and jobId
                            if incomingVersion > self._lastVersionInSync:
                                self._lastVersionInSync = incomingVersion
                            # Reset version and jobId if job is finished
                            if incomingStatus in ["FAILED", "SUCCESS", "REJECTED"]:
                                self._lastVersionInSync = -1  # The version will always be synced for the next incoming accepted response
                                self._currentJobId = None
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
            # notify-next: Watch execution data
            else:
                currentType += "/" + self._parseTopicThingName(currentTopic)
                # Sync local version
                self._basicJSONParserHandler.setString(payloadUTF8String)
                if self._basicJSONParserHandler.validateJSON():  # Filter out JSON without execution
                    incomingExecution = self._basicJSONParserHandler.getAttributeValue(u"execution")
                    if incomingExecution is not None:
                        # Custom callback
                        if self._jobSubscribeCallbackTable.get(currentAction) is not None:
                            processCustomCallback = Thread(target=self._jobSubscribeCallbackTable[currentAction], args=[payloadUTF8String, currentType, None])
                            processCustomCallback.start()

    def _parseTopicAction(self, srcTopic):
        ret = None
        fragments = srcTopic.split('/')
        if fragments[-1] in ["accepted", "rejected"]:
            ret = fragments[-2]
        else:
            ret = fragments[-1]
        return ret

    def _parseTopicJobId(self, srcTopic):
        fragments = srcTopic.split('/')
        return fragments[4]

    def _parseTopicType(self, srcTopic):
        fragments = srcTopic.split('/')
        return fragments[-1]

    def _parseTopicThingName(self, srcTopic):
        fragments = srcTopic.split('/')
        return fragments[2]

    def _timerHandler(self, srcActionName, srcToken):
        with self._dataStructureLock:
            # Don't crash if we try to remove an unknown token
            if srcToken not in self._tokenPool:
                self._logger.warning('Tried to remove non-existent token from pool: %s' % str(srcToken))
                return
            # Remove the token
            del self._tokenPool[srcToken]
            # Need to unsubscribe?
            self._jobSubscribeStatusTable[srcActionName] -= 1
            if not self._isPersistentSubscribe and self._jobSubscribeStatusTable.get(srcActionName) <= 0:
                self._jobSubscribeStatusTable[srcActionName] = 0
                self._jobManagerHandler.basicJobUnsubscribe(self._thingName, srcActionName)
            # Notify time-out issue
            if self._jobSubscribeCallbackTable.get(srcActionName) is not None:
                self._logger.info("Job request with token: " + str(srcToken) + " has timed out.")
                self._jobSubscribeCallbackTable[srcActionName]("REQUEST TIME OUT", "timeout", srcToken)

    def jobStartNext(self, srcCallback, srcTimeout):
        with self._dataStructureLock:
            # Update callback data structure
            self._jobSubscribeCallbackTable["start-next"] = srcCallback
            # Update number of pending feedback
            self._jobSubscribeStatusTable["start-next"] += 1
            # clientToken
            currentToken = self._tokenHandler.getNextToken()
            self._tokenPool[currentToken] = Timer(srcTimeout, self._timerHandler, ["start-next", currentToken])
            self._basicJSONParserHandler.setString("{}")
            self._basicJSONParserHandler.validateJSON()
            self._basicJSONParserHandler.setAttributeValue("clientToken", currentToken)
            currentPayload = self._basicJSONParserHandler.regenerateString()
        # Two subscriptions
        if not self._isPersistentSubscribe or not self._isStartNextSubscribed:
            self._jobManagerHandler.basicJobSubscribe(self._thingName, "start-next", self.generalCallback)
            self._isStartNextSubscribed = True
            self._logger.info("Subscribed to start-next accepted/rejected topics for device: " + self._thingName)
        # One publish
        self._jobManagerHandler.basicJobPublish(self._thingName, "start-next", currentPayload)
        # Start the timer
        self._tokenPool[currentToken].start()
        return currentToken

    def jobUpdate(self, srcStatus, srcCallback, srcTimeout):
        if srcStatus not in ["FAILED", "SUCCESS", "REJECTED"]:
            raise TypeError("Invalid job status.")
        if self._currentJobId is None:
            raise TypeError("No job in progress to update.")
        with self._dataStructureLock:
            # Update callback data structure
            self._jobSubscribeCallbackTable["update"] = srcCallback
            # Update number of pending feedback
            self._jobSubscribeStatusTable["update"] += 1
            # clientToken
            currentToken = self._tokenHandler.getNextToken()
            self._tokenPool[currentToken] = Timer(srcTimeout, self._timerHandler, ["update", currentToken])
            self._basicJSONParserHandler.setString("{}")
            self._basicJSONParserHandler.validateJSON()
            self._basicJSONParserHandler.setAttributeValue("status", srcStatus)
            self._basicJSONParserHandler.setAttributeValue("expectedVersion", self._lastVersionInSync)
            self._basicJSONParserHandler.setAttributeValue("includeJobExecutionState", True)
            self._basicJSONParserHandler.setAttributeValue("clientToken", currentToken)
            currentPayload = self._basicJSONParserHandler.regenerateString()
        # Two subscriptions
        if not self._isPersistentSubscribe or not self._isUpdateSubscribed:
            self._jobManagerHandler.basicJobSubscribe(self._thingName, "update", self.generalCallback)
            self._isUpdateSubscribed = True
            self._logger.info("Subscribed to update accepted/rejected topics for device/job: " + self._thingName + "/" + self._currentJobId)
        # One publish
        self._jobManagerHandler.basicJobPublish(self._thingName, "update", currentPayload)
        # Start the timer
        self._tokenPool[currentToken].start()
        return currentToken

    def jobRegisterNotifyNextCallback(self, srcCallback):
        with self._dataStructureLock:
            # Update callback data structure
            self._jobSubscribeCallbackTable["notify-next"] = srcCallback
        # One subscription
        self._jobManagerHandler.basicJobSubscribe(self._thingName, "notify-next", self.generalCallback)
        self._logger.info("Subscribed to notify-next topic for device: " + self._thingName)

    def jobUnregisterNotifyNextCallback(self):
        with self._dataStructureLock:
            # Update callback data structure
            del self._jobSubscribeCallbackTable["notify-next"]
        # One unsubscription
        self._jobManagerHandler.basicJobUnsubscribe(self._thingName, "notify-next")
        self._logger.info("Unsubscribed from notify-next topic for device: " + self._thingName)
