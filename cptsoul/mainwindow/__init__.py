# -*- coding: utf-8 -*-

import gtk

from cptsoul.common import CptCommon, ignoreParams

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
            self.show_all()
            self.iconify()
        elif not self.cmdline.tray:
            self.show_all()        

    def _createAccels(self):
        accels = [
            ('<ctrl>p', self.manager.openSettingsWindowEvent),
            ('<ctrl>o', self.manager.openAddContactWindowEvent),
            ('<ctrl>q', self.manager.quitEvent),
            ('Escape', self.hide_on_delete)
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

    @ignoreParams
    def deleteEvent(self):
        if self.systray.is_embedded():
            self.hide()
        else:
            self.iconify()

    @ignoreParams
    def resizeEvent(self):
        self.config['mainWidth'], self.config['mainHeight'] = self.get_size()

    @ignoreParams
    def showHideEvent(self):
        if self.get_visible():
            if self.systray.is_embedded():
                self.hide()
            else:
                self.iconify()
        else:
            self.show_all()
