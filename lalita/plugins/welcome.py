# -*- coding: utf8 -*-

# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

import os
import shelve
from lalita import Plugin


class Welcome(Plugin):
    '''Teach Lalita to welcome users joining the channel.'''

    def init(self, config):
        self.logger.info('Welcome plugin init! config: %s', config)

        self.welcome_message = '%s: Bienvenido a %s!'
        self.instructions_message = 'Aqui van algunas instrucciones'

        # self.register_translation(self, TRANSLATION_TABLE)
        base = config.get('basedir', None)
        if base is not None:
            base = os.path.join(base, config.get('channel_folder', ''))
            if not os.path.exists(base):
                os.makedirs(base)
            self.known_users = shelve.open(os.path.join(base, 'users'))
        else:
            self.known_users = {}

        self.register(self.events.JOIN, self.user_joined)

    def new_user(self, user):
        return user not in self.known_users

    def add_user(self, channel, user):
        self.known_users[user] = channel

    def user_joined(self, user, channel):
        if user.startswith(u'pyarense'):
            self.logger.debug("%s joined %s", user, channel)
            self.say(channel, self.welcome_message, user, channel)
            self.say(user, self.instructions_message)
        elif self.new_user(user):
            self.add_user(channel, user)
            self.logger.debug("%s joined %s", user, channel)
            self.say(channel, self.welcome_message, user, channel)
