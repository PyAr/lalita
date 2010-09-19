# -*- coding: utf8 -*-

# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

from lalita import Plugin

class Sum(Plugin):
    """Ejemplo que suma los nros pasados."""

    def init(self, config):
        self.register(self.events.TALKED_TO_ME, self.action)

    def action(self, user, channel, msg):
        u"Suma los números recibidos."
        result = sum(int(x) for x in msg.split())
        self.say(channel, u"%s, la suma es %d", user, result)
