# -*- coding: utf8 -*-

# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

from twisted.internet import reactor
import sys
import logging

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
                            "%(asctime)s %(name)s:%(lineno)-4d %(levelname)-8s %(message)s",
                            '%H:%M:%S')
handler.setFormatter(formatter)

# if we're in production, this should work and no magic is necessary
try:
    import lalita
except ImportError:
    import core
    sys.modules["lalita"] = core

from plugins.url import Url

if __name__ == '__main__':
    lalitalone = Url (dict (nickname=sys.argv[1], guess_encoding=0.75), logging.DEBUG)

    logfile= sys.argv[2]
    try:
        no_more_than= int (sys.argv[3])
    except (ValueError, IndexError):
        no_more_than= 500
    lalitalone.import_logs (logfile, no_more_than)

    reactor.run()

# end
