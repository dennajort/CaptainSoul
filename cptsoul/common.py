# -*- coding: utf-8 -*-


class CptCommon(object):
    manager = None
    downloadManager = None
    mainWindow = None
    cmdline = None
    config = None
    systray = None
    info = {}


class PreparedCaller(object):
    def __init__(self, function, *args, **kwargs):
        self._function = function
        self._args = args
        self._kwargs = kwargs

    def __call__(self, *args, **kwargs):
        kwargs.update(self._kwargs)
        self._function(*(self._args + args), **kwargs)


def ignoreParams(func):
    def ignorebis(obj, *args, **kwargs):
        func(obj)
    return ignorebis


def ignoreParamsFn(func):
    def ignorebis(*args, **kwargs):
        func()
    return ignorebis