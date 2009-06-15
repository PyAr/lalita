# -*- coding: utf8 -*-

# (c) 2009 Marcos Dione <mdione@grulic.org.ar>

from twisted.internet import reactor
import sys
import logging

# if we're in production, this should work and no magic is necessary
try:
    import lalita
except ImportError:
    import core
    sys.modules["lalita"] = core

from plugins.url import Url

if __name__ == '__main__':
    lalitalone = Url (dict (nickname=sys.argv[1]), logging.DEBUG)

    logfile= sys.argv[2]
    try:
        no_more_than= int (sys.argv[3])
    except (ValueError, IndexError):
        no_more_than= 500
    lalitalone.import_logs (logfile, no_more_than)

    reactor.run()

# end
