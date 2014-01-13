# -*- coding: utf-8 -*-

import logging
from os import unlink

from twisted.internet import reactor

from cptsoul.common import CptCommon
from cptsoul.getfile.factory import GetFileFactory


class FileGetter(CptCommon):
    def __init__(self, info, name, path, size, proCall, endCall, errorCall):
        self._ok = False
        self._path = path
        self._file = None
        self._endCall = endCall
        self._proCall = proCall
        self._errorCall = errorCall
        self._done = 0
        self._sizeTotal = size
        self._percent = 0
        self._port = reactor.listenTCP(0, GetFileFactory(
            self.clientConnectionMade,
            self.clientProgress,
            self.clientConnectionEnd
        ))
        logging.info('GetFile : Listen on port %d' % self._port.getHost().port)
        self.manager.sendFileStart(name, self.info['host'], self._port.getHost().port, [info.login])

    def clientConnectionMade(self):
        logging.info('GetFile : Client connected')
        self._file = open(self._path, 'w')
        self._port.stopListening()
        self._proCall(0, self._sizeTotal)

    def clientProgress(self, data, protocol):
        self._file.write(data)
        self._done += len(data)
        tmp = 100 * self._done / self._sizeTotal
        if tmp > self._percent:
            self._proCall(self._done, self._sizeTotal)
            self._percent = tmp
        if self._done >= self._sizeTotal:
            logging.info('GetFile : Transfer success')
            self._ok = True
            self._file.close()
            protocol.transport.loseConnection()
            self._endCall()

    def clientConnectionEnd(self):
        if not self._ok:
            logging.warning('GetFile : Tranfer aborted')
            self._file.close()
            unlink(self._path)
            self._errorCall()
