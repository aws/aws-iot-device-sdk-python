'''
/*
 * Copyright 2010-2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *  http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */
 '''

# This class implements a simple secured websocket client
# with support for websocket handshake, frame encoding/decoding
# and Python paho-mqtt compatible low level socket I/O
# By now, we assume that for each MQTT packet over websocket,
# it will be wrapped into ONE websocket frame. Fragments of
# MQTT packet should be ignored.

import os
import sys
import ssl
import struct
import socket
import base64
import hashlib
from AWSIoTPythonSDK.core.util.sigV4Core import sigV4Core
from AWSIoTPythonSDK.exception.AWSIoTExceptions import wssNoKeyInEnvironmentError
from AWSIoTPythonSDK.exception.AWSIoTExceptions import wssHandShakeError

# This is an internal class that buffers the incoming bytes into an
# internal buffer until it gets the full desired length of bytes.
# At that time, this bufferedReader will be reset.
# *Error handling:
# For retry errors (ssl.SSL_ERROR_WANT_READ, ssl.SSL_ERROR_WANT_WRITE, EAGAIN),
# leave them to the paho _packet_read for further handling (ignored and try
# again when data is available.
# For other errors, leave them to the paho _packet_read for error reporting.


class _bufferedReader:
    _sslSocket = None
    _internalBuffer = None
    _remainedLength = -1
    _bufferingInProgress = False

    def __init__(self, sslSocket):
        self._sslSocket = sslSocket
        self._internalBuffer = bytearray()
        self._bufferingInProgress = False

    def _reset(self):
        self._internalBuffer = bytearray()
        self._remainedLength = -1
        self._bufferingInProgress = False

    def read(self, numberOfBytesToBeBuffered):
        if not self._bufferingInProgress:  # If last read is completed...
            self._remainedLength = numberOfBytesToBeBuffered
            self._bufferingInProgress = True  # Now we start buffering a new length of bytes

        while self._remainedLength > 0:  # Read in a loop, always try to read in the remained length
            # If the data is temporarily not available, socket.error will be raised and catched by paho
            dataChunk = self._sslSocket.read(self._remainedLength)
            self._internalBuffer.extend(dataChunk)  # Buffer the data
            self._remainedLength -= len(dataChunk)  # Update the remained length

        # The requested length of bytes is buffered, recover the context and return it
        # Otherwise error should be raised
        ret = self._internalBuffer
        self._reset()
        return ret  # This should always be bytearray

# This is the internal class that sends requested data out chunk by chunk according
# to the availablity of the socket write operation. If the requested bytes of data
# (after encoding) needs to be sent out in separate socket write operations (most
# probably be interrupted by the error socket.error (errno = ssl.SSL_ERROR_WANT_WRITE).)
# , the write pointer is stored to ensure that the continued bytes will be sent next
# time this function gets called.
# *Error handling:
# For retry errors (ssl.SSL_ERROR_WANT_READ, ssl.SSL_ERROR_WANT_WRITE, EAGAIN),
# leave them to the paho _packet_read for further handling (ignored and try
# again when data is available.
# For other errors, leave them to the paho _packet_read for error reporting.


class _bufferedWriter:
    _sslSocket = None
    _internalBuffer = None
    _writingInProgress = False
    _requestedDataLength = -1

    def __init__(self, sslSocket):
        self._sslSocket = sslSocket
        self._internalBuffer = bytearray()
        self._writingInProgress = False
        self._requestedDataLength = -1

    def _reset(self):
        self._internalBuffer = bytearray()
        self._writingInProgress = False
        self._requestedDataLength = -1

    # Input data for this function needs to be an encoded wss frame
    # Always request for packet[pos=0:] (raw MQTT data)
    def write(self, encodedData, payloadLength):
    	# encodedData should always be bytearray
        # Check if we have a frame that is partially sent
        if not self._writingInProgress:
            self._internalBuffer = encodedData
            self._writingInProgress = True
            self._requestedDataLength = payloadLength
        # Now, write as much as we can
        lengthWritten = self._sslSocket.write(self._internalBuffer)
        self._internalBuffer = self._internalBuffer[lengthWritten:]
        # This MQTT packet has been sent out in a wss frame, completely
        if len(self._internalBuffer) == 0:
            ret = self._requestedDataLength
            self._reset()
            return ret
        # This socket write is half-baked...
        else:
            return 0  # Ensure that the 'pos' inside the MQTT packet never moves since we have not finished the transmission of this encoded frame


class securedWebsocketCore:
    # Websocket Constants
    _OP_CONTINUATION = 0x0
    _OP_TEXT = 0x1
    _OP_BINARY = 0x2
    _OP_CONNECTION_CLOSE = 0x8
    _OP_PING = 0x9
    _OP_PONG = 0xa
    # Websocket Connect Status
    _WebsocketConnectInit = -1
    _WebsocketDisconnected = 1

    def __init__(self, socket, hostAddress, portNumber, AWSAccessKeyID="", AWSSecretAccessKey="", AWSSessionToken=""):
        self._connectStatus = self._WebsocketConnectInit
        # Handlers
        self._sslSocket = socket
        self._sigV4Handler = self._createSigV4Core()
        self._sigV4Handler.setIAMCredentials(AWSAccessKeyID, AWSSecretAccessKey, AWSSessionToken)
        # Endpoint Info
        self._hostAddress = hostAddress
        self._portNumber = portNumber
        # Section Flags
        self._hasOpByte = False
        self._hasPayloadLengthFirst = False
        self._hasPayloadLengthExtended = False
        self._hasMaskKey = False
        self._hasPayload = False
        # Properties for current websocket frame
        self._isFIN = False
        self._RSVBits = None
        self._opCode = None
        self._needMaskKey = False
        self._payloadLengthBytesLength = 1
        self._payloadLength = 0
        self._maskKey = None
        self._payloadDataBuffer = bytearray()  # Once the whole wss connection is lost, there is no need to keep the buffered payload
        try:
            self._handShake(hostAddress, portNumber)
        except wssNoKeyInEnvironmentError:  # Handle SigV4 signing and websocket handshaking errors
            raise ValueError("No Access Key/KeyID Error")
        except wssHandShakeError:
            raise ValueError("Websocket Handshake Error")
        # Now we have a socket with secured websocket...
        self._bufferedReader = _bufferedReader(self._sslSocket)
        self._bufferedWriter = _bufferedWriter(self._sslSocket)

    def _createSigV4Core(self):
        return sigV4Core()

    def _generateMaskKey(self):
        return bytearray(os.urandom(4))
        # os.urandom returns ascii str in 2.x, converted to bytearray
        # os.urandom returns bytes in 3.x, converted to bytearray

    def _reset(self):  # Reset the context for wss frame reception
        # Control info
        self._hasOpByte = False
        self._hasPayloadLengthFirst = False
        self._hasPayloadLengthExtended = False
        self._hasMaskKey = False
        self._hasPayload = False
        # Frame Info
        self._isFIN = False
        self._RSVBits = None
        self._opCode = None
        self._needMaskKey = False
        self._payloadLengthBytesLength = 1
        self._payloadLength = 0
        self._maskKey = None
        # Never reset the payloadData since we might have fragmented MQTT data from the pervious frame

    def _generateWSSKey(self):
        return base64.b64encode(os.urandom(128))  # Bytes

    def _verifyWSSResponse(self, response, clientKey):
        # Check if it is a 101 response
        rawResponse = response.strip().lower()
        if b"101 switching protocols" not in rawResponse or b"upgrade: websocket" not in rawResponse or b"connection: upgrade" not in rawResponse:
            return False
        # Parse out the sec-websocket-accept
        WSSAcceptKeyIndex = response.strip().index(b"sec-websocket-accept: ") + len(b"sec-websocket-accept: ")
        rawSecWebSocketAccept = response.strip()[WSSAcceptKeyIndex:].split(b"\r\n")[0].strip()
        # Verify the WSSAcceptKey
        return self._verifyWSSAcceptKey(rawSecWebSocketAccept, clientKey)

    def _verifyWSSAcceptKey(self, srcAcceptKey, clientKey):
        GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        verifyServerAcceptKey = base64.b64encode((hashlib.sha1(clientKey + GUID)).digest())  # Bytes
        return srcAcceptKey == verifyServerAcceptKey

    def _handShake(self, hostAddress, portNumber):
        CRLF = "\r\n"
        hostAddressChunks = hostAddress.split('.')  # <randomString>.iot.<region>.amazonaws.com
        region = hostAddressChunks[2]  # XXXX.<region>.beta
        signedURL = self._sigV4Handler.createWebsocketEndpoint(hostAddress, portNumber, region, "GET", "iotdata", "/mqtt")
        if signedURL == "":
            raise wssNoKeyInEnvironmentError()
        # Now we got a signedURL
        path = signedURL[signedURL.index("/mqtt"):]
        # Assemble HTTP request headers
        Method = "GET " + path + " HTTP/1.1" + CRLF
        Host = "Host: " + hostAddress + CRLF
        Connection = "Connection: " + "Upgrade" + CRLF
        Upgrade = "Upgrade: " + "websocket" + CRLF
        secWebSocketVersion = "Sec-WebSocket-Version: " + "13" + CRLF
        rawSecWebSocketKey = self._generateWSSKey()  # Bytes
        secWebSocketKey = "sec-websocket-key: " + rawSecWebSocketKey.decode('utf-8') + CRLF  # Should be randomly generated...
        secWebSocketProtocol = "Sec-WebSocket-Protocol: " + "mqttv3.1" + CRLF
        secWebSocketExtensions = "Sec-WebSocket-Extensions: " + "permessage-deflate; client_max_window_bits" + CRLF
        # Send the HTTP request
        # Ensure that we are sending bytes, not by any chance unicode string
        handshakeBytes = Method + Host + Connection + Upgrade + secWebSocketVersion + secWebSocketProtocol + secWebSocketExtensions + secWebSocketKey + CRLF
        handshakeBytes = handshakeBytes.encode('utf-8')
        self._sslSocket.write(handshakeBytes)
        # Read it back (Non-blocking socket)
        # Do we need a timeout here?
        wssHandshakeResponse = bytearray()
        while len(wssHandshakeResponse) == 0:
            try:
                wssHandshakeResponse += self._sslSocket.read(1024)  # Response is always less than 1024 bytes
            except socket.error as err:
                if err.errno == ssl.SSL_ERROR_WANT_READ or err.errno == ssl.SSL_ERROR_WANT_WRITE:
                    pass
        # Verify response
        # Now both wssHandshakeResponse and rawSecWebSocketKey are byte strings
        if not self._verifyWSSResponse(wssHandshakeResponse, rawSecWebSocketKey):
            raise wssHandShakeError()
        else:
            pass

    # Used to create a single wss frame
    # Assume that the maximum length of a MQTT packet never exceeds the maximum length
    # for a wss frame. Therefore, the FIN bit for the encoded frame will always be 1.
    # Frames are encoded as BINARY frames.
    def _encodeFrame(self, rawPayload, opCode, masked=1):
        ret = bytearray()
        # Op byte
        opByte = 0x80 | opCode  # Always a FIN, no RSV bits
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
            maskKey = self._generateMaskKey()
            ret.extend(maskKey)
        # Mask the payload
        payloadBytes = bytearray(rawPayload)
        if maskBit == 1:
            for i in range(0, payloadLength):
                payloadBytes[i] ^= maskKey[i % 4]
        ret.extend(payloadBytes)
        # Return the assembled wss frame
        return ret

    # Used for the wss client to close a wss connection
    # Create and send a masked wss closing frame
    def _closeWssConnection(self):
        # Frames sent from client to server must be masked
        self._sslSocket.write(self._encodeFrame(b"", self._OP_CONNECTION_CLOSE, masked=1))

    # Used for the wss client to respond to a wss PING from server
    # Create and send a masked PONG frame
    def _sendPONG(self):
        # Frames sent from client to server must be masked
        self._sslSocket.write(self._encodeFrame(b"", self._OP_PONG, masked=1))

    # Override sslSocket read. Always read from the wss internal payload buffer, which
    # contains the masked MQTT packet. This read will decode ONE wss frame every time
    # and load in the payload for MQTT _packet_read. At any time, MQTT _packet_read
    # should be able to read a complete MQTT packet from the payload (buffered per wss
    # frame payload). If the MQTT packet is break into separate wss frames, different
    # chunks will be buffered in separate frames and MQTT _packet_read will not be able
    # to collect a complete MQTT packet to operate on until the necessary payload is
    # fully buffered.
    # If the requested number of bytes are not available, SSL_ERROR_WANT_READ will be
    # raised to trigger another call of _packet_read when the data is available again.
    def read(self, numberOfBytes):
        # Check if we have enough data for paho
        # _payloadDataBuffer will not be empty ony when the payload of a new wss frame
        # has been unmasked.
        if len(self._payloadDataBuffer) >= numberOfBytes:
            ret = self._payloadDataBuffer[0:numberOfBytes]
            self._payloadDataBuffer = self._payloadDataBuffer[numberOfBytes:]
            # struct.unpack(fmt, string) # Py2.x
            # struct.unpack(fmt, buffer) # Py3.x
            # Here ret is always in bytes (buffer interface)
            if sys.version_info[0] < 3:  # Py2.x
            	ret = str(ret)
            return ret
        # Emmm, We don't. Try to buffer from the socket (It's a new wss frame).
        if not self._hasOpByte:  # Check if we need to buffer OpByte
            opByte = self._bufferedReader.read(1)
            self._isFIN = (opByte[0] & 0x80) == 0x80
            self._RSVBits = (opByte[0] & 0x70)
            self._opCode = (opByte[0] & 0x0f)
            self._hasOpByte = True  # Finished buffering opByte
            # Check if any of the RSV bits are set, if so, close the connection
            # since client never sends negotiated extensions
            if self._RSVBits != 0x0:
                self._closeWssConnection()
                self._connectStatus = self._WebsocketDisconnected
                self._payloadDataBuffer = bytearray()
                raise socket.error(ssl.SSL_ERROR_WANT_READ, "RSV bits set with NO negotiated extensions.")
        if not self._hasPayloadLengthFirst:  # Check if we need to buffer First Payload Length byte
            payloadLengthFirst = self._bufferedReader.read(1)
            self._hasPayloadLengthFirst = True  # Finished buffering first byte of payload length
            self._needMaskKey = (payloadLengthFirst[0] & 0x80) == 0x80
            payloadLengthFirstByteArray = bytearray()
            payloadLengthFirstByteArray.extend(payloadLengthFirst)
            self._payloadLength = (payloadLengthFirstByteArray[0] & 0x7f)

            if self._payloadLength == 126:
                self._payloadLengthBytesLength = 2
                self._hasPayloadLengthExtended = False  # Force to buffer the extended
            elif self._payloadLength == 127:
                self._payloadLengthBytesLength = 8
                self._hasPayloadLengthExtended = False  # Force to buffer the extended
            else:  # _payloadLength <= 125:
                self._hasPayloadLengthExtended = True  # No need to buffer extended payload length
        if not self._hasPayloadLengthExtended:  # Check if we need to buffer Extended Payload Length bytes
            payloadLengthExtended = self._bufferedReader.read(self._payloadLengthBytesLength)
            self._hasPayloadLengthExtended = True
            if sys.version_info[0] < 3:
            	payloadLengthExtended = str(payloadLengthExtended)
            if self._payloadLengthBytesLength == 2:
	            self._payloadLength = struct.unpack("!H", payloadLengthExtended)[0]
            else:  # _payloadLengthBytesLength == 8
                self._payloadLength = struct.unpack("!Q", payloadLengthExtended)[0]

        if self._needMaskKey:  # Response from server is masked, close the connection
            self._closeWssConnection()
            self._connectStatus = self._WebsocketDisconnected
            self._payloadDataBuffer = bytearray()
            raise socket.error(ssl.SSL_ERROR_WANT_READ, "Server response masked, closing connection and try again.")

        if not self._hasPayload:  # Check if we need to buffer the payload
            payloadForThisFrame = self._bufferedReader.read(self._payloadLength)
            self._hasPayload = True
            # Client side should never received a masked packet from the server side
            # Unmask it as needed
            #if self._needMaskKey:
            #    for i in range(0, self._payloadLength):
            #        payloadForThisFrame[i] ^= self._maskKey[i % 4]
            # Append it to the internal payload buffer
            self._payloadDataBuffer.extend(payloadForThisFrame)
        # Now we have the complete wss frame, reset the context
        # Check to see if it is a wss closing frame
        if self._opCode == self._OP_CONNECTION_CLOSE:
            self._connectStatus = self._WebsocketDisconnected
            self._payloadDataBuffer = bytearray()  # Ensure that once the wss closing frame comes, we have nothing to read and start all over again
        # Check to see if it is a wss PING frame
        if self._opCode == self._OP_PING:
            self._sendPONG()  # Nothing more to do here, if the transmission of the last wssMQTT packet is not finished, it will continue
        self._reset()
        # Check again if we have enough data for paho
        if len(self._payloadDataBuffer) >= numberOfBytes:
            ret = self._payloadDataBuffer[0:numberOfBytes]
            self._payloadDataBuffer = self._payloadDataBuffer[numberOfBytes:]
            # struct.unpack(fmt, string) # Py2.x
            # struct.unpack(fmt, buffer) # Py3.x
            # Here ret is always in bytes (buffer interface)
            if sys.version_info[0] < 3:  # Py2.x
            	ret = str(ret)
            return ret
        else:  # Fragmented MQTT packets in separate wss frames
            raise socket.error(ssl.SSL_ERROR_WANT_READ, "Not a complete MQTT packet payload within this wss frame.")

    def write(self, bytesToBeSent):
        # When there is a disconnection, select will report a TypeError which triggers the reconnect.
        # In reconnect, Paho will set the socket object (mocked by wss) to None, blocking other ops
        # before a connection is re-established.
        # This 'low-level' socket write op should always be able to write to plain socket.
        # Error reporting is performed by Python socket itself.
        # Wss closing frame handling is performed in the wss read.
        return self._bufferedWriter.write(self._encodeFrame(bytesToBeSent, self._OP_BINARY, 1), len(bytesToBeSent))

    def close(self):
        if self._sslSocket is not None:
            self._sslSocket.close()
            self._sslSocket = None

    def getSSLSocket(self):
        if self._connectStatus != self._WebsocketDisconnected:
            return self._sslSocket
        else:
            return None  # Leave the sslSocket to Paho to close it. (_ssl.close() -> wssCore.close())
