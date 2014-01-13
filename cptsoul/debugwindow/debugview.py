# -*- coding: utf-8 -*-

import gtk

from cptsoul.common import CptCommon


class DebugView(gtk.ScrolledWindow, CptCommon):
    def __init__(self):
        super(DebugView, self).__init__()
        self.set_properties(
            border_width=0,
            shadow_type=gtk.SHADOW_ETCHED_IN,
            hscrollbar_policy=gtk.POLICY_AUTOMATIC,
            vscrollbar_policy=gtk.POLICY_AUTOMATIC
        )
        self._buffer = None
        self._createUi()
        self.connect('destroy', self.destroyEvent)
        self._connections = [
            self.manager.connect('send-raw', self.sendRawEvent),
            self.manager.connect('get-raw', self.getRawEvent)
        ]
        self._buffer.connect('changed', self.bufferChangedEvent)

    def _createUi(self):
        textview = gtk.TextView()
        textview.set_properties(
            cursor_visible=False,
            editable=False,
            wrap_mode=gtk.WRAP_NONE
        )
        self._buffer = textview.get_buffer()
        self.add(textview)

    def printLine(self, line):
        self._buffer.insert(self._buffer.get_end_iter(), "%s\n" % line)

    def getRawEvent(self, widget, line):
        self.printLine(">> %s" % line)

    def sendRawEvent(self, widget, line):
        self.printLine('<< %s' % line)

    def bufferChangedEvent(self, widget):
        adj = self.get_vadjustment()
        adj.set_value(adj.get_upper())

    def destroyEvent(self, widget):
        for co in self._connections:
            self.manager.disconnect(co)
