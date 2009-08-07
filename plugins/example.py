# -*- coding: utf8 -*-

# this is the only stuff from lalita you need to import
from lalita import Plugin

# there's an example with twisted, but you can write plugins without
# using this advanced stuff
from twisted.internet import defer


class Example(Plugin):
    '''This is an example plugin, enjoy.'''

    def init(self, config):
        # register to stuff
        self.logger.info("Init! config: %s", config)
        self.register(self.events.TALKED_TO_ME, self.talked_to_me)
        self.register(self.events.PRIVATE_MESSAGE, self.private)
        self.register(self.events.COMMAND, self.command_foo, ("foo",))
        self.register(self.events.COMMAND, self.command_bar, ("bar",))
        self.register(self.events.COMMAND, self.command_twisted, ("enroscau",))

    def private(self, user, text):
        self.logger.debug("private message from %s: %s", user, text)
        self.say(user, u'Me dijiste "%s"' % text)

    def talked_to_me(self, user, channel, msg):
        self.logger.debug("%s talked to me in: %s", user, channel, msg)
        txt = u"Hola %s, mi nombre es %s, :)" % (user, self.nickname)
        self.say(channel, txt)

    def command_foo(self, user, channel, command, *args):
        u"@foo txt: repite lo recibido... no sirve para nada, pero es un "\
         "buen ejemplo."
        self.logger.debug("command %s from %s (args: %s)", command, user, args)
        if args:
            txt = args[0]
        else:
            txt = u"%s: Me tenés que decir algo para que lo repita!" % user
        self.say(channel, txt)

    def command_bar(self, user, channel, command, *args):
        u"""@bar: Zen de Python, al azar."""
        self.logger.debug("command %s from %s (args: %s)", command, user, args)
        self.say(channel, u"Del Zen de Python:")
        self.say(channel, u"    " + random.choice(zen))

    def _twisted_example(self, info):
        user, channel = info
        self.say(channel, "%s: Hola! Estamos deferredeando como locas!" % user)

    def command_twisted(self, user, channel, command, *args):
        u"""enroscau: Ejemplo usando un Deferred."""
        self.logger.debug("command %s from %s (args: %s)", command, user, args)
        d = defer.Deferred()
        d.addCallback(self._twisted_example)
        self.say(user, "Te prometo a futuro un saludo en el canal")

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
