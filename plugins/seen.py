# -*- coding: utf8 -*-

# (c) 2009 Marcos Dione <mdione@grulic.org.ar>

import datetime

import logging
logger = logging.getLogger ('ircbot.plugins.seen')
logger.setLevel (logging.INFO)

class Seen (object):
    def __init__ (self, config, events, params):
        register= params['register']
        self.nickname= params['nickname']
        self.seenlog= {}
        self.config= dict (clever=True)
        self.config.update (config)

        register (events.JOIN, self.joined)
        register (events.PART, self.parted)
        register (events.PUBLIC_MESSAGE, self.message)
        register (events.TALKED_TO_ME, self.message)
        register (events.COMMAND, self.seen, ['seen'])

    def joined (self, channel, nick):
        logger.debug ("%s joined %s" % (nick, channel))
        self.log (channel, nick, 'joined')

    def parted (self, channel, nick):
        logger.debug ("%s parted %s" % (nick, channel))
        self.log (channel, nick, 'parted')

    def message (self, nick, channel, msg):
        logger.debug ("%s said %s" % (nick, msg))
        self.log (channel, nick, msg)

    def log (self, channel, nick, what):
        # server messages are from ''; ignore those and myself
        if nick not in (self.nickname, ''):
            self.seenlog[nick]= (what, datetime.datetime.now ())
            logger.debug ("logged %s: %s" % (nick, what))

    def seen (self, user, channel, command, nick):
        if not self.config['clever'] or nick not in (self.nickname, user):
            try:
                what, when= self.seenlog[nick]
            except KeyError:
                return [(channel, u"%s: me lo deje en la otra pollera :|" % user)]
            else:
                # now= time.time ()
                if what=='joined':
                    return [(channel, u"%s: [%s] -- joined" % (user, when.strftime ("%x %X")))]
                elif what=='parted':
                    return [(channel, u"%s: [%s] -- parted" % (user, when.strftime ("%x %X")))]
                else:
                    return [(channel, u"%s: [%s] %s" % (user, when.strftime ("%x %X"), what))]
        elif nick==self.nickname:
            return [(channel, u"%s: acástoi, papafrita!" % user)]
        elif nick==user:
            return [(channel, u"%s: andá mirate en el espejo del baño" % user)]

# end
