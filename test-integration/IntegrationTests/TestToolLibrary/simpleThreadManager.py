# Library for controllable threads. Should be able to:
# 1. Create different threads
# 2. Terminate certain thread
# 3. Join certain thread


import time
import threading


# Describe the type, property and control flag for a certain thread
class _threadControlUnit:
    # Constants for different thread type
    _THREAD_TYPE_ONETIME = 0
    _THREAD_TYPE_LOOP = 1

    def __init__(self, threadID, threadType, runFunction, runParameters, scanningSpeedSecond=0.01):
        if threadID is None or threadType is None or runFunction is None or runParameters is None:
            raise ValueError("None input detected.")
        if threadType != self._THREAD_TYPE_ONETIME and threadType != self._THREAD_TYPE_LOOP:
            raise ValueError("Thread type not supported.")
        self.threadID = threadID
        self.threadType = threadType
        self.runFunction = runFunction
        self.runParameters = runParameters
        self.threadObject = None  # Holds the real thread object
        # Now configure control flag, only meaning for loop thread type
        if self.threadType == self._THREAD_TYPE_LOOP:
            self.stopSign = False  # Enabled infinite loop by default
            self.scanningSpeedSecond = scanningSpeedSecond
        else:
            self.stopSign = None  # No control flag for one time thread
            self.scanningSpeedSecond = -1

    def _oneTimeRunFunction(self):
        self.runFunction(*self.runParameters)

    def _loopRunFunction(self):
        while not self.stopSign:
            self.runFunction(*self.runParameters)  # There should be no manual delay in this function
            time.sleep(self.scanningSpeedSecond)

    def _stopMe(self):
        self.stopSign = True

    def _setThreadObject(self, threadObject):
        self.threadObject = threadObject

    def _getThreadObject(self):
        return self.threadObject


# Class that manages all threadControlUnit
# Used in a single thread
class simpleThreadManager:
    def __init__(self):
        self._internalCount = 0
        self._controlCenter = dict()

    def createOneTimeThread(self, runFunction, runParameters):
        returnID = self._internalCount
        self._controlCenter[self._internalCount] = _threadControlUnit(self._internalCount,
                                                                      _threadControlUnit._THREAD_TYPE_ONETIME,
                                                                      runFunction, runParameters)
        self._internalCount += 1
        return returnID

    def createLoopThread(self, runFunction, runParameters, scanningSpeedSecond):
        returnID = self._internalCount
        self._controlCenter[self._internalCount] = _threadControlUnit(self._internalCount,
                                                                      _threadControlUnit._THREAD_TYPE_LOOP, runFunction,
                                                                      runParameters, scanningSpeedSecond)
        self._internalCount += 1
        return returnID

    def stopLoopThreadWithID(self, threadID):
        threadToStop = self._controlCenter.get(threadID)
        if threadToStop is None:
            raise ValueError("No such threadID.")
        else:
            if threadToStop.threadType == _threadControlUnit._THREAD_TYPE_LOOP:
                threadToStop._stopMe()
                time.sleep(3 * threadToStop.scanningSpeedSecond)
            else:
                raise TypeError("Error! Try to stop a one time thread.")

    def startThreadWithID(self, threadID):
        threadToStart = self._controlCenter.get(threadID)
        if threadToStart is None:
            raise ValueError("No such threadID.")
        else:
            currentThreadType = threadToStart.threadType
            newThreadObject = None
            if currentThreadType == _threadControlUnit._THREAD_TYPE_LOOP:
                newThreadObject = threading.Thread(target=threadToStart._loopRunFunction)
            else:  # One time thread
                newThreadObject = threading.Thread(target=threadToStart._oneTimeRunFunction)
            newThreadObject.start()
            threadToStart._setThreadObject(newThreadObject)

    def joinOneTimeThreadWithID(self, threadID):
        threadToJoin = self._controlCenter.get(threadID)
        if threadToJoin is None:
            raise ValueError("No such threadID.")
        else:
            if threadToJoin.threadType == _threadControlUnit._THREAD_TYPE_ONETIME:
                currentThreadObject = threadToJoin._getThreadObject()
                currentThreadObject.join()
            else:
                raise TypeError("Error! Try to join a loop thread.")
