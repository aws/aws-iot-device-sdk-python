from test.sdk_mock.mockSigV4Core import mockSigV4Core
from AWSIoTPythonSDK.core.protocol.connection.cores import SecuredWebSocketCore


class mockSecuredWebsocketCoreNoRealHandshake(SecuredWebSocketCore):
    def _createSigV4Core(self):
        ret = mockSigV4Core()
        ret.setNoEnvVar(False)  # Always has Env Var
        return ret

    def _handShake(self, hostAddress, portNumber):  # Override to pass handshake
        pass

    def _generateMaskKey(self):
        return bytearray(str("1234"), 'utf-8')  # Arbitrary mask key for testing


class MockSecuredWebSocketCoreNoSocketIO(SecuredWebSocketCore):
    def _createSigV4Core(self):
        ret = mockSigV4Core()
        ret.setNoEnvVar(False)  # Always has Env Var
        return ret

    def _generateMaskKey(self):
        return bytearray(str("1234"), 'utf-8')  # Arbitrary mask key for testing

    def _getTimeoutSec(self):
        return 3  # 3 sec to time out from waiting for handshake response for testing


class MockSecuredWebSocketCoreWithRealHandshake(SecuredWebSocketCore):
    def _createSigV4Core(self):
        ret = mockSigV4Core()
        ret.setNoEnvVar(False)  # Always has Env Var
        return ret
