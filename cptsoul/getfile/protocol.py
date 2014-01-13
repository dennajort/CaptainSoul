# -*- coding: utf-8 -*-

from twisted.internet.protocol import Protocol, connectionDone


class GetFileProtocol(Protocol):
    def __init__(self, coCall, proCall, endCall):
        self._coCall = coCall
        self._proCall = proCall
        self._endCall = endCall

    def connectionMade(self):
        self._coCall()

    def connectionLost(self, reason=connectionDone):
        self._endCall()

    def dataReceived(self, data):
        self._proCall(data, self)
