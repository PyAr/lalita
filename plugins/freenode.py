# -*- coding: utf8 -*-

# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

from lalita import Plugin

class Register(Plugin):
    def init(self, config):
        self.register(self.events.PRIVATE_MESSAGE, self.freenode_register)
        self.config = config
        # print config

    def freenode_register(self, user, msg):
        self.logger.debug("%s: %s", user, msg)
        if user == 'NickServ':
            if '/msg NickServ identify' in msg:
                self.say(user, u"identify %s" % self.config['password'])
            elif 'Invalid password' in msg:
                self.logger.warn('invalid password!?!')
            elif 'You are now identified' in msg:
                self.logger.info('successfuly identified')

# end
