
import unittest
import re

from collections import defaultdict
from twisted.trial.unittest import TestCase as TwistedTestCase
from twisted.internet import defer, reactor

from core import events
from core import dispatcher
from core import Plugin
import ircbot

server = dict(
    encoding='utf8',
    host="0.0.0.0",
    port=6667,
    nickname="test",
    channels=defaultdict(lambda: {}),
    plugins={},
)

ircbot_factory = ircbot.IRCBotFactory(server)
ircbot.logger.setLevel("error")
bot = ircbot.IrcBot()
bot.factory = ircbot_factory
bot.config = ircbot_factory.config
bot.msg = lambda *a:None

MY_NICKNAME = server['nickname']


class EasyDeferredTests(TwistedTestCase):
    def setUp(self):
        self.deferred = defer.Deferred()
        self.timeout = 1

    def deferredAssertEqual(self, a, b):
        def f(_):
            self.assertEqual(a, b)
            return _
        self.deferred.addCallback(f)


class Helper(object):
    def f(self):
        pass
    def g(self):
        pass
    def h(self):
        pass


class TestRegister(unittest.TestCase):
    def setUp(self):
        self.disp = dispatcher.Dispatcher(bot)
        self.disp.init({})

    def test_method_exists(self):
        self.assertTrue(hasattr(self.disp, "register"))

    def test_empty(self):
        '''Test no registration.'''
        self.assertEqual(self.disp._callbacks, {})

    def test_one_event(self):
        '''Test registration to events.'''
        h = Helper()

        self.disp.register(events.CONNECTION_MADE, h.f)
        self.assertEqual(self.disp._callbacks,
                         {events.CONNECTION_MADE: [(h, h.f, None)]})

    def test_one_event_regexp(self):
        '''Test registration to events with regexp.'''
        h = Helper()

        self.disp.register(events.CONNECTION_MADE, h.f, "foo")
        self.assertEqual(self.disp._callbacks,
                         {events.CONNECTION_MADE: [(h, h.f, "foo")]})

    def test_one_event_twice(self):
        '''Test two registrations to the same events.'''
        h = Helper()

        self.disp.register(events.CONNECTION_MADE, h.f)
        self.disp.register(events.CONNECTION_MADE, h.g)
        self.assertEqual(self.disp._callbacks,
                         {events.CONNECTION_MADE: [(h, h.f, None),
                                                   (h, h.g, None)]})

    def test_mixed(self):
        '''Test several registration, several events.'''
        h = Helper()

        self.disp.register(events.CONNECTION_MADE, h.f)
        self.disp.register(events.CONNECTION_LOST, h.g)
        self.disp.register(events.CONNECTION_MADE, h.h)
        self.assertEqual(self.disp._callbacks,
                            {events.CONNECTION_MADE: [(h, h.f, None),
                                                      (h, h.h, None)],
                             events.CONNECTION_LOST: [(h, h.g, None)]})


class TestPush(EasyDeferredTests):

    def setUp(self):
        super(TestPush, self).setUp()
        self.disp = dispatcher.Dispatcher(bot)
        self.disp.init({})

        class Helper(object):
            def f(self, *args):
                return self.test(*args)
        self.helper = Helper()
        self.disp.new_plugin(self.helper, "channel")

    def test_event_noarg(self):
        '''Test pushing events with no args.'''
        def test(*args):
            self.deferredAssertEqual(len(args), 0)
            self.deferred.callback(True)
        self.helper.test = test

        self.disp.register(events.CONNECTION_MADE, self.helper.f)
        self.disp.push(events.CONNECTION_MADE)
        return self.deferred

    def test_event_with_args(self):
        '''Test pushing events with args.'''
        def test(arg):
            self.deferredAssertEqual(arg, "reason")
            self.deferred.callback(True)
        self.helper.test = test

        self.disp.register(events.CONNECTION_LOST, self.helper.f)
        self.disp.push(events.CONNECTION_LOST, "reason")
        return self.deferred

    def test_deferred(self):
        '''Test pushing events with deferred results.'''
        def test():
            d = defer.Deferred()
            self.deferred.callback(True)
            return d
        self.helper.test = test

        self.disp.register(events.CONNECTION_MADE, self.helper.f)
        self.disp.push(events.CONNECTION_MADE)
        return self.deferred


class TestEvents(EasyDeferredTests):

    def setUp(self):
        super(TestEvents, self).setUp()
        self.disp = dispatcher.Dispatcher(bot)
        self.disp.init({})

        class Helper(object):
            def f(self, *args):
                return self.test(*args)
        self.helper = Helper()
        self.disp.new_plugin(self.helper, "channel")

    def test_connection_made(self):
        '''Test connection made.'''
        def test():
            self.deferred.callback(True)
        self.helper.test = test

        self.disp.register(events.CONNECTION_MADE, self.helper.f)
        self.disp.push(events.CONNECTION_MADE)
        return self.deferred

    def test_connection_lost(self):
        '''Test connection lost.'''
        def test(arg):
            self.deferredAssertEqual(arg, "reason")
            self.deferred.callback(True)
        self.helper.test = test

        self.disp.register(events.CONNECTION_LOST, self.helper.f)
        self.disp.push(events.CONNECTION_LOST, "reason")
        return self.deferred

    def test_signed_on(self):
        '''Test SIGNED_ON.'''
        def test():
            self.deferred.callback(True)
        self.helper.test = test

        self.disp.register(events.SIGNED_ON, self.helper.f)
        self.disp.push(events.SIGNED_ON)
        return self.deferred

    def test_joined(self):
        '''Test JOINED.'''
        def test(arg):
            self.deferredAssertEqual(arg, "channel")
            self.deferred.callback(True)
        self.helper.test = test

        self.disp.register(events.JOINED, self.helper.f)
        self.disp.push(events.JOINED, "channel")
        return self.deferred

    def test_private_message_raw(self):
        '''Test PRIVATE_MESSAGE raw.'''
        def test(a, b):
            self.deferredAssertEqual(a, "user")
            self.deferredAssertEqual(b, "msg")
            self.deferred.callback(True)
        self.helper.test = test

        self.disp.register(events.PRIVATE_MESSAGE, self.helper.f)
        self.disp.push(events.PRIVATE_MESSAGE, "user", "msg")
        return self.deferred

    def test_private_message_regexp(self):
        '''Test PRIVATE_MESSAGE with regexp.'''
        def test(a, b):
            self.deferredAssertEqual(a, "user")
            self.deferredAssertEqual(b, "hola mundo")
            self.deferred.callback(True)
        self.helper.test = test

        regexp = re.compile("^hola.*$")
        self.disp.register(events.PRIVATE_MESSAGE, self.helper.f, regexp)
        self.disp.push(events.PRIVATE_MESSAGE, "user", "esta no pasa")
        self.disp.push(events.PRIVATE_MESSAGE, "user", "hola mundo")
        return self.deferred

    def test_talked_to_me_raw(self):
        '''Test TALKED_TO_ME raw.'''
        def test(a, b, c):
            self.deferredAssertEqual(a, "user")
            self.deferredAssertEqual(b, "channel")
            self.deferredAssertEqual(c, "msg")
            self.deferred.callback(True)
        self.helper.test = test

        self.disp.register(events.TALKED_TO_ME, self.helper.f)
        self.disp.push(events.TALKED_TO_ME, "user", "channel", "msg")
        return self.deferred

    def test_talked_to_me_regexp(self):
        '''Test TALKED_TO_ME with regexp.'''
        def test(a, b, c):
            self.deferredAssertEqual(a, "user")
            self.deferredAssertEqual(b, "channel")
            self.deferredAssertEqual(c, "hola mundo")
            self.deferred.callback(True)
        self.helper.test = test

        regexp = re.compile("^hola.*$")
        self.disp.register(events.TALKED_TO_ME, self.helper.f, regexp)
        self.disp.push(events.TALKED_TO_ME, "user", "channel", "esta no pasa")
        self.disp.push(events.TALKED_TO_ME, "user", "channel", "hola mundo")
        return self.deferred

    def test_public_raw(self):
        '''Test PUBLIC_MESSAGE simple.'''
        def test(a, b, c):
            self.deferredAssertEqual(a, "user")
            self.deferredAssertEqual(b, "channel")
            self.deferredAssertEqual(c, "msg")
            self.deferred.callback(True)
        self.helper.test = test

        self.disp.register(events.PUBLIC_MESSAGE, self.helper.f)
        self.disp.push(events.PUBLIC_MESSAGE, "user", "channel", "msg")
        return self.deferred

    def test_public_regexp(self):
        '''Test PUBLIC_MESSAGE with regexp.'''
        def test(a, b, c):
            self.deferredAssertEqual(a, "user")
            self.deferredAssertEqual(b, "channel")
            self.deferredAssertEqual(c, "hola mundo")
            self.deferred.callback(True)
        self.helper.test = test

        regexp = re.compile("^hola.*$")
        self.disp.register(events.PUBLIC_MESSAGE, self.helper.f, regexp)
        self.disp.push(events.PUBLIC_MESSAGE, "user", "channel", "esta no")
        self.disp.push(events.PUBLIC_MESSAGE, "user", "channel", "hola mundo")
        return self.deferred

    def test_command_noargs(self):
        '''Test COMMAND with no arguments.'''
        def test(a, b, c):
            self.deferredAssertEqual(a, "user")
            self.deferredAssertEqual(b, "channel")
            self.deferredAssertEqual(c, "command")
            self.deferred.callback(True)
        self.helper.test = test

        self.disp.register(events.COMMAND, self.helper.f)
        self.disp.push(events.COMMAND, "user", "channel", "command")
        return self.deferred

    def test_command_specific_cmd(self):
        '''Test COMMAND with specific commands.'''
        def test(a, b, c):
            self.deferredAssertEqual(a, "user")
            self.deferredAssertEqual(b, "channel")
            self.deferredAssertEqual(c, "cmd1")
            self.deferred.callback(True)
        self.helper.test = test

        self.disp.register(events.COMMAND, self.helper.f, ["cmd1"])
        self.disp.push(events.COMMAND, "user", "channel", "command") # este no
        self.disp.push(events.COMMAND, "user", "channel", "cmd1") # sip
        return self.deferred

    def test_command_specific_cmds(self):
        '''Test COMMAND with several specific commands.'''
        class Helper(object):
            def __init__(innerself):
                innerself.counter = 0
            def met1(innerself, a, b, c):
                if innerself.counter != 0:
                    self.deferred.errback(ValueError("counter with bad value"))
                self.deferredAssertEqual(a, "user")
                self.deferredAssertEqual(b, "channel")
                self.deferredAssertEqual(c, "cmd1")
                innerself.counter += 1

            def met2(innerself, a, b, c):
                if innerself.counter != 1:
                    self.deferred.errback(ValueError("counter with bad value"))
                self.deferredAssertEqual(a, "user")
                self.deferredAssertEqual(b, "channel")
                self.deferredAssertEqual(c, "cmd2")
                self.deferred.callback(True)
        h = Helper()
        self.disp.new_plugin(h, "channel")

        self.disp.register(events.COMMAND, h.met1, ["cmd1"])
        self.disp.register(events.COMMAND, h.met2, ["cmd2"])
        self.disp.push(events.COMMAND, "user", "channel", "command") # este no
        self.disp.push(events.COMMAND, "user", "channel", "cmd1") # sip
        self.disp.push(events.COMMAND, "user", "channel", "cmd2") # sip
        return self.deferred

    def test_command_specific_cmds_samemeth(self):
        '''Test COMMAND with several specific commands to the same method.'''
        class Helper(object):
            def __init__(innerself):
                innerself.counter = 0
            def met(innerself, a, b, c):
                if innerself.counter == 0:
                    self.deferredAssertEqual(a, "user")
                    self.deferredAssertEqual(b, "channel")
                    self.deferredAssertEqual(c, "cmd1")
                    innerself.counter += 1
                elif innerself.counter == 1:
                    self.deferredAssertEqual(a, "user")
                    self.deferredAssertEqual(b, "channel")
                    self.deferredAssertEqual(c, "cmd2")
                    self.deferred.callback(True)
                else:
                    m = "counter with bad value: %d" % innerself.counter
                    self.deferred.errback(ValueError(m))
                return ("", "")
        h = Helper()
        self.disp.new_plugin(h, "channel")

        self.disp.register(events.COMMAND, h.met, ["cmd1", "cmd2"])
        self.disp.push(events.COMMAND, "user", "channel", "command") # este no
        self.disp.push(events.COMMAND, "user", "channel", "cmd1") # sip
        self.disp.push(events.COMMAND, "user", "channel", "cmd2") # sip
        return self.deferred

    def test_command_onearg(self):
        '''Test COMMAND with one argument.'''
        def test(a, b, c, d):
            self.deferredAssertEqual(a, "user")
            self.deferredAssertEqual(b, "channel")
            self.deferredAssertEqual(c, "command")
            self.deferredAssertEqual(d, "foo")
            self.deferred.callback(True)
        self.helper.test = test

        self.disp.register(events.COMMAND, self.helper.f)
        self.disp.push(events.COMMAND, "user", "channel", "command", "foo")
        return self.deferred

    def test_command_twoargs(self):
        '''Test COMMAND with two arguments.'''
        def test(a, b, c, d, e):
            self.deferredAssertEqual(a, "user")
            self.deferredAssertEqual(b, "channel")
            self.deferredAssertEqual(c, "command")
            self.deferredAssertEqual(d, "foo")
            self.deferredAssertEqual(e, "bar")
            self.deferred.callback(True)
        self.helper.test = test

        self.disp.register(events.COMMAND, self.helper.f)
        self.disp.push(events.COMMAND,
                       "user", "channel", "command", "foo", "bar")
        return self.deferred

    def test_action(self):
        '''Test ACTION.'''
        def test(a, b, c):
            self.deferredAssertEqual(a, "user")
            self.deferredAssertEqual(b, "channel")
            self.deferredAssertEqual(c, "msg")
            self.deferred.callback(True)
        self.helper.test = test

        self.disp.register(events.ACTION, self.helper.f)
        self.disp.push(events.ACTION, "user", "channel", "msg")
        return self.deferred

    def test_user_joined(self):
        '''Test JOIN.'''
        def test(a, b):
            self.deferredAssertEqual(a, "user")
            self.deferredAssertEqual(b, "channel")
            self.deferred.callback(True)
        self.helper.test = test

        self.disp.register(events.JOIN, self.helper.f)
        self.disp.push(events.JOIN, "user", "channel")
        return self.deferred

    def test_user_left(self):
        '''Test LEFT.'''
        def test(a, b):
            self.deferredAssertEqual(a, "user")
            self.deferredAssertEqual(b, "channel")
            self.deferred.callback(True)
        self.helper.test = test

        self.disp.register(events.LEFT, self.helper.f)
        self.disp.push(events.LEFT, "user", "channel")
        return self.deferred

    def test_user_quit(self):
        '''Test QUIT.'''
        def test(a, b):
            self.deferredAssertEqual(a, "user")
            self.deferredAssertEqual(b, "message")
            self.deferred.callback(True)
        self.helper.test = test

        self.disp.register(events.QUIT, self.helper.f)
        self.disp.push(events.QUIT, "user", "message")
        return self.deferred

    def test_user_kicked(self):
        '''Test KICK.'''
        def test(a, b, c, d):
            self.deferredAssertEqual(a, "kickee")
            self.deferredAssertEqual(b, "channel")
            self.deferredAssertEqual(c, "kicker")
            self.deferredAssertEqual(d, "msg")
            self.deferred.callback(True)
        self.helper.test = test

        self.disp.register(events.KICK, self.helper.f)
        self.disp.push(events.KICK, "kickee", "channel", "kicker", "msg")
        return self.deferred


class TestPluginI18n(EasyDeferredTests):

    def setUp(self):
        super(TestPluginI18n, self).setUp()
        self.disp = dispatcher.Dispatcher(bot)
        self.disp.init({})

        class Helper(Plugin):
            def init(self, *args):
                self.register_translation(self, {'a message':{'es':'un mensaje'},
                                                      'with args: %s':{'es':'con args: %s'}})
            def simple(self, user, channel, *args):
                self.say(channel, 'a message')
                self.test(True)
            def withargs(self, user, channel, command, *args):
                self.say(channel, 'with args: %s', command)
                self.test(True)

        self.helper = Helper({'nickname':'helper', 'encoding':'fake'}, 'DEBUG')
        self.disp.config['channels'] = {'channel-es':{'language':'es'}}
        self.old_msg = bot.msg
        self.answer = []
        def g(towhere, msg, _):
            self.answer.append((towhere, msg.decode("utf8")))
        bot.msg = g

    def tearDown(self):
        super(TestPluginI18n, self).tearDown()
        bot.msg = self.old_msg

    def test_simple_message(self):
        self.disp.new_plugin(self.helper, "channel")
        self.helper.init({})
        def test(_):
            self.deferred.callback(True)
        self.helper.test = test
        self.disp.register(events.COMMAND, self.helper.simple)
        self.disp.push(events.COMMAND, 'user', 'channel', 'command', 'foo', 'bar')
        self.deferred.addCallback(
            lambda _: self.assertEqual(self.answer[0][1], u'a message'))
        return self.deferred

    def test_simple_message_es(self):
        self.disp.new_plugin(self.helper, "channel-es")
        self.helper.init({})
        def test(_):
            self.deferred.callback(True)
        self.helper.test = test
        self.disp.register(events.COMMAND, self.helper.simple)
        self.disp.push(events.COMMAND, 'user', 'channel-es', 'command', 'foo', 'bar')
        self.deferred.addCallback(
            lambda _: self.assertEqual(self.answer[0][1], u'un mensaje'))
        return self.deferred

    def test_message_with_args(self):
        self.disp.new_plugin(self.helper, "channel")
        self.helper.init({})
        def test(_):
            self.deferred.callback(True)
        self.helper.test = test
        self.disp.register(events.COMMAND, self.helper.withargs)
        self.disp.push(events.COMMAND, 'user', 'channel', 'command', 'foo', 'bar')
        self.deferred.addCallback(
            lambda _: self.assertEqual(self.answer[0][1],
                                       u'with args: command'))
        return self.deferred

    def test_message_with_args(self):
        self.disp.new_plugin(self.helper, "channel-es")
        self.helper.init({})
        def test(_):
            self.deferred.callback(True)
        self.helper.test = test
        self.disp.register(events.COMMAND, self.helper.withargs)
        self.disp.push(events.COMMAND, 'user', 'channel-es', 'command', 'foo', 'bar')
        self.deferred.addCallback(
            lambda _: self.assertEqual(self.answer[0][1],
                                       u'con args: command'))
        return self.deferred

