# -*- coding: utf-8 -*-

import gtk


class AddContactWindow(gtk.Dialog):
    def __init__(self):
        super(AddContactWindow, self).__init__(title="CaptainSoul - Add contact")
        self.set_properties(
            resizable=False
        )
        self._createUi()
        self.show_all()

    def activateEvent(self, wid):
        self.response(gtk.RESPONSE_OK)

    def getLogin(self):
        return self._entry.get_text().strip()

    def _createUi(self):
        self._entry = gtk.Entry()
        self._entry.connect("activate", self.activateEvent)
        self.vbox.pack_start(self._entry, True, True, 0)
        self.add_buttons("Add", gtk.RESPONSE_OK, "Cancel", gtk.RESPONSE_CANCEL)
