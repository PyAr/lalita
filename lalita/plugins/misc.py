# -*- coding: utf8 -*-

# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

from lalita import Plugin

class Ping(Plugin):
    '''Plugin for the "ping" functionality.'''

    def init(self, config):
        self.logger.debug("Init! config: %s", config)
        self.register(self.events.COMMAND, self.ping, ['ping'])

    def ping(self, user, channel, command):
        u'''Sólo contesto.'''
        self.logger.debug("let's play ping pong with %s!" % user)
        self.say(channel, u"%s: pong", user)
