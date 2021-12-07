from AWSIoTPythonSDK.core.protocol.mqtt_core import MqttCore
from AWSIoTPythonSDK.core.shadow.shadowManager import shadowManager
try:
    from mock import MagicMock
except:
    from unittest.mock import MagicMock
try:
    from mock import NonCallableMagicMock
except:
    from unittest.mock import NonCallableMagicMock
try:
    from mock import call
except:
    from unittest.mock import call
import pytest


DUMMY_SHADOW_NAME = "CoolShadow"
DUMMY_PAYLOAD = "{}"

OP_SHADOW_GET = "get"
OP_SHADOW_UPDATE = "update"
OP_SHADOW_DELETE = "delete"
OP_SHADOW_DELTA = "delta"
OP_SHADOW_TROUBLE_MAKER = "not_a_valid_shadow_aciton_name"

DUMMY_SHADOW_TOPIC_PREFIX = "$aws/things/" + DUMMY_SHADOW_NAME + "/shadow/"
DUMMY_SHADOW_TOPIC_GET = DUMMY_SHADOW_TOPIC_PREFIX + "get"
DUMMY_SHADOW_TOPIC_GET_ACCEPTED = DUMMY_SHADOW_TOPIC_GET + "/accepted"
DUMMY_SHADOW_TOPIC_GET_REJECTED = DUMMY_SHADOW_TOPIC_GET + "/rejected"
DUMMY_SHADOW_TOPIC_UPDATE = DUMMY_SHADOW_TOPIC_PREFIX + "update"
DUMMY_SHADOW_TOPIC_UPDATE_ACCEPTED = DUMMY_SHADOW_TOPIC_UPDATE + "/accepted"
DUMMY_SHADOW_TOPIC_UPDATE_REJECTED = DUMMY_SHADOW_TOPIC_UPDATE + "/rejected"
DUMMY_SHADOW_TOPIC_UPDATE_DELTA = DUMMY_SHADOW_TOPIC_UPDATE + "/delta"
DUMMY_SHADOW_TOPIC_DELETE = DUMMY_SHADOW_TOPIC_PREFIX + "delete"
DUMMY_SHADOW_TOPIC_DELETE_ACCEPTED = DUMMY_SHADOW_TOPIC_DELETE + "/accepted"
DUMMY_SHADOW_TOPIC_DELETE_REJECTED = DUMMY_SHADOW_TOPIC_DELETE + "/rejected"


class TestShadowManager:

    def setup_method(self, test_method):
        self.mock_mqtt_core = MagicMock(spec=MqttCore)
        self.shadow_manager = shadowManager(self.mock_mqtt_core)

    def test_basic_shadow_publish(self):
        self.shadow_manager.basicShadowPublish(DUMMY_SHADOW_NAME, OP_SHADOW_GET, DUMMY_PAYLOAD)
        self.shadow_manager.basicShadowPublish(DUMMY_SHADOW_NAME, OP_SHADOW_UPDATE, DUMMY_PAYLOAD)
        self.shadow_manager.basicShadowPublish(DUMMY_SHADOW_NAME, OP_SHADOW_DELETE, DUMMY_PAYLOAD)
        self.mock_mqtt_core.publish.assert_has_calls([call(DUMMY_SHADOW_TOPIC_GET, DUMMY_PAYLOAD, 0, False),
                                                      call(DUMMY_SHADOW_TOPIC_UPDATE, DUMMY_PAYLOAD, 0, False),
                                                      call(DUMMY_SHADOW_TOPIC_DELETE, DUMMY_PAYLOAD, 0, False)])

    def test_basic_shadow_subscribe(self):
        callback = NonCallableMagicMock()
        self.shadow_manager.basicShadowSubscribe(DUMMY_SHADOW_NAME, OP_SHADOW_GET, callback)
        self.shadow_manager.basicShadowSubscribe(DUMMY_SHADOW_NAME, OP_SHADOW_UPDATE, callback)
        self.shadow_manager.basicShadowSubscribe(DUMMY_SHADOW_NAME, OP_SHADOW_DELETE, callback)
        self.shadow_manager.basicShadowSubscribe(DUMMY_SHADOW_NAME, OP_SHADOW_DELTA, callback)
        self.mock_mqtt_core.subscribe.assert_has_calls([call(DUMMY_SHADOW_TOPIC_GET_ACCEPTED, 0, callback),
                                                        call(DUMMY_SHADOW_TOPIC_GET_REJECTED, 0, callback),
                                                        call(DUMMY_SHADOW_TOPIC_UPDATE_ACCEPTED, 0, callback),
                                                        call(DUMMY_SHADOW_TOPIC_UPDATE_REJECTED, 0, callback),
                                                        call(DUMMY_SHADOW_TOPIC_DELETE_ACCEPTED, 0, callback),
                                                        call(DUMMY_SHADOW_TOPIC_DELETE_REJECTED, 0, callback),
                                                        call(DUMMY_SHADOW_TOPIC_UPDATE_DELTA, 0, callback)])

    def test_basic_shadow_unsubscribe(self):
        self.shadow_manager.basicShadowUnsubscribe(DUMMY_SHADOW_NAME, OP_SHADOW_GET)
        self.shadow_manager.basicShadowUnsubscribe(DUMMY_SHADOW_NAME, OP_SHADOW_UPDATE)
        self.shadow_manager.basicShadowUnsubscribe(DUMMY_SHADOW_NAME, OP_SHADOW_DELETE)
        self.shadow_manager.basicShadowUnsubscribe(DUMMY_SHADOW_NAME, OP_SHADOW_DELTA)
        self.mock_mqtt_core.unsubscribe.assert_has_calls([call(DUMMY_SHADOW_TOPIC_GET_ACCEPTED),
                                                          call(DUMMY_SHADOW_TOPIC_GET_REJECTED),
                                                          call(DUMMY_SHADOW_TOPIC_UPDATE_ACCEPTED),
                                                          call(DUMMY_SHADOW_TOPIC_UPDATE_REJECTED),
                                                          call(DUMMY_SHADOW_TOPIC_DELETE_ACCEPTED),
                                                          call(DUMMY_SHADOW_TOPIC_DELETE_REJECTED),
                                                          call(DUMMY_SHADOW_TOPIC_UPDATE_DELTA)])

    def test_unsupported_shadow_action_name(self):
        with pytest.raises(TypeError):
            self.shadow_manager.basicShadowUnsubscribe(DUMMY_SHADOW_NAME, OP_SHADOW_TROUBLE_MAKER)
