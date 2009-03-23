
import unittest
import re

from twisted.trial.unittest import TestCase as TwistedTestCase
from twisted.internet import defer, reactor

from core import events
from core import dispatcher
from config import servers
import ircbot

server = servers["perrito"]
ircbot_factory = ircbot.IRCBotFactory(server)

bot = ircbot.IrcBot()
bot.factory = ircbot_factory

#boo = reactor.connectTCP(server.get('host', '10.100.0.175'),

MY_NICKNAME = server['nickname']


class EasyDeferredTests(TwistedTestCase):
    def setUp(self):
        self.deferred = defer.Deferred()
        self.timeout = 1

    def deferredAssertEqual(self, deferred, a, b):
        def f(_):
            self.assertEqual(a, b)
            return _
        deferred.addCallback(f)


class TestRegister(unittest.TestCase):
    def setUp(self):
        self.disp = dispatcher.Dispatcher()

    def test_method_exists(self):
        self.assertTrue(hasattr(self.disp, "register"))

    def test_empty(self):
        '''Test no registration.'''
        self.assertEqual(self.disp._callbacks, {})

    def test_one_event(self):
        '''Test registration to events.'''
        def f(): pass

        self.disp.register(events.CONNECTION_MADE, f)
        self.assertEqual(self.disp._callbacks,
                         {events.CONNECTION_MADE: [(f, None)]})

    def test_one_event_regexp(self):
        '''Test registration to events with regexp.'''
        def f(): pass

        self.disp.register(events.CONNECTION_MADE, f, "foo")
        self.assertEqual(self.disp._callbacks,
                         {events.CONNECTION_MADE: [(f, "foo")]})

    def test_one_event_twice(self):
        '''Test two registrations to the same events.'''
        def f(): pass
        def g(): pass

        self.disp.register(events.CONNECTION_MADE, f)
        self.disp.register(events.CONNECTION_MADE, g)
        self.assertEqual(self.disp._callbacks,
                         {events.CONNECTION_MADE: [(f, None), (g, None)]})

    def test_mixed(self):
        '''Test several registration, several events.'''
        def f(): pass
        def g(): pass
        def h(): pass

        self.disp.register(events.CONNECTION_MADE, f)
        self.disp.register(events.CONNECTION_LOST, g)
        self.disp.register(events.CONNECTION_MADE, h)
        self.assertEqual(self.disp._callbacks,
                            {events.CONNECTION_MADE: [(f, None), (h, None)],
                             events.CONNECTION_LOST: [(g, None)]})


class TestPush(EasyDeferredTests):

    def setUp(self):
        super(TestPush, self).setUp()
        self.disp = dispatcher.Dispatcher()

    def test_event_noarg(self):
        '''Test pushing events with no args.'''
        def f():
            self.deferred.callback(True)
            return ""

        self.disp.register(events.CONNECTION_MADE, f)
        self.disp.push(events.CONNECTION_MADE)
        return self.deferred

    def test_event_with_args(self):
        '''Test pushing events with args.'''
        def f(arg):
            self.deferredAssertEqual(self.deferred, arg, "reason")
            self.deferred.callback(True)
            return ""

        self.disp.register(events.CONNECTION_LOST, f)
        self.disp.push(events.CONNECTION_LOST, "reason")
        return self.deferred

    def test_deferred(self):
        '''Test pushing events with deferred results.'''

        def f():
            d = defer.Deferred()
            self.deferred.callback(True)
            return d

        self.disp.register(events.CONNECTION_MADE, f)
        self.disp.push(events.CONNECTION_MADE)
        return self.deferred


class TestEvents(EasyDeferredTests):

    def setUp(self):
        super(TestEvents, self).setUp()
        self.disp = dispatcher.dispatcher
        self.disp._callbacks = {}

    def test_connection_made(self):
        '''Test connection made.'''
        def f():
            self.deferred.callback(True)
            return ""

        self.disp.register(events.CONNECTION_MADE, f)
        self.disp.push(events.CONNECTION_MADE)
        return self.deferred

    def test_connection_lost(self):
        '''Test connection lost.'''
        def f(arg):
            self.deferredAssertEqual(self.deferred, arg, "reason")
            self.deferred.callback(True)
            return ""

        self.disp.register(events.CONNECTION_LOST, f)
        self.disp.push(events.CONNECTION_LOST, "reason")
        return self.deferred

    def test_signed_on(self):
        '''Test SIGNED_ON.'''
        def f():
            self.deferred.callback(True)
            return ""

        self.disp.register(events.SIGNED_ON, f)
        self.disp.push(events.SIGNED_ON)
        return self.deferred

    def test_joined(self):
        '''Test JOINED.'''
        def f(arg):
            self.deferredAssertEqual(self.deferred, arg, "channel")
            self.deferred.callback(True)
            return ""

        self.disp.register(events.JOINED, f)
        self.disp.push(events.JOINED, "channel")
        return self.deferred

    def test_private_message_raw(self):
        '''Test PRIVATE_MESSAGE raw.'''
        def f(a, b):
            self.deferredAssertEqual(self.deferred, a, "user")
            self.deferredAssertEqual(self.deferred, b, "msg")
            self.deferred.callback(True)
            return ""

        self.disp.register(events.PRIVATE_MESSAGE, f)
        self.disp.push(events.PRIVATE_MESSAGE, "user", "msg")
        return self.deferred

    def test_private_message_regexp(self):
        '''Test PRIVATE_MESSAGE with regexp.'''
        def f(a, b):
            self.deferredAssertEqual(self.deferred, a, "user")
            self.deferredAssertEqual(self.deferred, b, "hola mundo")
            self.deferred.callback(True)
            return ""

        regexp = re.compile("^hola.*$")
        self.disp.register(events.PRIVATE_MESSAGE, f, regexp)
        self.disp.push(events.PRIVATE_MESSAGE, "user", "esta no pasa")
        self.disp.push(events.PRIVATE_MESSAGE, "user", "hola mundo")
        return self.deferred

    def test_talked_to_me_raw(self):
        '''Test TALKED_TO_ME raw.'''
        def f(a, b, c):
            self.deferredAssertEqual(self.deferred, a, "user")
            self.deferredAssertEqual(self.deferred, b, "channel")
            self.deferredAssertEqual(self.deferred, c, "msg")
            self.deferred.callback(True)
            return ""

        self.disp.register(events.TALKED_TO_ME, f)
        self.disp.push(events.TALKED_TO_ME, "user", "channel", "msg")
        return self.deferred

    def test_talked_to_me_regexp(self):
        '''Test TALKED_TO_ME with regexp.'''
        def f(a, b, c):
            self.deferredAssertEqual(self.deferred, a, "user")
            self.deferredAssertEqual(self.deferred, b, "channel")
            self.deferredAssertEqual(self.deferred, c, "hola mundo")
            self.deferred.callback(True)
            return ""

        regexp = re.compile("^hola.*$")
        self.disp.register(events.TALKED_TO_ME, f, regexp)
        self.disp.push(events.TALKED_TO_ME, "user", "channel", "esta no pasa")
        self.disp.push(events.TALKED_TO_ME, "user", "channel", "hola mundo")
        return self.deferred

    def test_public_raw(self):
        '''Test PUBLIC_MESSAGE simple.'''
        def f(a, b, c):
            self.deferredAssertEqual(self.deferred, a, "user")
            self.deferredAssertEqual(self.deferred, b, "channel")
            self.deferredAssertEqual(self.deferred, c, "msg")
            self.deferred.callback(True)
            return ""

        self.disp.register(events.PUBLIC_MESSAGE, f)
        self.disp.push(events.PUBLIC_MESSAGE, "user", "channel", "msg")
        return self.deferred

    def test_public_regexp(self):
        '''Test PUBLIC_MESSAGE with regexp.'''
        def f(a, b, c):
            self.deferredAssertEqual(self.deferred, a, "user")
            self.deferredAssertEqual(self.deferred, b, "channel")
            self.deferredAssertEqual(self.deferred, c, "hola mundo")
            self.deferred.callback(True)
            return ""

        regexp = re.compile("^hola.*$")
        self.disp.register(events.PUBLIC_MESSAGE, f, regexp)
        self.disp.push(events.PUBLIC_MESSAGE, "user", "channel", "esta no")
        self.disp.push(events.PUBLIC_MESSAGE, "user", "channel", "hola mundo")
        return self.deferred

    def test_command_noargs(self):
        '''Test COMMAND with no arguments.'''
        def f(a, b, c):
            self.deferredAssertEqual(self.deferred, a, "user")
            self.deferredAssertEqual(self.deferred, b, "channel")
            self.deferredAssertEqual(self.deferred, c, "command")
            self.deferred.callback(True)
            return ""

        self.disp.register(events.COMMAND, f)
        self.disp.push(events.COMMAND, "user", "channel", "command")
        return self.deferred

    def test_command_onearg(self):
        '''Test COMMAND with one argument.'''
        def f(a, b, c, d):
            self.deferredAssertEqual(self.deferred, a, "user")
            self.deferredAssertEqual(self.deferred, b, "channel")
            self.deferredAssertEqual(self.deferred, c, "command")
            self.deferredAssertEqual(self.deferred, d, "foo")
            self.deferred.callback(True)
            return ""

        self.disp.register(events.COMMAND, f)
        self.disp.push(events.COMMAND, "user", "channel", "command", "foo")
        return self.deferred

    def test_command_twoargs(self):
        '''Test COMMAND with two arguments.'''
        def f(a, b, c, d, e):
            self.deferredAssertEqual(self.deferred, a, "user")
            self.deferredAssertEqual(self.deferred, b, "channel")
            self.deferredAssertEqual(self.deferred, c, "command")
            self.deferredAssertEqual(self.deferred, d, "foo")
            self.deferredAssertEqual(self.deferred, e, "bar")
            self.deferred.callback(True)
            return ""

        self.disp.register(events.COMMAND, f)
        self.disp.push(events.COMMAND,
                       "user", "channel", "command", "foo", "bar")
        return self.deferred

    def test_action(self):
        '''Test ACTION.'''
        def f(a, b, c):
            self.deferredAssertEqual(self.deferred, a, "user")
            self.deferredAssertEqual(self.deferred, b, "channel")
            self.deferredAssertEqual(self.deferred, c, "msg")
            self.deferred.callback(True)
            return ""

        self.disp.register(events.ACTION, f)
        self.disp.push(events.ACTION, "user", "channel", "msg")
        return self.deferred

