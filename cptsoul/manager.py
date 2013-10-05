# -*- coding: utf-8 -*-

import logging

import gtk
import gobject
from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory

from cptsoul.common import CptCommon, ignoreParams
from cptsoul.netsoul import NsProtocol
from cptsoul import icons

from cptsoul.mainwindow import MainWindow
from cptsoul.downloadmanager import DownloadManager
from cptsoul.downloadmanager.askfilewindow import AskFileWindow
from cptsoul.systray import Systray
from cptsoul.settingswindow import SettingsWindow
from cptsoul.addcontactwindow import AddContactWindow
from cptsoul.chatwindow import ChatWindow
from cptsoul.debugwindow import DebugWindow


class Manager(gobject.GObject, ClientFactory, CptCommon):
    reconnectDelay = 2
    netsoulHost = 'ns-server.epita.fr'
    netsoulPort = 4242
    __gsignals__ = {
        'reconnecting': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
        'connecting': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
        'disconnected': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
        'connected': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
        'logged': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
        'login-failed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
        'login': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
        'logout': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
        'msg': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT, gobject.TYPE_STRING, gobject.TYPE_PYOBJECT]),
        'who': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
        'state': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT, gobject.TYPE_STRING]),
        'is-typing': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
        'cancel-typing': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
        'contact-added': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING]),
        'contact-deleted': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING]),
        'send-msg': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING, gobject.TYPE_PYOBJECT]),
        'send-raw': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING]),
        'get-raw': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_STRING]),
        'file-ask': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT, gobject.TYPE_STRING, gobject.TYPE_ULONG, gobject.TYPE_STRING]),
        'file-start': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_INT])
    }

    def __init__(self):
        gobject.GObject.__init__(self)
        self._protocol = None
        self._tryReconnecting = False
        self._pingDefer = None
        self._chatWindows = {}
        reactor.addSystemEventTrigger('before', 'shutdown', self._beforeShutdown)
        gtk.window_set_default_icon(icons.shield)
        CptCommon.manager = self
        CptCommon.mainWindow = MainWindow()
        CptCommon.systray = Systray()
        CptCommon.mainWindow.afterSystrayInit()
        CptCommon.downloadManager = DownloadManager()
        if CptCommon.cmdline.debug:
            DebugWindow()

    def _beforeShutdown(self):
        self._tryReconnecting = False

    def __call__(self):
        if self.config['autoConnect']:
            self.doConnectSocket()

    # Senders

    def sendState(self, state):
        if self._protocol is not None:
            logging.info(u'Manager : Send state %s' % state)
            self._protocol.sendState(state)
        else:
            logging.warning(u'Manager : Try send state %s' % state)

    def sendWatch(self, sendWho=True):
        if self._protocol is not None:
            logging.info(u'Manager : Send watch (send who = %s)' % sendWho)
            self._protocol.sendWatch(sendWho)
        else:
            logging.warning(u'Manager : Try send watch (send who = %s)' % sendWho)

    def sendMsg(self, msg, dests):
        if self._protocol is not None:
            logging.info(u'Manager : Send msg "%s" to %s' % (msg, dests))
            self.emit('send-msg', msg, dests)
            self._protocol.sendMsg(msg, dests)
        else:
            logging.warning(u'Manager : Try send msg "%s" to %s' % (msg, dests))

    def sendWho(self, logins):
        if self._protocol is not None:
            logging.info('Manager : Send who of %s' % logins)
            self._protocol.sendWho(logins)
        else:
            logging.warning('Manager : Try send who of %s' % logins)

    def sendExit(self):
        if self._protocol is not None:
            logging.info('Manager : Send exit')
            self._protocol.sendExit()
        else:
            logging.warning('Manager : Try send exit')

    def sendStartTyping(self, dests):
        if self._protocol is not None:
            logging.info('Manager : Send start typing to %s' % dests)
            self._protocol.sendStartTyping(dests)
        else:
            logging.warning('Manager : Try send start typing to %s' % dests)

    def sendCancelTyping(self, dests):
        if self._protocol is not None:
            logging.info('Manager : Send cancel typing to %s' % dests)
            self._protocol.sendCancelTyping(dests)
        else:
            logging.warning('Manager : Try send cancel typing to %s' % dests)

    def sendRaw(self, line):
        if self._protocol is not None:
            logging.info('Manager : Send raw "%s"' % line)
            self._protocol.sendLine(line)
        else:
            logging.warning('Manager : Try send raw "%s"' % line)

    def sendFileStart(self, name, ip, port, dests):
        if self._protocol is not None:
            logging.info('Manager : Send file "%s" start %s:%d to %s' % (name, ip, port, dests))
            self._protocol.sendFileStart(name, ip, port, dests)
        else:
            logging.warning('Manager : Try send file "%s" start %s:%d to %s' % (name, ip, port, dests))

    def sendFileAsk(self, name, size, desc, dests):
        if self._protocol is not None:
            logging.info('Manager : Send file "%s" ask size %d bytes to %s' % (name, size, dests))
            self._protocol.sendFileAsk(name, size, desc, dests)
        else:
            logging.warning('Manager : Try send file "%s" ask size %d bytes to %s' % (name, size, dests))

    # Actions

    def doConnectSocket(self):
        if self._protocol is not None:
            self.doDisconnectSocket()
        self._tryReconnecting = True
        reactor.connectTCP(self.netsoulHost, self.netsoulPort, self, timeout=10)

    def doDisconnectSocket(self):
        if self._protocol is not None:
            self._tryReconnecting = False
            self.sendExit()
            self._protocol.transport.loseConnection()
            self._protocol = None

    def doReconnectSocket(self):
        if self._protocol is not None:
            self._tryReconnecting = True
            self.sendExit()
            self._protocol.transport.loseConnection()
            self._protocol = None
        else:
            self.doConnectSocket()

    def doOpenChat(self, login, msg=None):
        if login not in self._chatWindows:
            self._chatWindows[login] = ChatWindow(login, False, msg)
        return self._chatWindows[login]

    def doDeleteContact(self, login):
        try:
            self.config['watchlist'].remove(login)
        except ValueError:
            return False
        else:
            self.emit('contact-deleted', login)
            return True

    def doAddContact(self, login):
        if login and login not in self.config['watchlist']:
            self.config['watchlist'].add(login)
            self.config.write()
            self.emit('contact-added', login)
            return True
        return False

    # Events

    @ignoreParams
    def connectEvent(self):
        self.doConnectSocket()

    @ignoreParams
    def disconnectEvent(self):
        self.doDisconnectSocket()

    @ignoreParams
    def quitEvent(self):
        reactor.stop()

    def closeChatWindowEvent(self, widget, event, login):
        widget.destroy()
        if login in self._chatWindows:
            self._chatWindows[login].destroy()
            del self._chatWindows[login]
        return True

    @ignoreParams
    def openAddContactWindowEvent(self):
        win = AddContactWindow()
        if win.run() == gtk.RESPONSE_OK:
            login = win.getLogin()
            win.destroy()
            self.doAddContact(login)
        else:
            win.destroy()

    @ignoreParams
    def openSettingsWindowEvent(self):
        win = SettingsWindow()
        if win.run() == gtk.RESPONSE_APPLY:
            for key, value in win.getAllParams().iteritems():
                self.config[key] = value
            self.config.write()
        win.destroy()

    # GSignals methods

    def do_logged(self):
        self.sendState('actif')
        self.sendWatch()

    def do_login_failed(self):
        self.doDisconnectSocket()

    def do_contact_added(self, login):
        self.sendWatch()

    def do_contact_deleted(self, login):
        self.sendWatch()

    def do_msg(self, info, msg, dests):
        if info.login not in self._chatWindows:
            self.doOpenChat(info.login, msg)

    def do_file_ask(self, info, name, size, desc):
        AskFileWindow(info, name, size, desc)

    def do_get_raw(self, line):
        if self._pingDefer is not None:
            self._pingDefer.cancel()
        self._pingDefer = reactor.callLater(60, self._pingStepOne)

    def do_reconnecting(self):
        if self._pingDefer is not None:
            self._pingDefer.cancel()
        self._pingDefer = None

    def do_disconnected(self):
        if self._pingDefer is not None:
            self._pingDefer.cancel()
        self._pingDefer = None

    # Ping callbacks

    def _pingStepOne(self):
        logging.info('Manager : PingStepOne')
        self._pingDefer = reactor.callLater(10, self._pingStepTwo)
        self.sendWho([self.config['login']])

    def _pingStepTwo(self):
        logging.info('Manager : PingStepTwo')
        self._pingDefer = None
        self.doReconnectSocket()

    # NsProtocol Hooks

    def setProtocol(self, protocol):
        self._protocol = protocol

    def connectionMadeHook(self):
        logging.info('Manager : Connected')
        self.emit('connected')

    def loggedHook(self):
        logging.info('Manager : Logged successfully')
        self.emit('logged')

    def loginFailedHook(self):
        logging.info('Manager : Login failed')
        self.emit('login-failed')

    def cmdLoginHook(self, info):
        logging.info(u'Manager : Cmd %s login' % info)
        self.emit('login', info)

    def cmdLogoutHook(self, info):
        logging.info(u'Manager : Cmd %s logout' % info)
        self.emit('logout', info)

    def cmdMsgHook(self, info, msg, dests):
        logging.info(u'Manager : Cmd %s msg "%s" %s' % (info, msg, dests))
        self.emit('msg', info, msg, dests)

    def cmdWhoHook(self, result):
        logging.info(u'Manager : Who %s' % result)
        self.emit('who', result)

    def cmdStateHook(self, info, state):
        logging.info(u'Manager : Cmd %s state %s' % (info, state))
        self.emit('state', info, state)

    def cmdIsTypingHook(self, info):
        logging.info(u'Manager : Cmd %s is typing' % info)
        self.emit('is-typing', info)

    def cmdCancelTypingHook(self, info):
        logging.info(u'Manager : Cmd %s cancel typing' % info)
        self.emit('cancel-typing', info)

    def rawHook(self, line):
        self.emit('get-raw', line)

    def sendRawHook(self, line):
        self.emit('send-raw', line)

    def cmdFileAskHook(self, info, name, size, desc):
        logging.info(u'Manager : Cmd %s file ask %s %dB' % (info, name, size))
        self.emit('file-ask', info, name, size, desc)

    def cmdFileStartHook(self, info, name, ip, port):
        logging.info(u'Manager : Cmd %s file start %s %s:%d' % (info, name, ip, port))
        self.emit('file-start', info, name, ip, port)

    # ClientFactory

    def buildProtocol(self, addr):
        return NsProtocol(self)

    def startedConnecting(self, connector):
        logging.info('Manager : Started connecting')
        self.emit('connecting')

    def clientConnectionFailed(self, connector, reason):
        self._protocol = None
        logging.warning('Manager : Connection failed reconnecting in %d seconds' % self.reconnectDelay)
        reactor.callLater(self.reconnectDelay, connector.connect)
        self.emit('reconnecting')

    def clientConnectionLost(self, connector, reason):
        self._protocol = None
        if self._tryReconnecting:
            logging.warning('Manager : Connection lost reconnecting in %d seconds' % self.reconnectDelay)
            reactor.callLater(self.reconnectDelay, connector.connect)
            self.emit('reconnecting')
        else:
            logging.info('Manager : Connection closed')
            self.emit('disconnected')
