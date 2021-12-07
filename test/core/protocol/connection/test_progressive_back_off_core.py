import time
import AWSIoTPythonSDK.core.protocol.connection.cores as backoff
import pytest


class TestProgressiveBackOffCore():
    def setup_method(self, method):
        self._dummyBackOffCore = backoff.ProgressiveBackOffCore()

    def teardown_method(self, method):
        self._dummyBackOffCore = None

    # Check that current backoff time is one seconds when this is the first time to backoff
    def test_BackoffForTheFirstTime(self):
        assert self._dummyBackOffCore._currentBackoffTimeSecond == 1

    # Check that valid input values for backoff configuration is properly configued
    def test_CustomConfig_ValidInput(self):
        self._dummyBackOffCore.configTime(2, 128, 30)
        assert self._dummyBackOffCore._baseReconnectTimeSecond == 2
        assert self._dummyBackOffCore._maximumReconnectTimeSecond == 128
        assert self._dummyBackOffCore._minimumConnectTimeSecond == 30

    # Check the negative input values will trigger exception
    def test_CustomConfig_NegativeInput(self):
        with pytest.raises(ValueError) as e:
            # _baseReconnectTimeSecond should be greater than zero, otherwise raise exception
            self._dummyBackOffCore.configTime(-10, 128, 30)
        with pytest.raises(ValueError) as e:
            # _maximumReconnectTimeSecond should be greater than zero, otherwise raise exception
            self._dummyBackOffCore.configTime(2, -11, 30)
        with pytest.raises(ValueError) as e:
            # _minimumConnectTimeSecond should be greater than zero, otherwise raise exception
            self._dummyBackOffCore.configTime(2, 128, -12)

    # Check the invalid input values will trigger exception
    def test_CustomConfig_InvalidInput(self):
        with pytest.raises(ValueError) as e:
            # _baseReconnectTimeSecond is larger than _minimumConnectTimeSecond,
            # which is not allowed...
            self._dummyBackOffCore.configTime(200, 128, 30)

    # Check the _currentBackoffTimeSecond increases to twice of the origin after 2nd backoff
    def test_backOffUpdatesCurrentBackoffTime(self):
        self._dummyBackOffCore.configTime(1, 32, 20)
        self._dummyBackOffCore.backOff()  # This is the first backoff, block for 0 seconds
        assert self._dummyBackOffCore._currentBackoffTimeSecond == self._dummyBackOffCore._baseReconnectTimeSecond * 2
        self._dummyBackOffCore.backOff()  # Now progressive backoff calc starts
        assert self._dummyBackOffCore._currentBackoffTimeSecond == self._dummyBackOffCore._baseReconnectTimeSecond * 2 * 2

    # Check that backoff time is reset when connection is stable enough
    def test_backOffResetWhenConnectionIsStable(self):
        self._dummyBackOffCore.configTime(1, 32, 5)
        self._dummyBackOffCore.backOff()  # This is the first backoff, block for 0 seconds
        assert self._dummyBackOffCore._currentBackoffTimeSecond == self._dummyBackOffCore._baseReconnectTimeSecond * 2
        self._dummyBackOffCore.backOff()  # Now progressive backoff calc starts
        assert self._dummyBackOffCore._currentBackoffTimeSecond == self._dummyBackOffCore._baseReconnectTimeSecond * 2 * 2
        # Now simulate a stable connection that exceeds _minimumConnectTimeSecond
        self._dummyBackOffCore.startStableConnectionTimer()  # Called when CONNACK arrives
        time.sleep(self._dummyBackOffCore._minimumConnectTimeSecond + 1)
        # Timer expires, currentBackoffTimeSecond should be reset
        assert self._dummyBackOffCore._currentBackoffTimeSecond == self._dummyBackOffCore._baseReconnectTimeSecond

    # Check that backoff resetting timer is properly cancelled when a disconnect happens immediately
    def test_resetTimerProperlyCancelledOnUnstableConnection(self):
        self._dummyBackOffCore.configTime(1, 32, 5)
        self._dummyBackOffCore.backOff()  # This is the first backoff, block for 0 seconds
        assert self._dummyBackOffCore._currentBackoffTimeSecond == self._dummyBackOffCore._baseReconnectTimeSecond * 2
        # Now simulate an unstable connection that is within _minimumConnectTimeSecond
        self._dummyBackOffCore.startStableConnectionTimer()  # Called when CONNACK arrives
        time.sleep(self._dummyBackOffCore._minimumConnectTimeSecond - 1)
        # Now "disconnect"
        self._dummyBackOffCore.backOff()
        assert self._dummyBackOffCore._currentBackoffTimeSecond == self._dummyBackOffCore._baseReconnectTimeSecond * 2 * 2
