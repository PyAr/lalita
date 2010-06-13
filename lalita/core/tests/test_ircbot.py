# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

import copy
import unittest

from lalita import ircbot
from lalita.core.dispatcher import ProxyBot

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
        class MockLogger(object):
            def info(_, msg):
                self.results.append((msg,))

        self.bot.load_plugin('lalita.plugins.example.Example', 'config',
            {'nickname': 'nickname', 'encoding': 'utf-8'}, 'channel')
        plugins = self.bot.dispatcher._plugins.keys()
        self.assertEqual(len(plugins), 1)
        plugin = plugins[0]
        plugin.logger = MockLogger()

        self.join_called = False
        plugin.bot.join('channel1')
        self.assertTrue(self.join_called)
        expected = [("Plugin %s calling method join on ircbot." % plugin,),
                    ('join', 'channel1', None)]
        self.assertEqual(self.results, expected)

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

    def test_command_char(self):
        from twisted.words.protocols import irc
        # setup
        _config = copy.copy(self.bot.config)
        self.bot.config.update({'command_char': '!'})

        def mock_connectionMade(self):
            pass
        _connectionMade = irc.IRCClient.connectionMade
        irc.IRCClient.connectionMade = mock_connectionMade

        # reconfigure bot
        self.bot.connectionMade()
        # test value
        self.assertEqual(self.bot.command_char, '!')

        # cleanup
        self.bot.config = _config
        irc.IRCClient.connectionMade = _connectionMade

