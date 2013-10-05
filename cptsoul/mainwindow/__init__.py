# -*- coding: utf-8 -*-

import gtk

from cptsoul.common import CptCommon

from cptsoul.mainwindow.watchlist import WatchList
from cptsoul.mainwindow.toolbar import ToolBar
from cptsoul.mainwindow.mainstatus import MainStatus


class MainWindow(gtk.Window, CptCommon):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.set_properties(
            title="CaptainSoul"
        )
        self.resize(self.config['mainWidth'], self.config['mainHeight'])
        self._createAccels()
        self._createUi()
        self.connect("delete-event", self.deleteEvent)
        self.connect("configure-event", self.resizeEvent)

    def afterSystrayInit(self):
        if self.cmdline.tray and not self.systray.is_embedded():
            self.iconify()
        elif not self.cmdline.tray:
            self.show_all()

    def _createAccels(self):
        accels = [
            ('<ctrl>p', self.manager.openSettingsWindowEvent),
            ('<ctrl>o', self.manager.openAddContactWindowEvent),
            ('<ctrl>q', self.manager.quitEvent),
            ('Escape', self.deleteEvent)
        ]
        ag = gtk.AccelGroup()
        self.add_accel_group(ag)
        for accel, callback in accels:
            key, mask = gtk.accelerator_parse(accel)
            ag.connect_group(key, mask, gtk.ACCEL_VISIBLE, callback)

    def _createUi(self):
        box = gtk.VBox(False, 0)
        self.add(box)
        box.pack_start(ToolBar(), False, False, 0)
        scroll = gtk.ScrolledWindow()
        scroll.set_properties(
            hscrollbar_policy=gtk.POLICY_NEVER,
            vscrollbar_policy=gtk.POLICY_AUTOMATIC,
            shadow_type=gtk.SHADOW_ETCHED_IN)
        scroll.add(WatchList())
        box.pack_start(scroll, True, True, 0)
        box.pack_start(MainStatus(), False, False, 0)

    # Events

    def deleteEvent(self, win, event):
        if self.systray.is_embedded():
            self.hide()
        else:
            self.iconify()
        return True

    def resizeEvent(self, win, event):
        self.config['mainWidth'], self.config['mainHeight'] = self.get_size()

    def showHideEvent(self, systray):
        if self.get_visible():
            if self.systray.is_embedded():
                self.hide()
            else:
                self.iconify()
        else:
            self.show_all()
            self.present()
