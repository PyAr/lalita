# -*- coding: utf8 -*-

# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

from lalita import Plugin

class Register(Plugin):
    def init(self, config):
        self.config = config
        self.register(self.events.PRIVATE_MESSAGE, self.freenode_register)
        self.register(self.events.CONNECTION_MADE, self._register)

    def _register(self, *a):
        self.logger.info("Identifying with NickServ: %s", a)
        self.say("NickServ", u"identify %s" % self.config['password'])

    def freenode_register(self, user, msg):
        self.logger.info("%s: %s", user, msg)
        if user == 'NickServ':
            if 'Invalid password' in msg:
                self.logger.warning('invalid password!?!')
            elif 'You are now identified' in msg:
                self.logger.info('successfuly identified')
            else:
                self.logger.warning("Unknown NickServ message: %r", msg)
