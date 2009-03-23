# -*- coding: utf8 -*-

# This is not a standard test case, but a special plugin that expect
# to be instantiated twice to talk to each other

from twisted.internet import reactor

from core import dispatcher
from core import events as evt


class TestPlugin(object):
    def __init__(self, config, params):
        self.other = config["general"]["other"]
        register = params["register"]
        self.nickname = params["nickname"]

        # register to stuff
        register(evt.CONNECTION_MADE, self.conn_made)
        register(evt.CONNECTION_LOST, self.conn_lost)
        register(evt.SIGNED_ON, self.signed)
        register(evt.JOINED, self.joined)
        register(evt.TALKED_TO_ME, self.talked_to_me)

        if self.nickname == "itchy":
            register(evt.COMMAND, self.command_foo, ("foo",))
        else:
            register(evt.COMMAND, self.command_bar, ("bar",))

        # helpers for testing
        self.state = "disconnected"

    def _check_state(self, from_st, to_st):
        if self.state == from_st:
            self.state = to_st
        else:
            raise ValueError(
                "Bad state going to %s: %r" % (to_st, self.state))

    def conn_made(self):
        self._check_state("disconnected", "connected")
        print "==================== Connection made!"

    def conn_lost(self):
        print "==================== Connection lost!"

    def signed(self):
        self._check_state("connected", "signed")
        print "==================== Signed!"

    def joined(self, channel):
        self._check_state("signed", "joined")
        print "==================== Joined!"
        if self.nickname == "itchy":
            msg = u"Hola! Soy itchy!"
        else:
            msg = u"itchy: Hola!" # scratchy says
        return (channel, msg)

    def talked_to_me(self, user, channel, msg):
        print "==================== Talked to me!", user
        if self.state == "joined":
            self.state = "msg1"
            if msg.strip() != "Hola!":
                raise ValueError("Bad message 1: %r" % msg)
            return (channel, u"%s, ¿cómo estás?" % user) # itchy says
        elif self.state == "msg1":
            self.state = "msg2"
            if msg.strip() != u"¿cómo estás?":
                raise ValueError("Bad message 2: %r" % msg)
            return (channel, u"@foo") # scratchy says
        else:
            raise ValueError("Bad state in talked_to_me")

    def command_foo(self, user, channel, command, *args):
        print "==================== Command! Foo", user, command, args
        if self.state == "msg2":
            self.state = "cmd1"
            if command != "foo" or args:
                raise ValueError("Bad info in cmd1: %r %r" % (command, args))
            return (channel, u"@bar baz") # itchy says
        elif self.state == "cmd2":
            self.state = "cmd3"
            if command != "foo" or args != ("mate", "esta"):
                raise ValueError("Bad info in cmd3: %r %r" % (command, args))
            return (channel, u":D") # itchy says
        else:
            raise ValueError("Bad state in command")

    def command_bar(self, user, channel, command, *args):
        print "==================== Command!", user, command, args
        if self.state == "cmd1":
            self.state = "cmd2"
            if command != "bar" or args != ("baz",):
                raise ValueError("Bad info in cmd2: %r %r" % (command, args))
            return (channel, u"@foo mate esta") # scratchy says
        else:
            raise ValueError("Bad state in command")







