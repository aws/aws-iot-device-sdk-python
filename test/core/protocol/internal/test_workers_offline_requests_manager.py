import pytest
from AWSIoTPythonSDK.core.protocol.internal.workers import OfflineRequestsManager
from AWSIoTPythonSDK.core.util.enums import DropBehaviorTypes
from AWSIoTPythonSDK.core.protocol.internal.queues import AppendResults

DEFAULT_QUEUE_SIZE = 3
FAKE_REQUEST_PREFIX = "Fake Request "

def test_has_more():
    offline_requests_manager = OfflineRequestsManager(DEFAULT_QUEUE_SIZE, DropBehaviorTypes.DROP_NEWEST)

    assert not offline_requests_manager.has_more()

    offline_requests_manager.add_one(FAKE_REQUEST_PREFIX + "0")
    assert offline_requests_manager.has_more()


def test_add_more_normal():
    offline_requests_manager = OfflineRequestsManager(DEFAULT_QUEUE_SIZE, DropBehaviorTypes.DROP_NEWEST)
    append_result = offline_requests_manager.add_one(FAKE_REQUEST_PREFIX + "0")

    assert append_result == AppendResults.APPEND_SUCCESS


def test_add_more_full_drop_newest():
    offline_requests_manager = OfflineRequestsManager(DEFAULT_QUEUE_SIZE, DropBehaviorTypes.DROP_NEWEST)
    _overflow_the_queue(offline_requests_manager)
    append_result = offline_requests_manager.add_one(FAKE_REQUEST_PREFIX + "A")

    assert append_result == AppendResults.APPEND_FAILURE_QUEUE_FULL

    next_request = offline_requests_manager.get_next()
    assert next_request == FAKE_REQUEST_PREFIX + "0"


def test_add_more_full_drop_oldest():
    offline_requests_manager = OfflineRequestsManager(DEFAULT_QUEUE_SIZE, DropBehaviorTypes.DROP_OLDEST)
    _overflow_the_queue(offline_requests_manager)
    append_result = offline_requests_manager.add_one(FAKE_REQUEST_PREFIX + "A")

    assert append_result == AppendResults.APPEND_FAILURE_QUEUE_FULL

    next_request = offline_requests_manager.get_next()
    assert next_request == FAKE_REQUEST_PREFIX + "1"


def test_add_more_disabled():
    offline_requests_manager = OfflineRequestsManager(0, DropBehaviorTypes.DROP_NEWEST)
    append_result = offline_requests_manager.add_one(FAKE_REQUEST_PREFIX + "0")

    assert append_result == AppendResults.APPEND_FAILURE_QUEUE_DISABLED


def _overflow_the_queue(offline_requests_manager):
    for i in range(0, DEFAULT_QUEUE_SIZE):
        offline_requests_manager.add_one(FAKE_REQUEST_PREFIX + str(i))


def test_get_next_normal():
    offline_requests_manager = OfflineRequestsManager(DEFAULT_QUEUE_SIZE, DropBehaviorTypes.DROP_NEWEST)
    append_result = offline_requests_manager.add_one(FAKE_REQUEST_PREFIX + "0")

    assert append_result == AppendResults.APPEND_SUCCESS
    assert offline_requests_manager.get_next() is not None


def test_get_next_empty():
    offline_requests_manager = OfflineRequestsManager(DEFAULT_QUEUE_SIZE, DropBehaviorTypes.DROP_NEWEST)
    assert offline_requests_manager.get_next() is None
