# -*- coding: utf8 -*-

# (c) 2009 Marcos Dione <mdione@grulic.org.ar>

import datetime

from lalita import Plugin

class Seen(Plugin):
    '''Plugin that implements the "seen" and "last" commands.'''
    def init(self, config):
        self.iolog = {}
        self.saidlog = {}
        self.config = dict(clever=True)
        self.config.update(config)

        self.register(self.events.JOIN, self.joined)
        self.register(self.events.LEFT, self.left)
        self.register(self.events.QUIT, self.quit)
        self.register(self.events.PUBLIC_MESSAGE, self.message)
        self.register(self.events.TALKED_TO_ME, self.message)
        self.register(self.events.COMMAND, self.seen, ['seen'])
        self.register(self.events.COMMAND, self.last, ['last'])

    def joined(self, nick, channel):
        '''Logs that the user has joined.'''
        self.logger.debug("%s joined %s", nick, channel)
        self.iolog[nick] = ("joined", datetime.datetime.now())

    def left(self, nick, channel):
        '''Logs that the user has left.'''
        self.logger.debug("%s left %s", nick, channel)
        self.iolog[nick] = ("left", datetime.datetime.now())

    def quit(self, nick, message):
        '''Logs that the user has quit.'''
        self.logger.debug("%s quit IRC (%s)", nick, message)
        self.iolog[nick] = ("quit IRC (%s)" % message, datetime.datetime.now())

    def message(self, nick, channel, msg):
        '''Logs something said by the user.'''
        self.logger.debug("%s said %s", nick, msg)
        self.saidlog[nick] = (msg, datetime.datetime.now())

    def seen(self, user, channel, command, nick):
        u'''Indica cuando fue visto por última vez un usuario y qué hizo.'''
        if self.config['clever'] and nick == self.nickname:
            self.say(channel, u"%s: acástoi, papafrita!" % user)
            return

        if self.config['clever'] and nick == user:
            self.say(channel, u"%s: andá mirate en el espejo del baño" % user)
            return

        what1, when1 = self.iolog.get(nick, (None, None))
        what2, when2 = self.saidlog.get(nick, (None, None))
        self.logger.debug(str((what1, when1, what2, when2)))

        # didn't se him at all or he has just been silent
        if when1 is None and when2 is None:
            self.say(channel, u"%s: se me quedó en la otra pollera :|" % user)
            return

        # seen him join or part and,
        # either didn't hear him say anything,
        # or just was too long before he joined/left
        if when1 is not None and (when2 is None or when1>when2):
            what = u"%s: [%s] -- %s" % (user, when1.strftime ("%x %X"), what1)
        else:
            what = u"%s: [%s] %s" % (user, when2.strftime ("%x %X"), what2)
        self.say (channel, what)

    def last(self, user, channel, command, nick):
        u'''Muestra que fue lo último que dijo un usuario.'''
        if self.config['clever'] and nick == self.nickname:
            self.say(channel, u'%s: lo último fue "lo último fue ..."' % user)
            return

        if self.config['clever'] and nick == user:
            self.say(channel, u"%s: me tiraste la órden" % user)
            return

        what1, when1 = self.iolog.get(nick, (None, None))
        what2, when2 = self.saidlog.get(nick, (None, None))
        self.logger.debug(str((what1, when1, what2, when2)))

        # he has just been silent
        if when2 is None:
            self.say(channel, u"%s: yo no oí nada..." % user)
            return

        self.say(channel,
                 u"%s: [%s] %s" % (user, when2.strftime ("%x %X"), what2))
