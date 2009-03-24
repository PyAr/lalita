# -*- coding: utf8 -*-

import time

import logging
logger = logging.getLogger ('ircbot.seen')
logger.setLevel (logging.DEBUG)

from core import dispatcher
from core import events

class Seen (object):
    def __init__ (self, config, params):
        register= params['register']
        self.nickname= params['nickname']
        register (events.JOIN, self.log)
        self.config= dict (block_size=4096).update (config)
        self.seenlog= {}

    def log (self, channel, nick):
        logger.debug ("%s joined %s" % (nick, channel))
        if nick!=self.nickname:
            self.seenlog[nick]= ("joined", time.time ())

# end
