# -*- coding: utf8 -*-

# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file


from lalita import Plugin


class Welcome(Plugin):
    '''Teach Lalita to welcome users joining the channel.'''

    def init(self, config):
        self.logger.info('Welcome plugin init! config: %s', config)
        self.welcome_message = config.get('message', u'%s: Bienvenido a %s!')
        self.register(self.events.JOIN, self.user_joined)

    def user_joined(self, user, channel):
        self.logger.debug("%s joined %s", user, channel)
        self.say(channel, self.welcome_message, user, channel)
