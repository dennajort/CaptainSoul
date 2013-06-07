# -*- coding: utf-8 -*-

import logging

import gtk
import gobject
from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory

from Config import Config
from Netsoul import NsProtocol
from MainWindow import MainWindow
from Systray import Systray

from SettingsWindow import SettingsWindow
from AddContactWindow import AddContactWindow
from ChatWindow import ChatWindow


class Manager(gobject.GObject, ClientFactory):
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
    }
    _protocol = None
    _tryReconnecting = False
    _chatWindows = {}

    def __init__(self):
        gobject.GObject.__init__(self)
        self._mainwindow = MainWindow(self)
        self._systray = Systray(self, self._mainwindow)
        if Config['autoConnect']:
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

    # Actions

    def doConnectSocket(self):
        if self._protocol is not None:
            self.doDisconnectSocket()
        self._tryReconnecting = True
        reactor.connectTCP("ns-server.epita.fr", 4242, self, timeout=10)

    def doDisconnectSocket(self):
        if self._protocol is not None:
            self._tryReconnecting = False
            self.sendExit()
            self._protocol.transport.loseConnection()
            self._protocol = None

    def doOpenChat(self, login):
        if login not in self._chatWindows:
            self._chatWindows[login] = ChatWindow(self, login, False)
        return self._chatWindows[login]

    def doDeleteContact(self, login):
        try:
            Config['watchlist'].remove(login)
        except ValueError:
            return False
        else:
            self.emit('contact-deleted', login)
            return True

    def doAddContact(self, login):
        if login and login not in Config['watchlist']:
            Config['watchlist'].add(login)
            self.emit('contact-added', login)
            return True
        return False

    # Events

    def connectEvent(self, *args, **kwargs):
        self.doConnectSocket()

    def disconnectEvent(self, *args, **kwargs):
        self.doDisconnectSocket()

    def quitEvent(self, *args, **kwargs):
        reactor.stop()

    def closeChatWindowEvent(self, widget, event, login):
        widget.destroy()
        if login in self._chatWindows:
            del self._chatWindows[login]
        return True

    def openAddContactWindowEvent(self, *args, **kwargs):
        win = AddContactWindow()
        if win.run() == gtk.RESPONSE_OK:
            login = win.getLogin()
            win.destroy()
            self.doAddContact(login)
        else:
            win.destroy()

    def openSettingsWindowEvent(self, *args, **kwargs):
        win = SettingsWindow()
        if win.run() == gtk.RESPONSE_APPLY:
            for key, value in win.getAllParams().iteritems():
                Config[key] = value
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
            win = self.doOpenChat(info.login)
            win.addMsg(msg)

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

    # ClientFactory

    def buildProtocol(self, addr):
        return NsProtocol(self)

    def startedConnecting(self, connector):
        logging.info('Manager : Started connecting')
        self.emit('connecting')

    def clientConnectionFailed(self, connector, reason):
        self._protocol = None
        logging.warning('Manager : Connection failed reconnecting in 3 seconds')
        reactor.callLater(3, connector.connect)
        self.emit('reconnecting')

    def clientConnectionLost(self, connector, reason):
        self._protocol = None
        if self._tryReconnecting:
            logging.warning('Manager : Connection lost reconnecting in 3 seconds')
            reactor.callLater(3, connector.connect)
            self.emit('reconnecting')
        else:
            logging.info('Manager : Connection closed')
            self.emit('disconnected')