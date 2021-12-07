from AWSIoTPythonSDK.core.protocol.internal.clients import ClientStatus
from AWSIoTPythonSDK.core.protocol.internal.clients import ClientStatusContainer


class TestClientsClientStatus:

    def setup_method(self, test_method):
        self.client_status = ClientStatusContainer()

    def test_set_client_status(self):
        assert self.client_status.get_status() == ClientStatus.IDLE  # Client status should start with IDLE
        self._set_client_status_and_verify(ClientStatus.ABNORMAL_DISCONNECT)
        self._set_client_status_and_verify(ClientStatus.CONNECT)
        self._set_client_status_and_verify(ClientStatus.RESUBSCRIBE)
        self._set_client_status_and_verify(ClientStatus.DRAINING)
        self._set_client_status_and_verify(ClientStatus.STABLE)

    def test_client_status_does_not_change_unless_user_connect_after_user_disconnect(self):
        self.client_status.set_status(ClientStatus.USER_DISCONNECT)
        self._set_client_status_and_verify(ClientStatus.ABNORMAL_DISCONNECT, ClientStatus.USER_DISCONNECT)
        self._set_client_status_and_verify(ClientStatus.RESUBSCRIBE, ClientStatus.USER_DISCONNECT)
        self._set_client_status_and_verify(ClientStatus.DRAINING, ClientStatus.USER_DISCONNECT)
        self._set_client_status_and_verify(ClientStatus.STABLE, ClientStatus.USER_DISCONNECT)
        self._set_client_status_and_verify(ClientStatus.CONNECT)

    def _set_client_status_and_verify(self, set_client_status_type, verify_client_status_type=None):
        self.client_status.set_status(set_client_status_type)
        if verify_client_status_type:
            assert self.client_status.get_status() == verify_client_status_type
        else:
            assert self.client_status.get_status() == set_client_status_type
