# -*- coding: utf8 -*-

# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

# This is not a standard test case, but a special plugin that expect
# to be instantiated twice to talk to each other


from lalita import Plugin


class TestPlugin(Plugin):
    def init(self, config):
        self.other = config["other"]

        # register to stuff
        self.register(self.events.CONNECTION_MADE, self.conn_made)
        self.register(self.events.CONNECTION_LOST, self.conn_lost)
        self.register(self.events.SIGNED_ON, self.signed)
        self.register(self.events.JOINED, self.joined)
        self.register(self.events.TALKED_TO_ME, self.talked_to_me)

        if self.nickname == "itchy":
            self.register(self.events.COMMAND, self.command_foo, ("foo",))
        else:
            self.register(self.events.COMMAND, self.command_bar, ("bar",))

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
        self.logger.info("%s: Connection made!", self.nickname)

    def conn_lost(self):
        self.logger.info("%s: Connection lost!", self.nickname)

    def signed(self):
        self._check_state("connected", "signed")
        self.logger.info("%s: Signed!", self.nickname)

    def joined(self, channel):
        self._check_state("signed", "joined")
        self.logger.info("%s: Joined!", self.nickname)
        if self.nickname == "itchy":
            msg = u"Hola! Soy itchy!"
        else:
            msg = u"itchy: Hola!" # scratchy says
        self.say(channel, msg)

    def talked_to_me(self, user, channel, msg):
        self.logger.info("%s: %s talked to me (%s)", self.nickname, user, msg)
        if self.nickname == "itchy" and self.state == "joined":
            self.state = "msg"
            if msg != "Hola!":
                raise ValueError("Bad message 1: %r" % msg)
            self.say(channel, u"%s, ¿cómo estás?" % user) # itchy says
        elif self.nickname == "scratchy" and self.state == "joined":
            self.state = "msg"
            if msg != u"¿cómo estás?":
                raise ValueError("Bad message 2: %r" % msg)
            self.say(channel, u"@foo") # scratchy says
        else:
            raise ValueError("Bad state in talked_to_me")

    def command_foo(self, user, channel, command, *args):
        self.logger.info("%s: command from %s (%s, %s)",
                         self.nickname, user, command, args)
        if self.nickname == "itchy" and self.state == "msg":
            self.state = "cmd"
            if command != "foo" or args:
                raise ValueError("Bad info in cmd1: %r %r" % (command, args))
            self.say(channel, u"@bar baz") # itchy says
        elif self.nickname == "itchy" and self.state == "cmd":
            self.state = "done"
            if command != "foo" or args != ("mate", "esta"):
                raise ValueError("Bad info in cmd3: %r %r" % (command, args))
            self.say(channel, u":D") # itchy says
        else:
            raise ValueError("Bad state in command")

    def command_bar(self, user, channel, command, *args):
        self.logger.info("%s: command from %s (%s, %s)",
                         self.nickname, user, command, args)
        if self.nickname == "scratchy" and self.state == "msg":
            self.state = "done"
            if command != "bar" or args != ("baz",):
                raise ValueError("Bad info in cmd2: %r %r" % (command, args))
            self.say(channel, u"@foo mate esta") # scratchy says
        else:
            raise ValueError("Bad state in command")







