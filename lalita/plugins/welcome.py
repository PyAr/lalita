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
        self.register(self.events.JOIN, self.user_joined)
        self.logged_users = []

    @property
    def default_message(self):
        return u'$user: Bienvenido a $channel!'

    def new_user(self, user):
        return user in self.logged_users

    def add_user(self, user):
        self.logged_users.append(user)

    def user_joined(self, user, channel):
        if user.startswith(u'pyarense_ij'):
            self.logger.debug("%s joined %s", user, channel)
            self.say(channel, self.default_message, user, channel)
        else:
            if self.new_user(user):
                self.add_user(user)
                self.logger.debug("%s joined %s", user, channel)
                self.say(channel, self.default_message, user, channel)
