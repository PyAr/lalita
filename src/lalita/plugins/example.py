# -*- coding: utf8 -*-

# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

# this is the only stuff from lalita you need to import
from lalita import Plugin

# there's an example with twisted, but you can write plugins without
# using this advanced stuff
from twisted.internet import defer

TRANSLATION_TABLE = {
    u'Me dijiste "%s"': {
        'en': u'You told me "%s"',
        'it': u'Mi hai detto "%s"',
    },

    u"Hola %s, mi nombre es %s, :)": {
        'en': u"Hi %s, my name is %s, :)",
        'it': u"Chao %s, il mio nome è %s, :)",
    },

    u"%s: Me tenés que decir algo para que lo repita!": {
        'en': u"%s: You have to tell me something for me to repeat!",
        'it': u"%s: Devi dirmi qualcosa per me di ripetere!",
    },

    u"%s: Hola! Estamos deferredeando como locas!": {
        'en': u"%s: Hi! We're deferring like crazy!",
        'it': u"%s: Chao! Stiamo facendo 'deferreds' come pazzi!",
    },

    u"Te prometo a futuro un saludo en el canal": {
        'en': u"I promise a greeting in the channel for the future",
        'it': u"Ti prometto un saluto nel canale per il futuro",
    },

    u"Del Zen de Python:": {
        'en': u"From the Zen of Python:",
        'it': u"Dal Zen di Python:",
    },
}


class Example(Plugin):
    '''This is an example plugin, enjoy.'''

    def init(self, config):
        # register the translation table for our messages
        self.register_translation(self, TRANSLATION_TABLE)

        # log that we started
        self.logger.info("Init! config: %s", config)

        # register our methods to the events
        self.register(self.events.TALKED_TO_ME, self.talked_to_me)
        self.register(self.events.PRIVATE_MESSAGE, self.private)
        self.register(self.events.COMMAND, self.command_foo, ("foo",))
        self.register(self.events.COMMAND, self.command_bar, ("bar",))
        self.register(self.events.COMMAND, self.command_twisted, ("enroscau",))

    def private(self, user, text):
        self.logger.debug("private message from %s: %s", user, text)
        self.say(user, u'Me dijiste "%s"', text)

    def talked_to_me(self, user, channel, msg):
        self.logger.debug("%s talked to me in %s: %s", user, channel, msg)
        txt = u"Hola %s, mi nombre es %s, :)"
        self.say(channel, txt, user, self.nickname)

    def command_foo(self, user, channel, command, *args):
        u"@foo txt: sólo repite lo recibido."
        self.logger.debug("command %s from %s (args: %s)", command, user, args)
        if args:
            self.say(channel, args[0])
        else:
            txt = u"%s: Me tenés que decir algo para que lo repita!"
            self.say(channel, txt, user)

    def command_bar(self, user, channel, command, *args):
        u"""@bar: Zen de Python, al azar."""
        self.logger.debug("command %s from %s (args: %s)", command, user, args)
        self.say(channel, u"Del Zen de Python:")
        self.say(channel, u"    " + random.choice(zen))

    def _twisted_example(self, info):
        user, channel = info
        self.say(channel, u"%s: Hola! Estamos deferredeando como locas!", user)

    def command_twisted(self, user, channel, command, *args):
        u"""enroscau: Ejemplo usando un Deferred."""
        self.logger.debug("command %s from %s (args: %s)", command, user, args)
        d = defer.Deferred()
        d.addCallback(self._twisted_example)
        self.say(user, u"Te prometo a futuro un saludo en el canal")

        # trigger the deferred: normally this will be done by other
        # components: web access, database access, etc.
        d.callback((user, channel))

        # return the deferred: this is mandatory for this "deferred
        # executions" to work ok
        return d


# this is only to get the Zen of Python, by Tim Peters
import sys
import StringIO
import random
s = StringIO.StringIO()
ant = sys.stdout
sys.stdout = s
import this
sys.stdout = ant
s.seek(0)
s.readline()
s.readline()
zen = [unicode(x.strip()) for x in s.readlines()]
