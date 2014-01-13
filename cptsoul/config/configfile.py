# -*- coding: utf-8 -*-

import logging
from json import load, dump

from twisted.internet import reactor

from cptsoul.config.configtypes import nonEmptyStrJSON, boolJSON, intJSON, nonEmptyStrSetJSON


class ConfigFile(object):
    def __init__(self, path):
        self._path = path
        self._data = {}
        self.read()
        reactor.addSystemEventTrigger('before', 'shutdown', self.write)

    def read(self):
        keys = [
            ('login', nonEmptyStrJSON, "login"),
            ('password', nonEmptyStrJSON, "password"),
            ('location', nonEmptyStrJSON, "CaptainSoul"),
            ('autoConnect', boolJSON, False),
            ('notification', boolJSON, True),
            ('lastUpdate', intJSON, 0),
            ('mainHeight', intJSON, 500),
            ('mainWidth', intJSON, 350),
            ('chatHeight', intJSON, 200),
            ('chatWidth', intJSON, 200),
            ('downHeight', intJSON, 200),
            ('downWidth', intJSON, 200),
            ('watchlist', nonEmptyStrSetJSON, set())
        ]
        try:
            data = load(file(self._path, 'r'))
            if not isinstance(data, dict):
                logging.error("File is not well formatted")
                data = {}
        except IOError:
            logging.info("File don't exist")
            data = {}
        except ValueError:
            logging.error("File isn't JSON")
            data = {}
        else:
            logging.info("File OK")
        self._data = {key: klass(data.get(key, default)) for key, klass, default in keys}

    def write(self):
        try:
            dump(
                {key: value.toJSON() for key, value in self._data.iteritems()},
                file(self._path, 'w'),
                indent=4,
                separators=(',', ': ')
            )
        except:
            logging.error("Can't write file")
        else:
            logging.info("File successfully written")

    def __getitem__(self, key):
        if key in self._data:
            logging.debug('Get key "%s"' % key)
            return self._data[key].getter()
        else:
            logging.error("Key %s don't exist" % key)
            raise KeyError(key)

    def __setitem__(self, key, value):
        if key in self._data:
            logging.debug('Set key "%s" == "%s"' % (key, value))
            self._data[key].setter(value)
        else:
            logging.error("Key %s don't exist" % key)
            raise KeyError(key)
