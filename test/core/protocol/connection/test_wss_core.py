from test.sdk_mock.mockSecuredWebsocketCore import mockSecuredWebsocketCoreNoRealHandshake
from test.sdk_mock.mockSecuredWebsocketCore import MockSecuredWebSocketCoreNoSocketIO
from test.sdk_mock.mockSecuredWebsocketCore import MockSecuredWebSocketCoreWithRealHandshake
from test.sdk_mock.mockSSLSocket import mockSSLSocket
import struct
import socket
import pytest
try:
    from configparser import ConfigParser  # Python 3+
except ImportError:
    from ConfigParser import ConfigParser


class TestWssCore:

    # Websocket Constants
    _OP_CONTINUATION = 0x0
    _OP_TEXT = 0x1
    _OP_BINARY = 0x2
    _OP_CONNECTION_CLOSE = 0x8
    _OP_PING = 0x9
    _OP_PONG = 0xa

    def _generateStringOfAs(self, length):
        ret = ""
        for i in range(0, length):
            ret += 'a'
        return ret

    def _printByteArray(self, src):
        for i in range(0, len(src)):
            print(hex(src[i]))
        print("")

    def _encodeFrame(self, rawPayload, opCode, FIN=1, RSV1=0, RSV2=0, RSV3=0, masked=1):
        ret = bytearray()
        # FIN+RSV1+RSV2+RSV3
        F = (FIN & 0x01) << 3
        R1 = (RSV1 & 0x01) << 2
        R2 = (RSV2 & 0x01) << 1
        R3 = (RSV3 & 0x01)
        FRRR = (F | R1 | R2 | R3) << 4
        # Op byte
        opByte = FRRR | opCode
        ret.append(opByte)
        # Payload Length bytes
        maskBit = masked
        payloadLength = len(rawPayload)
        if payloadLength <= 125:
            ret.append((maskBit << 7) | payloadLength)
        elif payloadLength <= 0xffff:  # 16-bit unsigned int
            ret.append((maskBit << 7) | 126)
            ret.extend(struct.pack("!H", payloadLength))
        elif payloadLength <= 0x7fffffffffffffff:  # 64-bit unsigned int (most significant bit must be 0)
            ret.append((maskBit << 7) | 127)
            ret.extend(struct.pack("!Q", payloadLength))
        else:  # Overflow
            raise ValueError("Exceeds the maximum number of bytes for a single websocket frame.")
        if maskBit == 1:
            # Mask key bytes
            maskKey = bytearray(b"1234")
            ret.extend(maskKey)
        # Mask the payload
        payloadBytes = bytearray(rawPayload)
        if maskBit == 1:
            for i in range(0, payloadLength):
                payloadBytes[i] ^= maskKey[i % 4]
        ret.extend(payloadBytes)
        # Return the assembled wss frame
        return ret

    def setup_method(self, method):
        self._dummySSLSocket = mockSSLSocket()

    # Wss Handshake
    def test_WssHandshakeTimeout(self):
        self._dummySSLSocket.refreshReadBuffer(bytearray())  # Empty bytes to read from socket
        with pytest.raises(socket.error):
            self._dummySecuredWebsocket = \
                MockSecuredWebSocketCoreNoSocketIO(self._dummySSLSocket, "data.iot.region.amazonaws.com", 1234)

    # Constructor
    def test_InvalidEndpointPattern(self):
        with pytest.raises(ValueError):
            self._dummySecuredWebsocket = MockSecuredWebSocketCoreWithRealHandshake(None, "ThisIsNotAValidIoTEndpoint!", 1234)

    def test_BJSEndpointPattern(self):
        bjsStyleEndpoint = "blablabla.iot.cn-north-1.amazonaws.com.cn"
        unexpectedExceptionMessage = "Invalid endpoint pattern for wss: %s" % bjsStyleEndpoint
        # Garbage wss handshake response to ensure the test code gets passed endpoint pattern validation
        self._dummySSLSocket.refreshReadBuffer(b"GarbageWssHanshakeResponse")
        try:
            self._dummySecuredWebsocket = MockSecuredWebSocketCoreWithRealHandshake(self._dummySSLSocket, bjsStyleEndpoint, 1234)
        except ValueError as e:
            if str(e) == unexpectedExceptionMessage:
                raise AssertionError("Encountered unexpected exception when initializing wss core with BJS style endpoint", e)

    # Wss I/O
    def test_WssReadComplete(self):
        # Config mockSSLSocket to contain a Wss frame
         rawPayload = b"If you can see me, this is good."
         # The payload of this frame will be masked by a randomly-generated mask key
         # securedWebsocketCore should be able to decode it and get the raw payload back
         coolFrame = self._encodeFrame(rawPayload, self._OP_BINARY, FIN=1, RSV1=0, RSV2=0, RSV3=0, masked=0)
         # self._printByteArray(coolFrame)
         self._dummySSLSocket.refreshReadBuffer(coolFrame)
         # Init securedWebsocket with this mockSSLSocket
         self._dummySecuredWebsocket = \
             mockSecuredWebsocketCoreNoRealHandshake(self._dummySSLSocket, "data.iot.region.amazonaws.com", 1234)
         # Read it back:
         readItBack = self._dummySecuredWebsocket.read(len(rawPayload))  # Basically read everything
         assert rawPayload == readItBack

    def test_WssReadFragmented(self):
        rawPayloadFragmented = b"I am designed to be fragmented..."
        # The payload of this frame will be masked by a randomly-generated mask key
        # securedWebsocketCore should be able to decode it and get the raw payload back
        stop1 = 4
        stop2 = 9
        coolFrame = self._encodeFrame(rawPayloadFragmented, self._OP_BINARY, FIN=1, RSV1=0, RSV2=0, RSV3=0, masked=0)
        # self._printByteArray(coolFrame)
        coolFramePart1 = coolFrame[0:stop1]
        coolFramePart2 = coolFrame[stop1:stop2]
        coolFramePart3 = coolFrame[stop2:len(coolFrame)]
        # Config mockSSLSocket to contain a fragmented Wss frame
        self._dummySSLSocket.setReadFragmented()
        self._dummySSLSocket.addReadBufferFragment(coolFramePart1)
        self._dummySSLSocket.addReadBufferFragment(coolFramePart2)
        self._dummySSLSocket.addReadBufferFragment(coolFramePart3)
        self._dummySSLSocket.loadFirstFragmented()
        # In this way, reading from SSLSocket will result in 3 sslError, simulating the situation where data is not ready
        # Init securedWebsocket with this mockSSLSocket
        self._dummySecuredWebsocket = \
            mockSecuredWebsocketCoreNoRealHandshake(self._dummySSLSocket, "data.iot.region.amazonaws.com", 1234)
        # Read it back:
        readItBack = bytearray()
        while len(readItBack) != len(rawPayloadFragmented):
            try:
                # Will be interrupted due to faked socket I/O Error
                # Should be able to read back the complete
                readItBack += self._dummySecuredWebsocket.read(len(rawPayloadFragmented))  # Basically read everything
            except:
                pass
        assert rawPayloadFragmented == readItBack

    def test_WssReadlongFrame(self):
        # Config mockSSLSocket to contain a Wss frame
        rawPayloadLong = bytearray(self._generateStringOfAs(300), 'utf-8')  # 300 bytes of raw payload, will use extended payload length bytes in encoding
        # The payload of this frame will be masked by a randomly-generated mask key
        # securedWebsocketCore should be able to decode it and get the raw payload back
        coolFrame = self._encodeFrame(rawPayloadLong, self._OP_BINARY, FIN=1, RSV1=0, RSV2=0, RSV3=0, masked=0)
        # self._printByteArray(coolFrame)
        self._dummySSLSocket.refreshReadBuffer(coolFrame)
        # Init securedWebsocket with this mockSSLSocket
        self._dummySecuredWebsocket = \
            mockSecuredWebsocketCoreNoRealHandshake(self._dummySSLSocket, "data.iot.region.amazonaws.com", 1234)
        # Read it back:
        readItBack = self._dummySecuredWebsocket.read(len(rawPayloadLong))  # Basically read everything
        assert rawPayloadLong == readItBack

    def test_WssReadReallylongFrame(self):
        # Config mockSSLSocket to contain a Wss frame
        # Maximum allowed length of a wss payload is greater than maximum allowed payload length of a MQTT payload
        rawPayloadLong = bytearray(self._generateStringOfAs(0xffff + 3), 'utf-8')  #  0xffff + 3 bytes of raw payload, will use extended payload length bytes in encoding
        # The payload of this frame will be masked by a randomly-generated mask key
        # securedWebsocketCore should be able to decode it and get the raw payload back
        coolFrame = self._encodeFrame(rawPayloadLong, self._OP_BINARY, FIN=1, RSV1=0, RSV2=0, RSV3=0, masked=0)
        # self._printByteArray(coolFrame)
        self._dummySSLSocket.refreshReadBuffer(coolFrame)
        # Init securedWebsocket with this mockSSLSocket
        self._dummySecuredWebsocket = \
            mockSecuredWebsocketCoreNoRealHandshake(self._dummySSLSocket, "data.iot.region.amazonaws.com", 1234)
        # Read it back:
        readItBack = self._dummySecuredWebsocket.read(len(rawPayloadLong))  # Basically read everything
        assert rawPayloadLong == readItBack

    def test_WssWriteComplete(self):
        ToBeWritten = b"Write me to the cloud."
        # Init securedWebsocket with this mockSSLSocket
        self._dummySecuredWebsocket = \
            mockSecuredWebsocketCoreNoRealHandshake(self._dummySSLSocket, "data.iot.region.amazonaws.com", 1234)
        # Fire the write op
        self._dummySecuredWebsocket.write(ToBeWritten)
        ans = self._encodeFrame(ToBeWritten, self._OP_BINARY, FIN=1, RSV1=0, RSV2=0, RSV3=0, masked=1)
        # self._printByteArray(ans)
        assert ans == self._dummySSLSocket.getWriteBuffer()

    def test_WssWriteFragmented(self):
        ToBeWritten = b"Write me to the cloud again."
        # Configure SSLSocket to perform interrupted write op
        self._dummySSLSocket.setFlipWriteError()
        # Init securedWebsocket with this mockSSLSocket
        self._dummySecuredWebsocket = \
            mockSecuredWebsocketCoreNoRealHandshake(self._dummySSLSocket, "data.iot.region.amazonaws.com", 1234)
        # Fire the write op
        with pytest.raises(socket.error) as e:
            self._dummySecuredWebsocket.write(ToBeWritten)
        assert "Not ready for write op" == e.value.strerror
        lengthWritten = self._dummySecuredWebsocket.write(ToBeWritten)
        ans = self._encodeFrame(ToBeWritten, self._OP_BINARY, FIN=1, RSV1=0, RSV2=0, RSV3=0, masked=1)
        assert lengthWritten == len(ToBeWritten)
        assert ans == self._dummySSLSocket.getWriteBuffer()

    # Wss Client Behavior
    def test_ClientClosesConnectionIfServerResponseIsMasked(self):
        ToBeWritten = b"I am designed to be masked."
        maskedFrame = self._encodeFrame(ToBeWritten, self._OP_BINARY, FIN=1, RSV1=0, RSV2=0, RSV3=0, masked=1)
        self._dummySSLSocket.refreshReadBuffer(maskedFrame)
        # Init securedWebsocket with this mockSSLSocket
        self._dummySecuredWebsocket = \
            mockSecuredWebsocketCoreNoRealHandshake(self._dummySSLSocket, "data.iot.region.amazonaws.com", 1234)
        # Now read it back
        with pytest.raises(socket.error) as e:
            self._dummySecuredWebsocket.read(len(ToBeWritten))
        assert "Server response masked, closing connection and try again." == e.value.strerror
        # Verify that a closing frame from the client is on its way
        closingFrame = self._encodeFrame(b"", self._OP_CONNECTION_CLOSE, FIN=1, RSV1=0, RSV2=0, RSV3=0, masked=1)
        assert closingFrame == self._dummySSLSocket.getWriteBuffer()

    def test_ClientClosesConnectionIfServerResponseHasReserveBitsSet(self):
        ToBeWritten = b"I am designed to be masked."
        maskedFrame = self._encodeFrame(ToBeWritten, self._OP_BINARY, FIN=1, RSV1=1, RSV2=0, RSV3=0, masked=1)
        self._dummySSLSocket.refreshReadBuffer(maskedFrame)
        # Init securedWebsocket with this mockSSLSocket
        self._dummySecuredWebsocket = \
            mockSecuredWebsocketCoreNoRealHandshake(self._dummySSLSocket, "data.iot.region.amazonaws.com", 1234)
        # Now read it back
        with pytest.raises(socket.error) as e:
            self._dummySecuredWebsocket.read(len(ToBeWritten))
        assert "RSV bits set with NO negotiated extensions." == e.value.strerror
        # Verify that a closing frame from the client is on its way
        closingFrame = self._encodeFrame(b"", self._OP_CONNECTION_CLOSE, FIN=1, RSV1=0, RSV2=0, RSV3=0, masked=1)
        assert closingFrame == self._dummySSLSocket.getWriteBuffer()

    def test_ClientSendsPONGIfReceivedPING(self):
        PINGFrame = self._encodeFrame(b"", self._OP_PING, FIN=1, RSV1=0, RSV2=0, RSV3=0, masked=0)
        self._dummySSLSocket.refreshReadBuffer(PINGFrame)
        # Init securedWebsocket with this mockSSLSocket
        self._dummySecuredWebsocket = \
            mockSecuredWebsocketCoreNoRealHandshake(self._dummySSLSocket, "data.iot.region.amazonaws.com", 1234)
        # Now read it back, this must be in the next round of paho MQTT packet reading
        # Should fail since we only have a PING to read, it never contains a valid MQTT payload
        with pytest.raises(socket.error) as e:
            self._dummySecuredWebsocket.read(5)
        assert "Not a complete MQTT packet payload within this wss frame." == e.value.strerror
        # Verify that PONG frame from the client is on its way
        PONGFrame = self._encodeFrame(b"", self._OP_PONG, FIN=1, RSV1=0, RSV2=0, RSV3=0, masked=1)
        assert PONGFrame == self._dummySSLSocket.getWriteBuffer()

