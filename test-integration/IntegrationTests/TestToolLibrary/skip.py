import sys
from TestToolLibrary.MQTTClientManager import CERT_ALPN
from TestToolLibrary.MQTTClientManager import WEBSOCKET

# This module manages the skip policy validation for each test


def skip_when_match(policy, message):
    if policy.validate():
        print(message)
        exit(0)  # Exit the Python interpreter


class Policy(object):

    AND = "and"
    OR = "or"

    def __init__(self):
        self._relations = []

    # Use caps to avoid collision with Python built-in and/or keywords
    def And(self, policy):
        self._relations.append((self.AND, policy))
        return self

    def Or(self, policy):
        self._relations.append((self.OR, policy))
        return self

    def validate(self):
        result = self.validate_impl()

        for element in self._relations:
            operand, policy = element
            if operand == self.AND:
                result = result and policy.validate()
            elif operand == self.OR:
                result = result or policy.validate()
            else:
                raise RuntimeError("Unrecognized operand: " + str(operand))

        return result

    def validate_impl(self):
        raise RuntimeError("Not implemented")


class PythonVersion(Policy):

    HIGHER = "higher"
    LOWER = "lower"
    EQUALS = "equals"

    def __init__(self, actual_version, expected_version, operand):
        Policy.__init__(self)
        self._actual_version = actual_version
        self._expected_version = expected_version
        self._operand = operand

    def validate_impl(self):
        if self._operand == self.LOWER:
            return self._actual_version < self._expected_version
        elif self._operand == self.HIGHER:
            return self._actual_version > self._expected_version
        elif self._operand == self.EQUALS:
            return self._actual_version == self._expected_version
        else:
            raise RuntimeError("Unsupported operand: " + self._operand)


class Python2VersionLowerThan(PythonVersion):

    def __init__(self, version):
        PythonVersion.__init__(self, sys.version_info[:3], version, PythonVersion.LOWER)

    def validate_impl(self):
        return sys.version_info[0] == 2 and PythonVersion.validate_impl(self)


class Python3VersionLowerThan(PythonVersion):

    def __init__(self, version):
        PythonVersion.__init__(self, sys.version_info[:3], version, PythonVersion.LOWER)

    def validate_impl(self):
        return sys.version_info[0] == 3 and PythonVersion.validate_impl(self)


class ModeIs(Policy):

    def __init__(self, actual_mode, expected_mode):
        Policy.__init__(self)
        self._actual_mode = actual_mode
        self._expected_mode = expected_mode

    def validate_impl(self):
        return self._actual_mode == self._expected_mode


class ModeIsALPN(ModeIs):

    def __init__(self, actual_mode):
        ModeIs.__init__(self, actual_mode=actual_mode, expected_mode=CERT_ALPN)


class ModeIsWebSocket(ModeIs):

    def __init__(self, actual_mode):
        ModeIs.__init__(self, actual_mode=actual_mode, expected_mode=WEBSOCKET)
