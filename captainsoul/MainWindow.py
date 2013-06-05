# -*- coding: utf-8 -*-

import logging

from gi.repository import Gtk
from twisted.internet import reactor

from CmdLine import options
from Netsoul import NsFactory
from Config import Config
import Icons

from WatchList import WatchList
from ToolBar import ToolBar
from SettingsWindow import SettingsWindow
from AddContactWindow import AddContactWindow
from Systray import Systray
from WindowManager import WindowManager

NS_HOST, NS_PORT = 'ns-server.epita.fr', 4242


class MainWindow(Gtk.Window):
    _protocol = None
    _keepConnect = True

    def __init__(self):
        super(MainWindow, self).__init__(title="CaptainSoul", border_width=2, icon=Icons.shield.get_pixbuf())
        self._manager = WindowManager(self)
        self._createUi()
        self.resize(Config['mainWidth'], Config['mainHeight'])
        self.connect("delete-event", self.deleteEvent)
        self.connect("configure-event", self.resizeEvent)
        if Config['autoConnect']:
            self.connectEvent()
        if not options.tray:
            self.show_all()

    def _createUi(self):
        self._systray = Systray(self)
        box = Gtk.VBox(False, 0)
        self._toolbar = ToolBar(self)
        box.pack_start(self._toolbar, False, False, 0)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_size_request(160, 50)
        self._watchlist = WatchList(self)
        scroll.add_with_viewport(self._watchlist)
        box.pack_start(scroll, True, True, 0)
        self._status = Gtk.Statusbar()
        box.pack_start(self._status, False, False, 0)
        self._status.push(0, "Welcome")
        self.add(box)

    # Events

    def resizeEvent(self, *args, **kwargs):
        Config['mainWidth'], Config['mainHeight'] = self.get_size()

    def quitEvent(self, *args, **kwargs):
        reactor.stop()

    def deleteEvent(self, *args, **kwargs):
        self.hide()
        return True

    def connectEvent(self, *args, **kwargs):
        self._toolbar.connectEvent()
        self._keepConnect = True
        self._status.push(0, "Connecting...")
        self.createConnection()

    def disconnectEvent(self, *args, **kwargs):
        self._toolbar.disconnectEvent()
        self._keepConnect = False
        self.stopConnection()

    def settingsEvent(self, *args, **kwargs):
        SettingsWindow().destroy()

    def showHideEvent(self, *args, **kwargs):
        if self.get_visible():
            self.hide()
        else:
            self.show_all()

    def addContactWindowEvent(self, *args, **kwargs):
        AddContactWindow(self).destroy()

    # Senders

    def sendState(self, state):
        if self._protocol is not None:
            self._protocol.sendState(state)

    def sendWatch(self):
        if self._protocol is not None:
            self._protocol.sendWatch()

    def sendMsg(self, msg, dests):
        if self._protocol is not None:
            self._protocol.sendMsg(msg, dests)

    def sendWho(self, logins):
        if self._protocol is not None:
            self._protocol.sendWho(logins)

    def sendExit(self):
        if self._protocol is not None:
            self._protocol.sendExit()

    def sendStartTyping(self, dests):
        if self._protocol is not None:
            self._protocol.sendStartTyping(dests)

    def sendCancelTyping(self, dests):
        if self._protocol is not None:
            self._protocol.sendCancelTyping(dests)

    # Netsoul Actions

    def createConnection(self):
        if self._protocol is not None:
            self.stopConnection()
        reactor.connectTCP(NS_HOST, NS_PORT, NsFactory(self))

    def stopConnection(self):
        if self._protocol is not None:
            self.sendExit()
            self._protocol.transport.loseConnection()

    # Netsoul Hooks

    def setProtocol(self, protocol):
        self._protocol = protocol

    def loggedHook(self):
        logging.debug('MainWindow : Logged')
        self._status.push(0, "Connected")

    def loginFailedHook(self):
        logging.debug('MainWindow : Login failed')
        self.disconnectEvent()

    def connectionLostHook(self):
        self._protocol = None
        if self._keepConnect:
            logging.warning('MainWindow : Connection lost try reconnect')
            self._status.push(0, "Reconnecting...")
            reactor.callLater(3, self.connectEvent)
        else:
            logging.debug("MainWindow : Connection lost don't try reconnect")
            self._status.push(0, "Disconnected")

    def connectionMadeHook(self):
        logging.debug('MainWindow : Connection made')

    def cmdStateHook(self, info, state):
        logging.debug('MainWindow : State %s "%s"' % (info, state))
        self._watchlist.setState(info, state)
        self._manager.changeState(info.login, state)

    def cmdLoginHook(self, info):
        pass

    def cmdLogoutHook(self, info):
        self._watchlist.logoutHook(info)

    def cmdIsTypingHook(self, info):
        self._manager.startTyping(info.login)

    def cmdCancelTypingHook(self, info):
        self._manager.cancelTyping(info.login)

    def cmdMsgHook(self, info, msg, dest):
        self._systray.notifyMessage(info.login, msg)
        self._manager.showMsg(info.login, msg)

    def cmdWhoHook(self, result):
        self._watchlist.processWho(result)
        for res in result:
            self._manager.changeState(res.login, res.state)
