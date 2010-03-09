# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

import unittest

from lalita import ircbot


class PluginTest(unittest.TestCase):

    test_server = dict(
        encoding = 'utf8',
        host='0.0.0.0', port=6667,
        nickname='test',
        channels={},
        plugins_dir="plugins",
    )

    def init(self, client_plugin=None, server_plugin=None):
        if client_plugin is not None:
            (plugin_name, config, channel) = client_plugin
            self.test_server["channels"] = { channel : { 'plugins' :
                                                    { plugin_name: config }}}

        if server_plugin is not None:
            (plugin_name, config) = server_plugin
            self.test_server["plugins"] = { plugin_name: config }

        self.test_server["log_config"] = { plugin_name: "error" }
        ircbot.logger.setLevel("error")
        ircbot_factory = ircbot.IRCBotFactory(self.test_server)
        self.bot = ircbot.IrcBot()
        self.bot.factory = ircbot_factory
        self.bot.config = self.test_server
        self.bot.nickname = "TestBot"
        self.bot.encoding_server = "utf-8"
        self.bot.encoding_channels = {}

        if client_plugin is not None:
            (plugin_name, config, channel) = client_plugin
            self.bot.load_channel_plugins(channel)

        if server_plugin is not None:
            self.bot.load_server_plugins()

        # configure the dispatcher
        self.bot.dispatcher.init(self.bot.config)

        self.answer = []
        def g(towhere, msg, _):
            self.answer.append((towhere, msg.decode("utf8")))
        self.bot.msg = g

        self.disp = self.bot.dispatcher
        for plugin in self.bot.dispatcher._plugins.keys():
            fullname = "%s.%s" % (plugin.__module__, plugin.__class__.__name__)
            if fullname == plugin_name:
                self.plugin = plugin
                break
        else:
            raise ValueError("The searched plugin does not exist!")

    def assertMessageInAnswer(self, message_idx, expected):
        """assert the content of message with index: message_idx in self.answer
        and handle unexpected errors properly."""
        try:
            self.assertEqual(self.answer[message_idx][1], expected, self.answer)
        except Exception, e:
            self.fail('Error: %s\nexpected: %r, but was: %r' % (e, expected, self.answer))
