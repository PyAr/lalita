# -*- coding: utf8 -*-

import logging
logger = logging.getLogger ('ircbot.freenode')
logger.setLevel (logging.DEBUG)

from core import dispatcher
from core import events

class Freenode (object):
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
