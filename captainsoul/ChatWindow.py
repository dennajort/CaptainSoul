# -*- coding: utf-8 -*-

from gi.repository import Gtk, Pango, Gdk

import Icons
from ChatView import ChatView


class ChatWindow(Gtk.Window):
    _typing = False

    def __init__(self, manager, mw, login, iconify):
        super(ChatWindow, self).__init__(title="CaptainSoul - %s" % login, border_width=2, icon=Icons.shield.get_pixbuf())
        self._login = login
        self._mw = mw
        self._createUi()
        self.connect("delete-event", self.deleteEvent)
        self.connect("delete-event", manager.closeWindow, login)
        self.resize(200, 200)
        if iconify:
            self.iconify()
        self.show_all()

    def _createUi(self):
        box = Gtk.VBox(False, 0)
        self._text = ChatView()
        box.add(self._text)
        # ENTRY
        view = Gtk.TextView(editable=True, cursor_visible=True, wrap_mode=Gtk.WrapMode.WORD_CHAR)
        self._entry = view.get_buffer()
        view.set_size_request(100, 30)
        view.connect("key-press-event", self.keyPressEvent)
        self._entry.connect("changed", self.keyPressEventEnd)
        box.pack_start(view, False, False, 0)
        self._status = Gtk.Statusbar()
        box.pack_start(self._status, False, False, 0)
        self.add(box)

    def deleteEvent(self, widget, reason):
        if self._typing:
            self._mw.sendCancelTyping([self._login])
            self._typing = False

    def keyPressEvent(self, widget, event):
        if event.keyval == Gdk.KEY_Return:
            text = self._entry.get_text(self._entry.get_start_iter(), self._entry.get_end_iter(), True)
            if len(text):
                self._entry.delete(self._entry.get_start_iter(), self._entry.get_end_iter())
                self._text.addMyMsg(text)
                self._mw.sendMsg(text, [self._login])
            return True

    def keyPressEventEnd(self, widget):
        l = len(self._entry.get_text(self._entry.get_start_iter(), self._entry.get_end_iter(), True))
        if not self._typing and l >= 5:
            self._mw.sendStartTyping([self._login])
            self._typing = True
        elif self._typing and l < 5:
            self._mw.sendCancelTyping([self._login])
            self._typing = False

    def addMsg(self, msg):
        self._text.addOtherMsg(msg, self._login)

    def changeState(self, state):
        pass

    def startTyping(self):
        self._status.push(0, "Is typing...")

    def cancelTyping(self):
        self._status.remove_all(0)
