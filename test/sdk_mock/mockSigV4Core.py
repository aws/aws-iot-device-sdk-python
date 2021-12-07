from AWSIoTPythonSDK.core.protocol.connection.cores import SigV4Core


class mockSigV4Core(SigV4Core):
    _forceNoEnvVar = False

    def setNoEnvVar(self, srcVal):
        self._forceNoEnvVar = srcVal

    def _checkKeyInEnv(self):  # Simulate no Env Var
        if self._forceNoEnvVar:
            return dict()  # Return empty list
        else:
            ret = dict()
            ret["aws_access_key_id"] = "blablablaID"
            ret["aws_secret_access_key"] = "blablablaSecret"
            return ret
