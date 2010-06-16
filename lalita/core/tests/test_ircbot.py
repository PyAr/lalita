# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

import copy
import logging
import unittest
from cStringIO import StringIO

from lalita import ircbot
from lalita.core.dispatcher import ProxyBot
from lalita.core.events import *

from twisted.words.protocols import irc

server = dict(
    encoding = 'utf8',
    host = "0.0.0.0",
    port = 6667,
    nickname = "test",
    channels = {
        '#testchn1': {
            'plugins': {
                'test.Test1': {'config1':'config2'},
            },
        },
        '#testchn2': {
            'plugins': {
                'test.Test1': {'config1':'config2'},
                'test.Test2': {'config3':'config4'},
            },
        },
        '#testchn3': {
            'plugins': {},
        },
    },
    plugins = {
        'test.Test2': {'config3':'config4'},
        'test.Test3': {'config5':'config6'},
    },
)


class TestLoadPlugin(unittest.TestCase):
    """Load the plugin with correct stuff."""

    def setUp(self):
        server["log_config"] = {}
        ircbot_factory = ircbot.IRCBotFactory(server)
        ircbot.logger.setLevel("error")
        self.bot = bot = ircbot.IrcBot()
        bot.factory = ircbot_factory
        bot.config = ircbot_factory.config
        bot.encoding_server = server['encoding']
        bot.encoding_channels = {}


        self.results = []

        class FakeModule(object):
            class TestClass (object):
                def __init__(innerself, params, loglvl):
                    self.results.append(("__init__", params, loglvl))
                def init(innerself, config):
                    self.results.append(("init", config))

        self.original_import = __import__
        def fake_import(modname, *args, **kwargs):
            if modname == "testme":
                return FakeModule
            return self.original_import(modname, *args, **kwargs)
        __builtins__["__import__"] = fake_import

    def tearDown(self):
        __builtins__["__import__"] = self.original_import

    def test_load_plugin(self):
        self.bot.load_plugin("testme.TestClass", "config", "params", "channel")
        self.assertEqual(self.results,
                         [("__init__", "params", None),
                          ("init", "config"),
                         ])

    def test_plugin_bot_is_proxy(self):
        self.bot.load_plugin('lalita.plugins.example.Example', 'config',
            {'nickname': 'nickname', 'encoding': 'utf-8'}, 'channel')
        plugins = self.bot.dispatcher._plugins.keys()
        self.assertEqual(len(plugins), 1)
        plugin = plugins[0]
        self.assertTrue(isinstance(plugin.bot, ProxyBot))
        self.assertEqual(plugin.bot.plugin, plugin)

    def test_plugin_bot_method(self):
        def mock_join(channel, key=None):
            self.results.append(('join', channel, key))
            self.join_called = True
        old_join = self.bot.join
        self.bot.join = mock_join

        self.bot.load_plugin('lalita.plugins.example.Example', 'config',
            {'nickname': 'nickname', 'encoding': 'utf-8'}, 'channel')
        plugins = self.bot.dispatcher._plugins.keys()
        self.assertEqual(len(plugins), 1)
        plugin = plugins[0]

        # enable logging
        logger = logging.getLogger('ircbot.ProxyBot')
        logger.setLevel(logging.INFO)
        output = StringIO()
        handler = logging.StreamHandler(output)
        logger.addHandler(handler)

        self.join_called = False
        # test method
        plugin.bot.join('channel1')
        self.assertTrue(self.join_called)
        expected = [('join', 'channel1', None)]
        self.assertEqual(self.results, expected)
        # test logged output
        output.seek(0)
        msg = "Plugin %s calling method join on ircbot with args %s %s.\n"
        self.assertEqual(msg % (plugin, ('channel1',), {}), output.read())

        self.bot.join = old_join


class TestConfiguration(unittest.TestCase):
    """Send the config to load the plugin."""

    def setUp(self):
        ircbot_factory = ircbot.IRCBotFactory(server)
        ircbot.logger.setLevel("error")
        self.bot = bot = ircbot.IrcBot()
        bot.factory = ircbot_factory
        bot.config = ircbot_factory.config
        bot.encoding_server = server['encoding']
        bot.encoding_channels = {}

        self.results = []
        def load_plugin(plugin, config, params, channel=None):
            self.results.append((plugin, config, channel))
        bot.load_plugin = load_plugin

    def test_server_plugin(self):
        self.bot.load_server_plugins()
        self.assertEqual(self.results,
                         [('test.Test2', {'config3': 'config4'}, None),
                          ('test.Test3', {'config5': 'config6'}, None)])

    def test_channel_plugin_1(self):
        self.bot.load_channel_plugins("#testchn1")
        self.assertEqual(self.results,
                         [('test.Test1', {'config1': 'config2'}, "#testchn1")])

    def test_channel_plugin_2(self):
        self.bot.load_channel_plugins("#testchn2")
        self.assertEqual(self.results,
                         [('test.Test1', {'config1': 'config2'}, "#testchn2"),
                          ('test.Test2', {'config3': 'config4'}, "#testchn2")])

    def test_channel_plugin_3(self):
        self.bot.load_channel_plugins("#testchn3")
        self.assertEqual(self.results, [])


class PrivateMessageTests(unittest.TestCase):
    """All private message processing."""

    def setUp(self):
        ircbot_factory = ircbot.IRCBotFactory(server.copy())
        ircbot.logger.setLevel("error")
        self.bot = bot = ircbot.IrcBot()
        bot.factory = ircbot_factory
        bot.config = ircbot_factory.config
        bot.encoding_server = server['encoding']
        bot.encoding_channels = {}
        bot.command_char = '@'

        # don't load plugins
        bot.load_plugin = lambda *a: None

        # record what is pushed
        self.pushed = []
        bot.dispatcher.push = lambda *a: self.pushed.append(a)

    def test_command_char(self):
        """Test that the attribute is set during connection."""
        # setup
        _config = copy.copy(self.bot.config)
        self.bot.config.update({'command_char': '!'})

        _connectionMade = irc.IRCClient.connectionMade
        irc.IRCClient.connectionMade = lambda s: None

        # reconfigure bot
        self.bot.connectionMade()
        # test value
        self.assertEqual(self.bot.command_char, '!')

        # cleanup
        self.bot.config = _config
        irc.IRCClient.connectionMade = _connectionMade

    def test_privmsg_private_message(self):
        """Test private message."""
        self.bot.privmsg('john!~jdoe@127.0.0.1', self.bot.nickname, u'blah')
        self.assertEqual(self.pushed, [(PRIVATE_MESSAGE, 'john', u'blah')])

    def test_talked_to_me_space(self):
        """Test talked to bot, separating with space."""
        self.bot.privmsg('john!~jdoe@127.0.0.1', "#channel",
                         u'%s foo bar' % self.bot.nickname)
        self.assertEqual(self.pushed,
                         [(TALKED_TO_ME, 'john', '#channel', u'foo bar')])

    def test_talked_to_me_comma(self):
        """Test talked to bot, separating with comma."""
        self.bot.privmsg('john!~jdoe@127.0.0.1', "#channel",
                         u'%s, foo bar' % self.bot.nickname)
        self.assertEqual(self.pushed,
                         [(TALKED_TO_ME, 'john', '#channel', u'foo bar')])

    def test_talked_to_me_twopoints(self):
        """Test talked to bot, separating with two points."""
        self.bot.privmsg('john!~jdoe@127.0.0.1', "#channel",
                         u'%s: foo bar' % self.bot.nickname)
        self.assertEqual(self.pushed,
                         [(TALKED_TO_ME, 'john', '#channel', u'foo bar')])

    def test_command_at(self):
        """Test command, using at."""
        self.bot.privmsg('john!~jdoe@127.0.0.1', "#channel", u'@foo bar')
        self.assertEqual(self.pushed,
                         [(COMMAND, 'john', '#channel', u'foo', 'bar')])

    def test_command_more_params(self):
        """Test command, using at."""
        self.bot.privmsg('john!~jdoe@127.0.0.1', "#channel", u'@foo bar baz 6')
        self.assertEqual(self.pushed, [(COMMAND, 'john', '#channel', u'foo',
                                        'bar', 'baz', '6')])

    def test_command_other_char(self):
        """Test command, using other char."""
        self.bot.command_char = '%'
        self.bot.privmsg('john!~jdoe@127.0.0.1', "#channel", u'%foo bar')
        self.assertEqual(self.pushed,
                         [(COMMAND, 'john', '#channel', u'foo', 'bar')])

    def test_command_indirect_server(self):
        """Test command that was talking to the bot, server config."""
        self.bot.config['indirect_command'] = True
        self.bot.privmsg('john!~jdoe@127.0.0.1', "#channel",
                         u'%s, foo bar baz' % self.bot.nickname)
        self.assertEqual(self.pushed,
                         [(COMMAND, 'john', '#channel', 'foo', 'bar', 'baz')])

    def test_command_indirect_channels(self):
        """Test command that was talking to the bot, channels config."""
        self.bot.config['channels']['#chan1'] = dict(indirect_command=True)
        name = self.bot.nickname
        self.bot.privmsg('j!~jdoe@127.0.0.1', "#chan1", u'%s, foo 1' % name)
        self.bot.privmsg('j!~jdoe@127.0.0.1', "#chan2", u'%s, foo 2' % name)
        self.assertEqual(self.pushed, [(COMMAND, 'j', '#chan1', 'foo', '1'),
                                       (TALKED_TO_ME, 'j', '#chan2', 'foo 2')])

    def test_public_message_standard(self):
        """Test public message."""
        self.bot.privmsg('john!~jdoe@127.0.0.1', "#channel", u'foo bar')
        self.assertEqual(self.pushed,
                         [(PUBLIC_MESSAGE, 'john', '#channel', u'foo bar')])

    def test_public_message_botname(self):
        """Test weird public message that starts with the bot name."""
        msg = u'%sfoobar baz' % self.bot.nickname  # no separation after name
        self.bot.privmsg('john!~jdoe@127.0.0.1', "#chan", msg)
        self.assertEqual(self.pushed, [(PUBLIC_MESSAGE, 'john', '#chan', msg)])
