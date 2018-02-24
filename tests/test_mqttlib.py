import mock
from AWSIoTPythonSDK.MQTTLib import (AWSIoTMQTTClient,
                                     AWSIoTMQTTShadowClient,
                                     MqttCore)


@mock.patch.object(MqttCore, 'disconnect')
@mock.patch.object(MqttCore, 'connect')
def test_awsiotmqtt_shadow_client_connect(mock_connect, mock_disconnect):
    client = AWSIoTMQTTShadowClient("myClientID", useWebsocket=False,
                                    hostName="YOUR.ENDPOINT", portNumber=8883)
    with client:
        client.createShadowHandlerWithName("Bot", True)
    mock_connect.assert_called_once_with(600)
    mock_disconnect.assert_called_once_with()


@mock.patch.object(MqttCore, 'disconnect')
@mock.patch.object(MqttCore, 'connect')
def test_awsiotmqtt_client_connect(mock_connect, mock_disconnect):
    client = AWSIoTMQTTClient("myClientID", useWebsocket=False,
                              keepAliveIntervalSecond=300,
                              hostName="YOUR.ENDPOINT", portNumber=443)
    with client:
        client.publish("myTopic", "myPayload", QoS=0)
    mock_connect.assert_called_once_with(300)
    mock_disconnect.assert_called_once_with()
