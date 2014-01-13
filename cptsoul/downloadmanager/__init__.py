# -*- coding: utf-8 -*-

import gtk

from cptsoul.common import CptCommon
from cptsoul.downloadmanager.downloadlist import DownloadList
from cptsoul.downloadmanager.uploadlist import UploadList


class DownloadManager(gtk.Window, CptCommon):
    def __init__(self):
        super(DownloadManager, self).__init__()
        self.set_properties(
            title="CaptainSoul - Download Manager"
        )
        self.resize(self.config['downWidth'], self.config['downHeight'])
        self.startFileDownload = None
        self.startFileUpload = None
        self._createUi()
        self.connect("delete-event", self.hide_on_delete)
        self.connect("configure-event", self.resizeEvent)

    def _createUi(self):
        box = gtk.VBox(False, 10)
        self.add(box)
        scroll = gtk.ScrolledWindow()
        scroll.set_properties(
            hscrollbar_policy=gtk.POLICY_AUTOMATIC,
            vscrollbar_policy=gtk.POLICY_AUTOMATIC,
            shadow_type=gtk.SHADOW_ETCHED_IN)
        down = DownloadList(self)
        self.startFileDownload = down.startFileTransfer
        scroll.add(down)
        box.pack_start(scroll, True, True, 0)
        scroll = gtk.ScrolledWindow()
        scroll.set_properties(
            hscrollbar_policy=gtk.POLICY_AUTOMATIC,
            vscrollbar_policy=gtk.POLICY_AUTOMATIC,
            shadow_type=gtk.SHADOW_ETCHED_IN)
        up = UploadList(self)
        self.startFileUpload = up.startFileTransfer
        scroll.add(up)
        box.pack_start(scroll, True, True, 0)

    def resizeEvent(self, win, event):
        self.config['downWidth'], self.config['downHeight'] = self.get_size()
