# -*- coding: utf-8 -*-

import os
import sys
import logging
from argparse import ArgumentParser

from cptsoul.common import CptCommon


def configLogging():
    fmt = '%(levelname)s\t: %(message)s'
    level = logging.DEBUG
    if CptCommon.cmdline.verbose <= 3:
        level = [logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG][CptCommon.cmdline.verbose]
    logging.basicConfig(level=level, format=fmt)


def cptsoul():
    # cmdline
    parser = ArgumentParser(prog='cptsoul')
    parser.add_argument('-v', '--verbose', action='count', dest='verbose', help='Set verbose mode', default=0)
    parser.add_argument('-t', action='store_true', dest='tray', help='Start in tray')
    parser.add_argument('-d', action='store_true', dest='debug', help='Start with debug window')
    CptCommon.cmdline = parser.parse_args()
    # imports
    from twisted.internet import gtk2reactor
    gtk2reactor.install()
    from twisted.internet import reactor
    from twisted.python import log
    observer = log.PythonLoggingObserver()
    observer.start()
    from cptsoul.config import createConfigFile
    from cptsoul.manager import Manager
    # start
    configLogging()
    CptCommon.config = createConfigFile()
    manager = Manager()
    manager()
    reactor.run()
    if CptCommon.willReboot:
        os.execl(sys.executable, sys.executable, *sys.argv)
