# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

import re

from collections import defaultdict
from twisted.trial.unittest import TestCase as TwistedTestCase
from twisted.internet import defer, reactor
from twisted.words.protocols.irc import RPL_NAMREPLY, numeric_to_symbolic

from lalita import Plugin, dispatcher, events, ircbot


class Base(TwistedTestCase):
    """Base class that setups a bot."""

    def setUp(self):
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
        self.bot = ircbot.IrcBot()
        self.bot.factory = ircbot_factory
        self.bot.config = ircbot_factory.config
        self.bot.msg = lambda *a:None


class EasyDeferredTests(Base):
    '''Base class for deferred tests.'''

    def setUp(self):
        Base.setUp(self)
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


class TestAddIRCCallback(Base):
    def setUp(self):
        Base.setUp(self)
        self.disp = dispatcher.Dispatcher(self.bot)
        self.disp.init({})

    def test_method_exists(self):
        self.assertTrue(hasattr(self.disp, 'add_irc_callback'))

    def test_add_nonexisting_callback(self):
        def names(self, *args):
            pass

        self.assertRaises(AttributeError, getattr, self.bot, 'irc_RPL_NAMREPLY')
        self.disp.add_irc_callback(numeric_to_symbolic.get(RPL_NAMREPLY), names)
        self.assertEqual(self.bot.irc_RPL_NAMREPLY, names)

        # make sure to clean up
        del self.bot.irc_RPL_NAMREPLY

    def test_numeric_callback(self):
        def names(self, *args):
            pass

        self.assertRaises(AttributeError, getattr, self.bot,
            'irc_RPL_NAMREPLY')
        self.disp.add_irc_callback(RPL_NAMREPLY, names)
        self.assertEqual(self.bot.irc_RPL_NAMREPLY, names)

        # make sure to clean up
        del self.bot.irc_RPL_NAMREPLY

    def test_add_existing_callback(self):
        def join(self, *args):
            pass

        _irc_JOIN = self.bot.irc_JOIN

        self.assertTrue(hasattr(self.bot, 'irc_JOIN'))
        self.assertNotEqual(self.bot.irc_JOIN, join)
        self.disp.add_irc_callback('JOIN', join)
        self.assertEqual(self.bot.irc_JOIN, join)

        # make sure to clean up
        self.bot.irc_JOIN = _irc_JOIN


class TestRegister(Base):
    def setUp(self):
        Base.setUp(self)
        self.disp = dispatcher.Dispatcher(self.bot)
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
    '''Test that push works.'''

    def setUp(self):
        super(TestPush, self).setUp()
        self.disp = dispatcher.Dispatcher(self.bot)
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

    def test_events_supported(self):
        def test(*args):
            self.deferred.callback(True)
        self.helper.test = test

        supported_events = [getattr(events, name) for name in dir(events) \
                            if name == name.upper()]
        for event in supported_events:
            self.disp.register(event, self.helper.f)
            if (event in dispatcher.USER_POS and 
                dispatcher.USER_POS[event] is not None):
                self.disp.push(event, 'user', 'channel', 'msg')
            elif (event in dispatcher.CHANNEL_POS and
                  dispatcher.CHANNEL_POS[event] is not None):
                if event == events.JOINED:
                    self.disp.push(event, 'channel', 'user', 'msg')
                else:
                    self.disp.push(event, 'user', 'channel', 'msg')
            else:
                self.disp.push(event)
        return self.deferred


class TestEvents(EasyDeferredTests):
    '''Test all the events.'''

    def setUp(self):
        super(TestEvents, self).setUp()
        self.disp = dispatcher.Dispatcher(self.bot)
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

    def test_no_such_command(self):
        d = defer.Deferred()
        def test(*args):
            self.assertEquals(3, len(args))
            self.assertEquals('user', args[2])
            self.assertEquals(u'%s: No existe esa orden!', args[1])
            d.callback(True)
        self.disp.register(events.COMMAND, self.helper.f, 'foo')
        self.disp.msg = test
        self.disp.push(events.COMMAND, 'user', 'channel', '@notthecommand')
        return d

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


class TestSay(EasyDeferredTests):
    '''Plugins say stuff, the dispatcher transmit that.'''

    def setUp(self):
        super(TestSay, self).setUp()
        self._disp = disp = dispatcher.Dispatcher(self.bot)

        # let's register what the dispatcher says that plugin said
        self.recorder = []
        disp._msg = lambda *a: self.recorder.append(a)
        disp.init({})

        class Helper(object):
            '''Plugin that says what we tell to say.'''
            def f(self, *args):
                for what in self.what:
                    self.say(*what)

        self.helper = Helper()
        disp.new_plugin(self.helper, "#channel")
        disp.register(events.PUBLIC_MESSAGE, self.helper.f)
        self.deferred.addCallback(lambda _: disp.push(events.PUBLIC_MESSAGE,
                                                      "usr", "#channel", "bu"))

    def tearDown(self):
        self._disp.shutdown()

    def test_nothing(self):
        '''Plugin don't say anything.'''
        self.helper.what = []

        def check(_):
            self.assertEqual(self.recorder, [])

        self.deferred.addCallback(check)
        self.deferred.callback(True)
        return self.deferred

    def test_one_thing(self):
        '''Plugin say one thing.'''
        self.helper.what = [("touser", "text")]

        def check(_):
            self.assertEqual(self.recorder, [("touser", "text")])

        self.deferred.addCallback(check)
        self.deferred.callback(True)
        return self.deferred

    def test_two_things(self):
        '''Plugin say two things.'''
        self.helper.what = [("user", "t1"), ("user", "t2")]

        def check(_):
            self.assertEqual(self.recorder, [("user", "t1"), ("user", "t2")])

        self.deferred.addCallback(check)
        self.deferred.callback(True)
        return self.deferred

    def test_problem_alert_message(self):
        """A problem with the message is reported to the ircmaster."""
        disp = dispatcher.Dispatcher(self.bot)
        recorder = []
        disp._msg = lambda *a: recorder.append(a)
        disp.init({'ircmaster':'ircmaster'})

        class Helper(object):
            """Plugin that says what we tell to say."""
            def f(self, *args):
                """Say something bad."""
                self.say("usr", "foo %d", "no int")

        helper = Helper()
        disp.new_plugin(helper, "#channel")
        disp.register(events.PUBLIC_MESSAGE, helper.f)

        d = defer.Deferred()
        d.addCallback(lambda _: disp.push(events.PUBLIC_MESSAGE,
                                          "usr", "#channel", "bu"))

        def check(_):
            """Check what's reported."""
            m = "Unable to format message! Msg: 'foo %d'  Args: ('no int',)"
            self.assertEqual(recorder[0], ("ircmaster", m))

        d.addCallback(check)
        d.callback(True)
        return d

    def test_problem_alert_executing(self):
        """A problem with the execution is reported to the ircmaster."""
        disp = dispatcher.Dispatcher(self.bot)
        recorder = []
        disp._msg = lambda *a: recorder.append(a)
        disp.init({'ircmaster':'ircmaster'})

        class Helper(object):
            """Plugin that says what we tell to say."""
            def f(self, *args):
                """Have a problem."""
                raise ValueError("problem!")

        helper = Helper()
        disp.new_plugin(helper, "#channel")
        disp.register(events.PUBLIC_MESSAGE, helper.f)

        d = defer.Deferred()
        d.addCallback(lambda _: disp.push(events.PUBLIC_MESSAGE,
                                          "usr", "#channel", "bu"))

        def check(_):
            """Check what's reported."""
            m = "Error calling the plugin 'lalita.core.tests."\
                "test_dispatcher.Helper': ValueError('problem!',)"
            self.assertEqual(recorder[0], ("ircmaster", m))

        d.addCallback(check)
        d.callback(True)
        return d

    def test_args_replac_one(self):
        '''Say something to be replaced with one item.'''
        self.helper.what = [("touser", "text %d", 5)]

        def check(_):
            self.assertEqual(self.recorder, [("touser", "text 5")])

        self.deferred.addCallback(check)
        self.deferred.callback(True)
        return self.deferred

    def test_args_replac_two(self):
        '''Say something to be replaced with two items.'''
        self.helper.what = [("touser", "text %d %s", 5, "foo")]

        def check(_):
            self.assertEqual(self.recorder, [("touser", "text 5 foo")])

        self.deferred.addCallback(check)
        self.deferred.callback(True)
        return self.deferred

    def test_args_replac_dict(self):
        '''Say something to be replaced with info from dict.'''
        d = dict(a=4, b='foo')
        self.helper.what = [("touser", "text %(a)d %(b)s", d)]

        def check(_):
            self.assertEqual(self.recorder, [("touser", "text 4 foo")])

        self.deferred.addCallback(check)
        self.deferred.callback(True)
        return self.deferred

    def test_args_replac_nothing(self):
        '''Nothing to be replaced but using %.'''
        self.helper.what = [("touser", "Rate is 4%")]

        def check(_):
            self.assertEqual(self.recorder, [("touser", "Rate is 4%")])

        self.deferred.addCallback(check)
        self.deferred.callback(True)
        return self.deferred



class TestFlowController(EasyDeferredTests):
    '''Plugins say stuff, the dispatcher transmit that.'''

    def setUp(self):
        super(TestFlowController, self).setUp()
        dispatcher.FLOW_TIMEOUT = 1
        self.disp = disp = dispatcher.Dispatcher(self.bot)

        # let's register what the dispatcher says that plugin said
        self.recorder = []
        disp._msg = lambda *a: self.recorder.append(a)
        disp.init({})

        class Helper(object):
            '''Plugin that says what we tell to say.'''
            def f(self, usr, chnl, txt):
                for to, msg in self.what:
                    if usr == to:
                        self.say(to, msg)

            def g(self, *a):
                '''nothing!'''

        self.helper = Helper()
        disp.new_plugin(self.helper, "#channel")
        disp.register(events.PUBLIC_MESSAGE, self.helper.f)
        disp.register(events.COMMAND, self.helper.g, ("void",))

    def tearDown(self):
        self.disp.shutdown()

    def user_says(self, _, user, channel, text):
        self.disp.push(events.PUBLIC_MESSAGE, user, channel, text)

    def test_nothing(self):
        '''Plugin don't say anything.'''
        self.helper.what = []

        def check(_):
            self.assertEqual(self.recorder, [])

        self.deferred.addCallback(self.user_says, "usr", "#channel", "bu")
        self.deferred.addCallback(check)
        self.deferred.callback(True)
        return self.deferred

    def test_short(self):
        '''One answer, receive it.'''
        self.helper.what = [("usr", "froobar")]

        def check(_):
            self.assertEqual(self.recorder, [("usr", "froobar")])

        self.deferred.addCallback(self.user_says, "usr", "#channel", "bu")
        self.deferred.addCallback(check)
        self.deferred.callback(True)
        return self.deferred

    def test_long(self):
        '''Several answers, receive only the first ones.'''
        self.helper.what = []
        for i in range(7):
            self.helper.what.append(("usr", "r %d" % i))

        def check(_):
            self.assertEqual(self.recorder, [("usr", "r 0"), ("usr", "r 1"),
                                             ("usr", "r 2"), ("usr", "r 3"),
                                             ("usr", "r 4"),
                                            ])

        self.deferred.addCallback(self.user_says, "usr", "#channel", "bu")
        self.deferred.addCallback(check)
        self.deferred.callback(True)
        return self.deferred

    def test_more(self):
        '''Get what's queued.'''
        self.helper.what = []
        for i in range(7):
            self.helper.what.append(("usr", "r %d" % i))

        def check1(_):
            self.assertEqual(self.recorder, [("usr", "r 0"), ("usr", "r 1"),
                                             ("usr", "r 2"), ("usr", "r 3"),
                                             ("usr", "r 4"),
                                            ])
            self.recorder[:] = []

        def check2(_):
            self.assertEqual(self.recorder, [("usr", "r 5"), ("usr", "r 6")])

        self.deferred.addCallback(self.user_says, "usr", "#channel", "bu")
        self.deferred.addCallback(check1)
        self.deferred.addCallback(lambda _: self.disp.push(events.COMMAND,
                                                           "usr", "#channel",
                                                           "more", ()))
        self.deferred.addCallback(check2)
        self.deferred.callback(True)
        return self.deferred

    def test_more_different_users(self):
        '''More discriminates per talking user.'''
        self.helper.what = []
        for i in range(7):
            self.helper.what.append(("usr1", "r %d" % i))
            self.helper.what.append(("usr2", "r %d" % i))

        def reset_recorder(_):
            self.recorder[:] = []

        def check2(_):
            self.assertEqual(self.recorder, [("usr2", "r 5"), ("usr2", "r 6")])

        self.deferred.addCallback(self.user_says, "usr1", "#channel", "bu")
        self.deferred.addCallback(self.user_says, "usr2", "#channel", "bu")
        self.deferred.addCallback(reset_recorder)
        self.deferred.addCallback(lambda _: self.disp.push(events.COMMAND,
                                                           "usr2", "#channel",
                                                           "more", ()))
        self.deferred.addCallback(check2)
        self.deferred.callback(True)
        return self.deferred

    def test_more_different_channel(self):
        '''More discriminates per channel.'''
        self.disp.new_plugin(self.helper, "#channel1")
        self.disp.new_plugin(self.helper, "#channel2")
        self.helper.what = []
        for i in range(7):
            self.helper.what.append(("usr", "r %d" % i))

        def reset_recorder(_):
            self.recorder[:] = []

        def check2(_):
            self.assertEqual(self.recorder, [("usr", "r 5"), ("usr", "r 6")])

        self.deferred.addCallback(self.user_says, "usr", "#channel1", "bu")
        self.deferred.addCallback(self.user_says, "usr", "#channel2", "bu")
        self.deferred.addCallback(reset_recorder)
        self.deferred.addCallback(lambda _: self.disp.push(events.COMMAND,
                                                           "usr", "#channel1",
                                                           "more", ()))
        self.deferred.addCallback(check2)
        self.deferred.callback(True)
        return self.deferred

    def test_reset(self):
        '''Other than more, the queue is reseted.'''
        self.helper.what = []
        for i in range(7):
            self.helper.what.append(("usr", "r %d" % i))

        def check1(_):
            self.assertEqual(self.recorder, [("usr", "r 0"), ("usr", "r 1"),
                                             ("usr", "r 2"), ("usr", "r 3"),
                                             ("usr", "r 4"),
                                            ])
            self.recorder[:] = []

        def check2(_):
            self.assertEqual(self.recorder,
                             [("#channel", u"No hay nada encolado para vos")])

        self.deferred.addCallback(self.user_says, "usr", "#channel", "bu")
        self.deferred.addCallback(check1)
        self.deferred.addCallback(lambda _: self.disp.push(events.COMMAND,
                                                           "usr", "#channel",
                                                           "void", ()))
        self.deferred.addCallback(lambda _: self.disp.push(events.COMMAND,
                                                           "usr", "#channel",
                                                           "more", ()))
        self.deferred.addCallback(check2)
        self.deferred.callback(True)
        return self.deferred

    def test_timeout(self):
        '''The queue dissappears after some time.'''
        self.helper.what = []
        for i in range(7):
            self.helper.what.append(("usr", "r %d" % i))

        def check1(_):
            self.assertEqual(self.recorder, [("usr", "r 0"), ("usr", "r 1"),
                                             ("usr", "r 2"), ("usr", "r 3"),
                                             ("usr", "r 4"),
                                            ])
            self.recorder[:] = []

        def check2(_):
            self.assertEqual(self.recorder,
                             [("#channel", u"No hay nada encolado para vos")])

        self.deferred.addCallback(self.user_says, "usr", "#channel", "bu")
        self.deferred.addCallback(check1)

        # second part of the test, time later
        d2 = defer.Deferred()
        d2.addCallback(lambda _: self.disp.push(events.COMMAND, "usr",
                                               "#channel", "more", ()))
        d2.addCallback(check2)
        self.deferred.addCallback(lambda _: d2)

        reactor.callLater(1.5, d2.callback, None)
        self.deferred.callback(True)
        return self.deferred
    test_timeout.timeout = 3


class TestPluginI18n(EasyDeferredTests):

    def setUp(self):
        super(TestPluginI18n, self).setUp()
        self.disp = dispatcher.Dispatcher(self.bot)
        self.disp.init({})

        class Helper(Plugin):
            def init(self, *args):
                d = {'a message' : {'es' : 'un mensaje'},
                     'with args: %s' : {'es' : 'con args: %s'}
                    }
                self.register_translation(self, d)
            def simple(self, user, channel, *args):
                self.say(channel, 'a message')
                self.test(True)
            def withargs(self, user, channel, command, *args):
                self.say(channel, 'with args: %s', command)
                self.test(True)

        self.helper = Helper({'nickname':'helper', 'encoding':'fake'}, 'DEBUG')
        self.disp.config['channels'] = {'channel-es':{'language':'es'}}
        self.old_msg = self.bot.msg
        self.answer = []
        def g(towhere, msg, _):
            self.answer.append((towhere, msg.decode("utf8")))
        self.bot.msg = g

    def tearDown(self):
        self.disp.shutdown()
        super(TestPluginI18n, self).tearDown()
        self.bot.msg = self.old_msg

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

    def test_message_with_args_es(self):
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

    def test_message_with_empty_args(self):
        """Test that string formating errors raise a better error message."""
        self.disp.new_plugin(self.helper, "channel")
        self.helper.init({})
        def withemptyargs(user, channel, command, *args):
            """Break self.helper.say not having enough args."""
            try:
                self.helper.say(channel, 'with empty args: %s %d', 5)
            except Exception, e:
                self.helper.test(e)
            else:
                self.helper.test(True)
        # lie to the dispatcher about this function
        withemptyargs.im_self = self.helper
        withemptyargs.im_func = withemptyargs
        self.helper.withemptyargs = withemptyargs
        def test(result):
            """Check that we get a TypeError."""
            if isinstance(result, TypeError):
                self.deferred.callback(True)
            else:
                self.deferred.errback(result)
        self.helper.test = test
        self.disp.register(events.COMMAND, self.helper.withemptyargs)
        self.disp.push(events.COMMAND, 'user', 'channel', 'command')
        return self.deferred


class TestTooMuchTalk(Base):
    """Test situations where instances are in a lot of places."""

    class Helper(object):
        """Plugin that says what we tell to say."""
        def f(self, *_):
            """Answers."""
            self.say(*self.what)

    def setUp(self):
        super(TestTooMuchTalk, self).setUp()
        self.disp = disp = dispatcher.Dispatcher(self.bot)

        # let's register what the dispatcher says that plugin said
        self.recorder = []
        disp._msg = lambda *a: self.recorder.append(a)
        disp.init({})

    def tearDown(self):
        self.disp.shutdown()

    @defer.inlineCallbacks
    def test_repeated_public(self):
        """Repeated in the public."""
        helper = self.Helper()
        self.disp.new_plugin(helper, "#channel")
        self.disp.register(events.PUBLIC_MESSAGE, helper.f)
        helper.what = ("#channel", "resp")

        helper = self.Helper()
        self.disp.new_plugin(helper, None)
        self.disp.register(events.PUBLIC_MESSAGE, helper.f)
        helper.what = ("#channel", "resp")

        def check():
            """Check all is ok."""
            self.assertEqual(self.recorder, [("#channel", "resp")])

        yield self.disp.push(events.PUBLIC_MESSAGE, "usr", "#channel", "bu")
        yield check()

    @defer.inlineCallbacks
    def test_repeated_private(self):
        """Repeated in the private."""
        helper = self.Helper()
        self.disp.new_plugin(helper, "#channel")
        self.disp.register(events.PRIVATE_MESSAGE, helper.f)
        helper.what = ("usr", "resp")

        helper = self.Helper()
        self.disp.new_plugin(helper, None)
        self.disp.register(events.PRIVATE_MESSAGE, helper.f)
        helper.what = ("usr", "resp")

        def check():
            """Check all is ok."""
            self.assertEqual(self.recorder, [("usr", "resp")])

        yield self.disp.push(events.PRIVATE_MESSAGE, "usr", "bu")
        yield check()
