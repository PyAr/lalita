
from twisted.trial.unittest import TestCase as TwistedTestCase
from twisted.internet import defer

from core import events
from core import dispatcher
from config import servers
import ircbot

ircbot_factory = ircbot.IRCBotFactory(servers["perrito"])
MY_NICKNAME = servers["perrito"]['nickname']
import pdb;pdb.set_trace()

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
        super(TestRegister, self).setUp()
        self.disp = dispatcher.Dispatcher()

    def test_method_exists(self):
        self.assertTrue(hasattr(self.disp, "register"))

    def test_empty(self):
        '''Test no registration.'''
        self.assertEqual(self.disp._callbacks, {})
        return self.deferred

    def test_one_event(self):
        '''Test registration to events.'''
        def f(): pass

        self.disp.register(events.CONNECTION_MADE, f)
        self.assertEqual(self.disp._callbacks, {events.CONNECTION_MADE: [f]})
        return self.deferred

    def test_one_event_twice(self):
        '''Test two registrations to the same events.'''
        def f(): pass
        def g(): pass

        self.disp.register(events.CONNECTION_MADE, f)
        self.disp.register(events.CONNECTION_MADE, g)
        self.assertEqual(self.disp._callbacks,
                                            {events.CONNECTION_MADE: [f, g]})
        return self.deferred

    def test_mixed(self):
        '''Test several registration, several events.'''
        def f(): pass
        def g(): pass
        def h(): pass

        self.disp.register(events.CONNECTION_MADE, f)
        self.disp.register(events.CONNECTION_LOST, g)
        self.disp.register(events.CONNECTION_MADE, h)
        self.assertEqual(self.disp._callbacks, {events.CONNECTION_MADE: [f, h],
                                                events.CONNECTION_LOST: [g]})
        return self.deferred


class TestPush(EasyDeferredTests):

    def setUp(self):
        super(TestRegister, self).setUp()
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
            d = defer.deferred()
            self.deferred.callback(True)
            return d

        self.disp.register(events.CONNECTION_MADE, f)
        self.disp.push(events.CONNECTION_MADE)
        return self.deferred


class TestEvents(EasyDeferredTests):

#   * register ('event_<>', callback)
#              ('event_command', callback, [c])
#              ('privmsg', callback, [regex])
#
    def setUp(self):
        super(TestRegister, self).setUp()
        self.disp = dispatcher.Dispatcher()

    def test_connection_made(self):
        '''Test CONNECTION_MADE.'''
        def f():
            self.deferred.callback(True)
            return ""

        self.disp.register(events.CONNECTION_MADE, f)
        self.disp.connectionMade()
        return self.deferred

    def test_connection_lost(self):
        '''Test CONNECTION_LOST.'''
        def f(arg):
            self.deferredAssertEqual(self.deferred, arg, "reason")
            self.deferred.callback(True)
            return ""

        self.disp.register(events.CONNECTION_LOST, f)
        self.disp.connectionLost("reason")
        return self.deferred

    def test_signed_on(self):
        '''Test SIGNED_ON.'''
        def f(arg):
            self.deferred.callback(True)
            return ""

        self.disp.register(events.SIGNED_ON, f)
        self.disp.signedOn()
        return self.deferred

    def test_joined(self):
        '''Test JOINED.'''
        def f(arg):
            self.deferredAssertEqual(self.deferred, arg, "channel")
            self.deferred.callback(True)
            return ""

        self.disp.register(events.JOINED, f)
        self.disp.joined("channel")
        return self.deferred

    def test_private_message_raw(self):
        '''Test PRIVATE_MESSAGE simple.'''
        def f(a, b):
            self.deferredAssertEqual(self.deferred, a, "user")
            self.deferredAssertEqual(self.deferred, b, "msg")
            self.deferred.callback(True)
            return ""

        self.disp.register(events.PRIVATE_MESSAGE, f)
        self.disp.privmsg("user", MY_NICKNAME, "msg")
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
        self.disp.privmsg("user", MY_NICKNAME, "esta no pasa")
        self.disp.privmsg("user", MY_NICKNAME, "hola mundo")
        return self.deferred

    def test_talked_to_me_raw(self):
        '''Test TALKED_TO_ME simple.'''
        def f(a, b):
            self.deferredAssertEqual(self.deferred, a, "user")
            self.deferredAssertEqual(self.deferred, b, "msg")
            self.deferred.callback(True)
            return ""

        self.disp.register(events.TALKED_TO_ME, f)
        self.disp.privmsg("user", "channel", MY_NICKNAME + " msg")
        return self.deferred

    def test_talked_to_me_raw_nicenicks(self):
        '''Test TALKED_TO_ME recognizing well the nickname.'''
        cant = []
        class Helper(object):
            def __init__(innerself):
                innerself.counter = 0
            def met(self, a, b):
                self.deferredAssertEqual(self.deferred, a, "user")
                self.deferredAssertEqual(self.deferred, b, "msg")
                innerself.counter += 1
                if innerself.counter == 3:
                    self.deferred.callback(True)
                return ""
        helper = helper()

        self.disp.register(events.TALKED_TO_ME, helper.met)
        self.disp.privmsg("user", "channel", MY_NICKNAME + "msg")  # nop
        self.disp.privmsg("user", "channel", MY_NICKNAME + ":msg") # yes
        self.disp.privmsg("user", "channel", MY_NICKNAME + ",msg") # yes
        self.disp.privmsg("user", "channel", MY_NICKNAME + " msg") # yes
        return self.deferred

    def test_talked_to_me_regexp(self):
        '''Test TALKED_TO_ME with regexp.'''
        def f(a, b):
            self.deferredAssertEqual(self.deferred, a, "user")
            self.deferredAssertEqual(self.deferred, b, "hola mundo")
            self.deferred.callback(True)
            return ""

        regexp = re.compile("^hola.*$")
        self.disp.register(events.PRIVATE_MESSAGE, f, regexp)
        self.disp.privmsg("user", "channel", MY_NICKNAME + " esta no pasa")
        self.disp.privmsg("user", "channel", MY_NICKNAME + " hola mundo")
        return self.deferred

    def test_public_raw(self):
        '''Test PUBLIC_MESSAGES simple.'''
        def f(a, b):
            self.deferredAssertEqual(self.deferred, a, "user")
            self.deferredAssertEqual(self.deferred, b, "msg")
            self.deferred.callback(True)
            return ""

        self.disp.register(events.PUBLIC_MESSAGES, f)
        self.disp.privmsg("user", "channel", "msg")
        return self.deferred

    def test_public_regexp(self):
        '''Test PUBLIC_MESSAGES with regexp.'''
        def f(a, b):
            self.deferredAssertEqual(self.deferred, a, "user")
            self.deferredAssertEqual(self.deferred, b, "hola mundo")
            self.deferred.callback(True)
            return ""

        regexp = re.compile("^hola.*$")
        self.disp.register(events.PRIVATE_MESSAGE, f, regexp)
        self.disp.privmsg("user", "channel", "esta no pasa")
        self.disp.privmsg("user", "channel", "hola mundo")
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
        self.disp.privmsg("user", "channel", "@command")
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
        self.disp.privmsg("user", "channel", "@command foo")
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
        self.disp.privmsg("user", "channel", "@command foo bar")
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
        self.disp.privmsg("user", "channel", "msg")
        return self.deferred

