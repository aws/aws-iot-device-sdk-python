import socket
import ssl

class mockSSLSocket:
	def __init__(self):
		self._readBuffer = bytearray()
		self._writeBuffer = bytearray()
		self._isClosed = False
		self._isFragmented = False
		self._fragmentDoneThrowError = False
		self._currentFragments = bytearray()
		self._fragments = list()
		self._flipWriteError = False
		self._flipWriteErrorCount = 0

	# TestHelper APIs
	def refreshReadBuffer(self, bytesToLoad):
		self._readBuffer = bytesToLoad

	def reInit(self):
		self._readBuffer = bytearray()
		self._writeBuffer = bytearray()
		self._isClosed = False
		self._isFragmented = False
		self._fragmentDoneThrowError = False
		self._currentFragments = bytearray()
		self._fragments = list()
		self._flipWriteError = False
		self._flipWriteErrorCount = 0

	def getReaderBuffer(self):
		return self._readBuffer

	def getWriteBuffer(self):
		return self._writeBuffer

	def addReadBufferFragment(self, fragmentElement):
		self._fragments.append(fragmentElement)

	def setReadFragmented(self):
		self._isFragmented = True

	def setFlipWriteError(self):
		self._flipWriteError = True
		self._flipWriteErrorCount = 0

	def loadFirstFragmented(self):
		self._currentFragments = self._fragments.pop(0)

	# Public APIs
	# Should return bytes, not string
	def read(self, numberOfBytes):
		if not self._isFragmented:  # Read a lot, then nothing
			if len(self._readBuffer) == 0:
				raise socket.error(ssl.SSL_ERROR_WANT_READ, "End of read buffer")
			# If we have enough data for the requested amount, give them out
			if numberOfBytes <= len(self._readBuffer):
				ret = self._readBuffer[0:numberOfBytes]
				self._readBuffer = self._readBuffer[numberOfBytes:]
			else:
				ret = self._readBuffer
				self._readBuffer = self._readBuffer[len(self._readBuffer):]  # Empty
			return ret
		else:  # Read 1 fragement util it is empty, then throw error, then load in next
			if self._fragmentDoneThrowError and len(self._fragments) > 0:
				self._currentFragments = self._fragments.pop(0)  # Load in next fragment
				self._fragmentDoneThrowError = False  # Reset ThrowError flag
				raise socket.error(ssl.SSL_ERROR_WANT_READ, "Not ready for read op")
			# If we have enough data for the requested amount in the current fragment, give them out
			ret = bytearray()
			if numberOfBytes <= len(self._currentFragments):
				ret = self._currentFragments[0:numberOfBytes]
				self._currentFragments = self._currentFragments[numberOfBytes:]
				if len(self._currentFragments) == 0:
					self._fragmentDoneThrowError = True  # Will throw error next time
			else:
				ret = self._currentFragments
				self._currentFragments = self._currentFragments[len(self._currentFragments):]  # Empty
				self._fragmentDoneThrowError = True
			return ret

	# Should write bytes, not string
	def write(self, bytesToWrite):
		if self._flipWriteError:
			if self._flipWriteErrorCount % 2 == 1:
				self._writeBuffer += bytesToWrite  # bytesToWrite should always be in 'bytes' type
				self._flipWriteErrorCount += 1
				return len(bytesToWrite)
			else:
				self._flipWriteErrorCount += 1
				raise socket.error(ssl.SSL_ERROR_WANT_WRITE, "Not ready for write op")
		else:
			self._writeBuffer += bytesToWrite  # bytesToWrite should always be in 'bytes' type
			return len(bytesToWrite)
		
	def close(self):
		self._isClosed = True







