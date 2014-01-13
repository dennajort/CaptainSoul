# -*- coding: utf-8 -*-

import random
import string


def sizeFormatter(size, p=None):
    p = p or ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    if size > 1024:
        return sizeFormatter(size / 1024., p[1:])
    return '%.4g%s' % (size, p[0])


def strRandom(l=10):
    return ''.join(random.choice(string.ascii_letters + string.digits) for x in range(l))
