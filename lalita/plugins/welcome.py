# -*- coding: utf8 -*-

# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file


import string
from lalita import Plugin


class Welcome(Plugin):
    '''Teach Lalita to welcome users joining the channel.'''

    def init(self, config):
        self.logger.info('Welcome plugin init! config: %s', config)
        default_message = u'$user: Bienvenido a $channel!'
        welcome_message = config.get('message', default_message)
        self.template = string.Template(welcome_message)
        self.register(self.events.JOIN, self.user_joined)

    def user_joined(self, user, channel):
        if user.startswith(u'pythonista'):
            self.logger.debug("%s joined %s", user, channel)
            message = self.template.safe_substitute(user=user, channel=channel)
            self.say(channel, message)
