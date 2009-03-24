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

        register (events.JOIN, self.joined)
        register (events.PART, self.parted)
        # register (event
        register (events.COMMAND, self.seen, ['seen'])

    def joined (self, channel, nick):
        logger.debug ("%s joined %s" % (nick, channel))
        if nick!=self.nickname:
            self.log (channel, nick, 'joined')

    def parted (self, channel, nick):
        logger.debug ("%s parted %s" % (nick, channel))
        if nick!=self.nickname:
            self.log (channel, nick, 'parted')

    def log (self, channel, nick, what):
        self.seenlog[nick]= (what, time.time ())
        logger.debug ("logged %s %s %s" % (nick, 'joined', time.time ()))

    def seen (self, user, channel, command, nick):
        try:
            what, when= self.seenlog[nick]
            now= time.time ()
            if what=='joined':
                return (channel, "%s: le vi entrar hace un rato..." % user)
            elif what=='parted':
                return (channel, "%s: creo que se fua a hacer una paja y no volvio..." % user)
        except KeyError:
            return (channel, "%s: me lo deje en la otra pollera" % user)

# end
