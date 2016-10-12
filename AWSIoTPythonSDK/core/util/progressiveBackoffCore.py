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

 # This class implements the progressive backoff logic for auto-reconnect.
 # It manages the reconnect wait time for the current reconnect, controling
 # when to increase it and when to reset it.

import time
import threading
import logging


class progressiveBackoffCore:
    
    # Logger
    _logger = logging.getLogger(__name__)

    def __init__(self, srcBaseReconnectTimeSecond=1, srcMaximumReconnectTimeSecond=32, srcMinimumConnectTimeSecond=20):
        # The base reconnection time in seconds, default 1
        self._baseReconnectTimeSecond = srcBaseReconnectTimeSecond
        # The maximum reconnection time in seconds, default 32
        self._maximumReconnectTimeSecond = srcMaximumReconnectTimeSecond
        # The minimum time in milliseconds that a connection must be maintained in order to be considered stable
        # Default 20
        self._minimumConnectTimeSecond = srcMinimumConnectTimeSecond
        # Current backOff time in seconds, init to equal to 0
        self._currentBackoffTimeSecond = 1
        # Handler for timer
        self._resetBackoffTimer = None

    # For custom progressiveBackoff timing configuration
    def configTime(self, srcBaseReconnectTimeSecond, srcMaximumReconnectTimeSecond, srcMinimumConnectTimeSecond):
        if  srcBaseReconnectTimeSecond < 0 or srcMaximumReconnectTimeSecond < 0 or srcMinimumConnectTimeSecond < 0:
            self._logger.error("init: Negative time configuration detected.")
            raise ValueError("Negative time configuration detected.")
        if srcBaseReconnectTimeSecond >= srcMinimumConnectTimeSecond:
            self._logger.error("init: Min connect time should be bigger than base reconnect time.")
            raise ValueError("Min connect time should be bigger than base reconnect time.")
        self._baseReconnectTimeSecond = srcBaseReconnectTimeSecond
        self._maximumReconnectTimeSecond = srcMaximumReconnectTimeSecond
        self._minimumConnectTimeSecond = srcMinimumConnectTimeSecond
        self._currentBackoffTimeSecond = 1

    # Block the reconnect logic for _currentBackoffTimeSecond
    # Update the currentBackoffTimeSecond for the next reconnect
    # Cancel the in-waiting timer for resetting backOff time
    # This should get called only when a disconnect/reconnect happens
    def backOff(self):
        self._logger.debug("backOff: current backoff time is: " + str(self._currentBackoffTimeSecond) + " sec.")
        if self._resetBackoffTimer is not None:
            # Cancel the timer
            self._resetBackoffTimer.cancel()
        # Block the reconnect logic
        time.sleep(self._currentBackoffTimeSecond)
        # Update the backoff time
        if self._currentBackoffTimeSecond == 0:
            # This is the first attempt to connect, set it to base
            self._currentBackoffTimeSecond = self._baseReconnectTimeSecond
        else:
            # r_cur = min(2^n*r_base, r_max)
            self._currentBackoffTimeSecond = min(self._maximumReconnectTimeSecond, self._currentBackoffTimeSecond * 2)

    # Start the timer for resetting _currentBackoffTimeSecond
    # Will be cancelled upon calling backOff
    def startStableConnectionTimer(self):
        self._resetBackoffTimer = threading.Timer(self._minimumConnectTimeSecond, self._connectionStableThenResetBackoffTime)
        self._resetBackoffTimer.start()

    def stopStableConnectionTimer(self):
       if self._resetBackoffTimer is not None:
           # Cancel the timer
           self._resetBackoffTimer.cancel()

    # Timer callback to reset _currentBackoffTimeSecond
    # If the connection is stable for longer than _minimumConnectTimeSecond,
    # reset the currentBackoffTimeSecond to _baseReconnectTimeSecond
    def _connectionStableThenResetBackoffTime(self):
        self._logger.debug("stableConnection: Resetting the backoff time to: " + str(self._baseReconnectTimeSecond) + " sec.")
        self._currentBackoffTimeSecond = self._baseReconnectTimeSecond
