# -*- coding: utf8 -*-

# (c) 2009 Marcos Dione <mdione@grulic.org.ar>

import datetime

from lalita import Plugin

class Seen(Plugin):
    def init(self, config):
        self.iolog= {}
        self.saidlog= {}
        self.config= dict (clever=True)
        self.config.update (config)

        self.register(self.events.JOIN, self.joined)
        self.register(self.events.PART, self.parted)
        self.register(self.events.PUBLIC_MESSAGE, self.message)
        self.register(self.events.TALKED_TO_ME, self.message)
        self.register(self.events.COMMAND, self.seen, ['seen', 'last'])

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
            if what in ('joined', 'parted'):
                self.iolog[nick] = (what, datetime.datetime.now())
            else:
                self.saidlog[nick] = (what, datetime.datetime.now())
            self.logger.debug("logged %s: %s", nick, what)

    def seen (self, user, channel, command, nick):
        if not self.config['clever'] or nick not in (self.nickname, user):
            what1, when1 = self.iolog.get (nick, (None, None))
            what2, when2 = self.saidlog.get (nick, (None, None))
            self.logger.debug (str ((what1, when1, what2, when2)))
            # didn't se him at all or he has just been silent
            # NOTE: I know this can be reduced a little,
            # but this way is more understandable at first sight
            if (when1 is None and when2 is None) or (command=='last' and when2 is None):
                what= u"%s: me lo deje en la otra pollera :|" % user
            # seen him join or part and,
            # either didn't hearm him say anython,
            # or just was too long before he joined/left
            elif command=='seen' and when1 is not None and (when2 is None or when1>when2):
                if what1=='joined':
                    what= u"%s: [%s] -- joined" % (user, when1.strftime ("%x %X"))
                elif what1=='parted':
                    what= u"%s: [%s] -- parted" % (user, when1.strftime ("%x %X"))
            else: # command=='last' or when1<when2 or when1 is None
                what= u"%s: [%s] %s" % (user, when2.strftime ("%x %X"), what2)
        elif nick==self.nickname:
            what= u"%s: acástoi, papafrita!" % user
        elif nick==user:
            what= u"%s: andá mirate en el espejo del baño" % user

        self.say (channel, what)

# end
