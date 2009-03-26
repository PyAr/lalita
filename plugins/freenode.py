# -*- coding: utf8 -*-

# (c) 2009 Marcos Dione <mdione@grulic.org.ar>

import logging
logger = logging.getLogger ('ircbot.plugins.freenode')
logger.setLevel (logging.DEBUG)

from core import dispatcher
from core import events

class Register (object):
    def __init__ (self, config, params):
        register= params['register']
        register (events.PRIVATE_MESSAGE, self.register)
        self.config= config
        # print config

    def register (self, user, msg):
        logger.debug ("%s: %s" % (user, msg))
        # print "%s: %s" % (user, msg)
        # if user=='NickServ!NickServ@services.' and 'identify' in msg:
        if user=='NickServ':
            if '/msg NickServ identify' in msg:
                return (user, "identify zaraza")
            elif 'Invalid password' in msg:
                logger.warn ('invalid password!?!')

# end
