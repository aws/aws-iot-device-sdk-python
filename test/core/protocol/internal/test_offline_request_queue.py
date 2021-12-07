import AWSIoTPythonSDK.core.protocol.internal.queues as Q
from AWSIoTPythonSDK.core.protocol.internal.queues import AppendResults
import pytest


class TestOfflineRequestQueue():

    # Check that invalid input types are filtered out on initialization
    def test_InvalidTypeInit(self):
        with pytest.raises(TypeError):
            Q.OfflineRequestQueue(1.7, 0)
        with pytest.raises(TypeError):
            Q.OfflineRequestQueue(0, 1.7)

    # Check that elements can be append to a normal finite queue
    def test_NormalAppend(self):
        coolQueue = Q.OfflineRequestQueue(20, 1)
        numberOfMessages = 5
        answer = list(range(0, numberOfMessages))
        for i in range(0, numberOfMessages):
            coolQueue.append(i)
        assert answer == coolQueue

    # Check that new elements are dropped for DROPNEWEST configuration
    def test_DropNewest(self):
        coolQueue = Q.OfflineRequestQueue(3, 1)  # Queueing section: 3, Response section: 1, DropNewest
        numberOfMessages = 10
        answer = [0, 1, 2]  # '0', '1' and '2' are stored, others are dropped.
        fullCount = 0
        for i in range(0, numberOfMessages):
            if coolQueue.append(i) == AppendResults.APPEND_FAILURE_QUEUE_FULL:
                fullCount += 1
        assert answer == coolQueue
        assert 7 == fullCount

    # Check that old elements are dropped for DROPOLDEST configuration
    def test_DropOldest(self):
        coolQueue = Q.OfflineRequestQueue(3, 0)
        numberOfMessages = 10
        answer = [7, 8, 9]  # '7', '8' and '9' are stored, others (older ones) are dropped.
        fullCount = 0
        for i in range(0, numberOfMessages):
            if coolQueue.append(i) == AppendResults.APPEND_FAILURE_QUEUE_FULL:
                fullCount += 1
        assert answer == coolQueue
        assert 7 == fullCount

    # Check infinite queue
    def test_Infinite(self):
        coolQueue = Q.OfflineRequestQueue(-100, 1)
        numberOfMessages = 10000
        answer = list(range(0, numberOfMessages))
        for i in range(0, numberOfMessages):
            coolQueue.append(i)
        assert answer == coolQueue  # Nothing should be dropped since response section is infinite

    # Check disabled queue
    def test_Disabled(self):
        coolQueue = Q.OfflineRequestQueue(0, 1)
        numberOfMessages = 10
        answer = list()
        disableFailureCount = 0
        for i in range(0, numberOfMessages):
            if coolQueue.append(i) == AppendResults.APPEND_FAILURE_QUEUE_DISABLED:
                disableFailureCount += 1
        assert answer == coolQueue  # Nothing should be appended since the queue is disabled
        assert numberOfMessages == disableFailureCount
