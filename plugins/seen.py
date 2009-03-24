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
        register (events.PUBLIC_MESSAGE, self.message)
        register (events.TALKED_TO_ME, self.message)
        register (events.COMMAND, self.seen, ['seen'])

    def joined (self, channel, nick):
        logger.debug ("%s joined %s" % (nick, channel))
        if nick!=self.nickname:
            self.log (channel, nick, 'joined')

    def parted (self, channel, nick):
        logger.debug ("%s parted %s" % (nick, channel))
        if nick!=self.nickname:
            self.log (channel, nick, 'parted')

    def message (self, nick, channel, msg):
        logger.debug ("%s said %s" % (nick, msg))
        if nick!=self.nickname:
            self.log (channel, nick, msg)

    def log (self, channel, nick, what):
        self.seenlog[nick]= (what, time.time ())
        logger.debug ("logged %s %s %s" % (nick, what, time.time ()))

    def seen (self, user, channel, command, nick):
        try:
            what, when= self.seenlog[nick]
            now= time.time ()
            if what=='joined':
                return (channel, u"%s: le vi entrar hace un rato..." % user)
            elif what=='parted':
                return (channel, u"%s: creo que se fua a hacer una paja y no volvio..." % user)
            else:
                return (channel, u"%s: hace un rato lo escuche decir «%s» o una gansada por el estilo" % (user, what))
        except KeyError:
            return (channel, u"%s: me lo deje en la otra pollera :|" % user)

# end
