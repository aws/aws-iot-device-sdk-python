import pytest
from AWSIoTPythonSDK.core.protocol.internal.workers import SubscriptionManager

DUMMY_TOPIC1 = "topic1"
DUMMY_TOPIC2 = "topic2"


def _dummy_callback(client, user_data, message):
    pass


def test_add_record():
    subscription_manager = SubscriptionManager()
    subscription_manager.add_record(DUMMY_TOPIC1, 1, _dummy_callback, _dummy_callback)

    record_list = subscription_manager.list_records()

    assert len(record_list) == 1

    topic, (qos, message_callback, ack_callback) = record_list[0]
    assert topic == DUMMY_TOPIC1
    assert  qos == 1
    assert message_callback == _dummy_callback
    assert ack_callback == _dummy_callback


def test_remove_record():
    subscription_manager = SubscriptionManager()
    subscription_manager.add_record(DUMMY_TOPIC1, 1, _dummy_callback, _dummy_callback)
    subscription_manager.add_record(DUMMY_TOPIC2, 0, _dummy_callback, _dummy_callback)
    subscription_manager.remove_record(DUMMY_TOPIC1)

    record_list = subscription_manager.list_records()

    assert len(record_list) == 1

    topic, (qos, message_callback, ack_callback) = record_list[0]
    assert topic == DUMMY_TOPIC2
    assert qos == 0
    assert message_callback == _dummy_callback
    assert ack_callback == _dummy_callback
