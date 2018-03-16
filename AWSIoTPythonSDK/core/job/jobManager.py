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

import logging
import time
from threading import Lock

class _jobAction:
    _actionType = ["get", "start-next", "update", "notify", "notify-next"]

    def __init__(self, srcThingName, srcActionName, srcJobId=None):
        if srcActionName is None or srcActionName not in self._actionType:
            raise TypeError("Unsupported job action.")
        if srcJobId is None and srcActionName == "update":
            raise TypeError("Unsupported job action.")
        if srcJobId is not None and srcActionName not in ["get", "update"]:
            raise TypeError("Unsupported job action.")
        self._thingName = srcThingName
        self._actionName = srcActionName
        # Add srcJobId to get and update actions if required
        if srcJobId is not None and self._actionName in ["get", "update"]:
            self._actionName = srcJobId + "/" + self._actionName
        self._topicGeneral = "$aws/things/" + str(self._thingName) + "/jobs/" + str(self._actionName)
        self._topicAccept = "$aws/things/" + str(self._thingName) + "/jobs/" + str(self._actionName) + "/accepted"
        self._topicReject = "$aws/things/" + str(self._thingName) + "/jobs/" + str(self._actionName) + "/rejected"

    def getTopicGeneral(self):
        return self._topicGeneral

    def getTopicAccept(self):
        return self._topicAccept

    def getTopicReject(self):
        return self._topicReject


class jobManager:

    _logger = logging.getLogger(__name__)

    def __init__(self, srcMQTTCore):
        # Load in mqttCore
        if srcMQTTCore is None:
            raise TypeError("None type inputs detected.")
        self._mqttCoreHandler = srcMQTTCore
        self._jobSubUnsubOperationLock = Lock()

    def basicJobPublish(self, srcThingName, srcJobAction, srcPayload, srcJobId=None):
        currentJobAction = _jobAction(srcThingName, srcJobAction, srcJobId=srcJobId)
        self._mqttCoreHandler.publish(currentJobAction.getTopicGeneral(), srcPayload, 0, False)

    def basicJobSubscribe(self, srcThingName, srcJobAction, srcCallback, srcJobId=None):
        with self._jobSubUnsubOperationLock:
            currentJobAction = _jobAction(srcThingName, srcJobAction, srcJobId=srcJobId)
            self._mqttCoreHandler.subscribe(currentJobAction.getTopicAccept(), 0, srcCallback)
            self._mqttCoreHandler.subscribe(currentJobAction.getTopicReject(), 0, srcCallback)
            time.sleep(2)

    def basicJobUnsubscribe(self, srcThingName, srcJobAction, srcJobId=None):
        with self._jobSubUnsubOperationLock:
            currentJobAction = _jobAction(srcThingName, srcJobAction, srcJobId=srcJobId)
            self._logger.debug(currentJobAction.getTopicAccept())
            self._mqttCoreHandler.unsubscribe(currentJobAction.getTopicAccept())
            self._logger.debug(currentJobAction.getTopicReject())
            self._mqttCoreHandler.unsubscribe(currentJobAction.getTopicReject())
