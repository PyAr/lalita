# -*- coding: utf8 -*-

# (c) 2009 Marcos Dione <mdione@grulic.org.ar>

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
                logger.warn('invalid password!?!')
            elif 'You are now identified' in msg:
                logger.info('successfuly identified')

# end
