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

# This class implements the offline Publish Queue, with configurable length and drop behaviors.
# This queue will be used as the offline Publish Queue for all message outside Paho as an option
# to publish to when the client is offline.
# DROP_OLDEST: Drop the head of the queue when the size limit is reached.
# DROP_NEWEST: Drop the new incoming elements when the size limit is reached.

import logging

class offlinePublishQueue(list):

	_DROPBEHAVIOR_OLDEST = 0
	_DROPBEHAVIOR_NEWEST = 1

	APPEND_FAILURE_QUEUE_FULL = -1
	APPEND_FAILURE_QUEUE_DISABLED = -2
	APPEND_SUCCESS = 0

	_logger = logging.getLogger(__name__)

	def __init__(self, srcMaximumSize, srcDropBehavior=1):
		if not isinstance(srcMaximumSize, int) or not isinstance(srcDropBehavior, int):
			self._logger.error("init: MaximumSize/DropBehavior must be integer.")
			raise TypeError("MaximumSize/DropBehavior must be integer.")
		if srcDropBehavior != self._DROPBEHAVIOR_OLDEST and srcDropBehavior != self._DROPBEHAVIOR_NEWEST:
			self._logger.error("init: Drop behavior not supported.")
			raise ValueError("Drop behavior not supported.")
		list.__init__([])
		self._dropBehavior = srcDropBehavior
		# When self._maximumSize > 0, queue is limited
		# When self._maximumSize == 0, queue is disabled
		# When self._maximumSize < 0. queue is infinite
		self._maximumSize = srcMaximumSize

	def _isEnabled(self):
		return self._maximumSize != 0

	def _needDropMessages(self):
		# Need to drop messages when:
		# 1. Queue is limited and full
		# 2. Queue is disabled
		isQueueFull = len(self) >= self._maximumSize
		isQueueLimited = self._maximumSize > 0
		isQueueDisabled = not self._isEnabled()
		return (isQueueFull and isQueueLimited) or isQueueDisabled

	def setQueueBehaviorDropNewest(self):
		self._dropBehavior = self._DROPBEHAVIOR_NEWEST

	def setQueueBehaviorDropOldest(self):
		self._dropBehavior = self._DROPBEHAVIOR_OLDEST

	# Override
	# Append to a queue with a limited size.
	# Return APPEND_SUCCESS if the append is successful
	# Return APPEND_FAILURE_QUEUE_FULL if the append failed because the queue is full
	# Return APPEND_FAILURE_QUEUE_DISABLED if the append failed because the queue is disabled
	def append(self, srcData):
		ret = self.APPEND_SUCCESS
		if self._isEnabled():
			if self._needDropMessages():
				# We should drop the newest
				if self._dropBehavior == self._DROPBEHAVIOR_NEWEST:
					self._logger.warn("append: Full queue. Drop the newest: " + str(srcData))
					ret = self.APPEND_FAILURE_QUEUE_FULL
				# We should drop the oldest
				else:
					currentOldest = super(offlinePublishQueue, self).pop(0)
					self._logger.warn("append: Full queue. Drop the oldest: " + str(currentOldest))
					super(offlinePublishQueue, self).append(srcData)
					ret = self.APPEND_FAILURE_QUEUE_FULL
			else:
				self._logger.debug("append: Add new element: " + str(srcData))
				super(offlinePublishQueue, self).append(srcData)
		else:
			self._logger.debug("append: Queue is disabled. Drop the message: " + str(srcData))
			ret = self.APPEND_FAILURE_QUEUE_DISABLED
		return ret
