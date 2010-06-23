# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file


from twisted.trial.unittest import TestCase as TwistedTestCase
from twisted.internet import defer

from lalita import dispatcher, events, ircbot

server = dict(
    encoding='utf8',
    host="0.0.0.0",
    port=6667,
    nickname="test",
    channels={"channel":{}},
    plugins={},
)

class FakeTransport(object):
    def write(*a): pass

ircbot_factory = ircbot.IRCBotFactory(server)
ircbot.logger.setLevel("error")
bot = ircbot.IrcBot()
bot.factory = ircbot_factory
bot.msg = lambda *a:None
bot.transport = FakeTransport()

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


class FakeDispatcher(object):
    '''Fake dispatcher for the tests.'''
    def __init__(self):
        self.pushed = None

    def init(self, config):
        pass

    def push(self, *args):
        '''Stores what was pushed.'''
        self.pushed = args


class TestBase(EasyDeferredTests):
    '''Base setup.'''

    def setUp(self):
        super(TestBase, self).setUp()
        bot.dispatcher = FakeDispatcher()

    def check_pushed(self, *to_compare):
        '''Checks against what was pushed in the dispatcher.'''
        self.deferredAssertEqual(bot.dispatcher.pushed, to_compare)
        self.deferred.callback(True)


class TestConnection(TestBase):
    '''Connection, signing, etc.'''

    def test_connection_made(self):
        '''Calling bot.connectionMade'''
        bot.connectionMade()
        self.check_pushed(events.CONNECTION_MADE)
        return self.deferred

    def test_connection_lost(self):
        '''Calling bot.connectionLost'''
        bot.connectionMade()
        bot.connectionLost("reason")
        self.check_pushed(events.CONNECTION_LOST)
        return self.deferred

    def test_signed_on(self):
        '''Calling bot.signedOn'''
        bot.signedOn()
        self.check_pushed(events.SIGNED_ON)
        return self.deferred

    def test_joined(self):
        '''Calling bot.joined'''
        bot.joined("channel")
        self.check_pushed(events.JOINED, "channel")
        return self.deferred


class TestMessages(TestBase):
    '''Messages from users.'''

    def setUp(self):
        super(TestMessages, self).setUp()
        bot.connectionMade()

    def test_privmsg_private(self):
        '''Calling bot.privmsg for self'''
        bot.privmsg("user", MY_NICKNAME, "blah")
        self.check_pushed(events.PRIVATE_MESSAGE, "user", "blah")
        return self.deferred

    def test_privmsg_talkedtome1(self):
        '''Calling bot.privmsg when talking to self using ":"'''
        bot.privmsg("user", "chnl", MY_NICKNAME + ":" + "blah    ")
        self.check_pushed(events.TALKED_TO_ME, "user", "chnl", "blah")
        return self.deferred

    def test_privmsg_talkedtome2(self):
        '''Calling bot.privmsg when talking to self using " "'''
        bot.privmsg("user", "chnl", MY_NICKNAME + " " + "blah")
        self.check_pushed(events.TALKED_TO_ME, "user", "chnl", "blah")
        return self.deferred

    def test_privmsg_talkedtome3(self):
        '''Calling bot.privmsg when talking to self using ","'''
        bot.privmsg("user", "chnl", MY_NICKNAME + "," + "    blah")
        self.check_pushed(events.TALKED_TO_ME, "user", "chnl", "blah")
        return self.deferred

    def test_privmsg_command_noargs(self):
        '''Calling bot.privmsg with a command with no args'''
        bot.privmsg("user", "chnl", "@command")
        self.check_pushed(events.COMMAND, "user", "chnl", "command")
        return self.deferred

    def test_privmsg_command_onearg(self):
        '''Calling bot.privmsg with a command with one arg'''
        bot.privmsg("user", "chnl", "@command foo")
        self.check_pushed(events.COMMAND, "user", "chnl", "command", "foo")
        return self.deferred

    def test_privmsg_command_twoargs(self):
        '''Calling bot.privmsg with a command with two args'''
        bot.privmsg("user", "chnl", "@cmd foo bar")
        self.check_pushed(events.COMMAND, "user", "chnl", "cmd", "foo", "bar")
        return self.deferred

    def test_privmsg_public(self):
        '''Calling bot.privmsg with something public'''
        bot.privmsg("user", "chnl", "blah")
        self.check_pushed(events.PUBLIC_MESSAGE, "user", "chnl", "blah")
        return self.deferred

    def test_privmsg_command_char(self):
        '''Calling bot.privmsg with custom command char'''
        # set up command char config
        _command_char = bot.command_char
        bot.command_char = '!'

        # call command and test
        bot.privmsg("user", "chnl", "!cmd foo")
        self.check_pushed(events.COMMAND, "user", "chnl", "cmd", "foo")

        # cleanup
        bot.command_char = _command_char
        return self.deferred

    def test_action(self):
        '''Calling bot.action'''
        bot.action("user!foo!bar", "chnl", "blah")
        self.check_pushed(events.ACTION, "user", "chnl", "blah")
        return self.deferred


class TestUserActions(TestBase):
    '''Actions done by other users.'''

    def setUp(self):
        super(TestUserActions, self).setUp()
        bot.connectionMade()

    def test_userJoined(self):
        '''Calling bot.userJoined'''
        bot.userJoined("user", "chnl")
        self.check_pushed(events.JOIN, "user", "chnl")
        return self.deferred

    def test_userLeft(self):
        '''Calling bot.userLeft'''
        bot.userLeft("user", "chnl")
        self.check_pushed(events.LEFT, "user", "chnl")
        return self.deferred

    def test_userQuit(self):
        '''Calling bot.userQuit'''
        bot.userQuit("user", "message")
        self.check_pushed(events.QUIT, "user", "message")
        return self.deferred

    def test_userKicked(self):
        '''Calling bot.userKicked'''
        bot.userKicked("user", "chnl", "op", "bad behaviour")
        self.check_pushed(events.KICK, "user", "chnl", "op", "bad behaviour")
        return self.deferred

    def test_userRenamed(self):
        '''Calling bot.userRenamed'''
        bot.userRenamed('oldname', 'newname')
        self.check_pushed(events.RENAME, 'oldname', 'newname')
        return self.deferred
