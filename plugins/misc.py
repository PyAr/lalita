# -*- coding: utf8 -*-

# (c) 2009 Marcos Dione <mdione@grulic.org.ar>

import logging
logger = logging.getLogger ('ircbot.plugins.misc')
logger.setLevel (logging.DEBUG)

class Ping (object):
    def __init__ (self, config, events, params):
        register= params['register']
        register (events.COMMAND, self.ping, ['ping'])

    def ping (self, user, channel, command):
        return [(channel, u"%s: pong" % user)]

# end
