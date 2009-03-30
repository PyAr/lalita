# -*- coding: utf8 -*-

# (c) 2009 Marcos Dione <mdione@grulic.org.ar>

import datetime

from lalita import Plugin

class Seen(Plugin):
    def init(self, config):
        self.seenlog= {}

        self.register(self.events.JOIN, self.joined)
        self.register(self.events.PART, self.parted)
        self.register(self.events.PUBLIC_MESSAGE, self.message)
        self.register(self.events.TALKED_TO_ME, self.message)
        self.register(self.events.COMMAND, self.seen, ['seen'])

    def joined (self, channel, nick):
        self.logger.debug("%s joined %s", nick, channel)
        self.log(channel, nick, 'joined')

    def parted(self, channel, nick):
        self.logger.debug("%s parted %s", nick, channel)
        self.log(channel, nick, 'parted')

    def message(self, nick, channel, msg):
        self.logger.debug("%s said %s", nick, msg)
        self.log(channel, nick, msg)

    def log(self, channel, nick, what):
        # server messages are from ''; ignore those and myself
        if nick not in (self.nickname, ''):
            self.seenlog[nick] = (what, datetime.datetime.now())
            self.logger.debug("logged %s: %s", nick, what)

    def seen(self, user, channel, command, nick):
        if nick not in (self.nickname, user):
            try:
                what, when = self.seenlog[nick]
            except KeyError:
                self.say(channel, u"%s: me lo deje en la otra pollera :|" % user)
            else:
                # now= time.time ()
                if what=='joined':
                    self.say(channel, u"%s: le vi entrar hace un rato..." % user)
                elif what=='parted':
                    self.say(channel, u"%s: creo que se fua a hacer una paja y no volvio..." % user)
                else:
                    self.say(channel, u"%s: hace un rato lo escuche decir «%s» o una gansada por el estilo" % (user, what))
        elif nick==self.nickname:
            self.say(channel, u"%s: acástoi, papafrita!" % user)
        elif nick==user:
            self.say(channel, u"%s: andá mirate en el espejo del baño" % user)

# end
