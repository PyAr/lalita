# -*- coding: utf-8 -*-

# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

from randomer_utils.randomer import contestame
import random
import re

from lalita import Plugin

class Randomer(Plugin):

    def init(self, config):
        self._internals = {}
        pattern = re.compile('.*%s.*' % self.nickname)
        self.register(self.events.TALKED_TO_ME, self.answer)
        self.register(self.events.PUBLIC_MESSAGE, self.answer, pattern)
        self.register(self.events.PRIVATE_MESSAGE, self.priv_answer)

    def priv_answer(self, user, *args):
        if not user or user.lower() in ['nickserv', 'chanserv']:
            return

        self.logger.debug("priv_answer, user: %s", user)
        self.answer(user, None, *args)

    def answer(self, user, channel, *args):
        comment = u' '.join(args)
        whom = random.random() > 0.9 and '%s: ' % user or ''
        where = channel is not None and channel or user
        self.say(where, '%s%s' % (whom, contestame(comment)))
