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
        self.seenlog= {}

        register (events.JOIN, self.log)
        register (events.COMMAND, self.seen, ['seen'])

    def log (self, channel, nick):
        logger.debug ("%s joined %s" % (nick, channel))
        if nick!=self.nickname:
            self.seenlog[nick]= ('joined', time.time ())
            logger.debug ("logged %s %s %s" % (nick, 'joined', time.time ()))

    def seen (self, user, channel, command, nick):
        # logger.debug ('seen command called w/ '+ str ())
        # logger.debug (self.seenlog)
        try:
            what, when= self.seenlog[nick]
            now= time.time ()
            if what=='joined':
                return (channel, "%s: le vi entrar hace un rato..." % user)
        except KeyError:
            return (channel, "%s: me lo deje en la otra pollera" % user)

# end
