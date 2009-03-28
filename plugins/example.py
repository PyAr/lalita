# -*- coding: utf8 -*-

from lalita import Plugin

# This is an example plugin, enjoy.

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

class Example(Plugin):

    def start(self, config):
        # register to stuff
        self.register(self.events.TALKED_TO_ME, self.talked_to_me)
        self.register(self.events.COMMAND, self.command_foo, ("foo",))
        self.register(self.events.COMMAND, self.command_bar, ("bar",))

    def talked_to_me(self, user, channel, msg):
        print "==================== talked_to_me"
        txt = u"Hola %s, mi nombre es %s, :)" % (user, self.nickname)
        return [(channel, txt)]

    def command_foo(self, user, channel, command, *args):
        u"@foo txt: repite lo recibido... no sirve para nada, pero es un "\
         "buen ejemplo."
        print "==================== command foo"
        if args:
            txt = args[0]
        else:
            txt = u"%s: Me tenés que decir algo para que lo repita!" % user
        return [(channel, txt)]

    def command_bar(self, user, channel, command, *args):
        u"""@bar: Zen de Python, al azar."""
        print "==================== command foo"
        txt = random.choice(zen)
        return [(channel, "Del Zen de Python:"), (channel, txt)]
