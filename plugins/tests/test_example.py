# -*- coding: utf8 -*-

import unittest

from twisted.trial.unittest import TestCase as TwistedTestCase
from twisted.internet import defer, reactor

from core import events
from core import dispatcher
import ircbot

class TestRegister(unittest.TestCase):

    test_server = dict(
        encoding = 'utf8',
        host='0.0.0.0', port=6667,
        nickname='test',
        channels={},
        plugins_dir="plugins",
    )

    def init(self, plugin_name):
        self.test_server["plugins"] = { plugin_name: {} }
        self.test_server["log_config"] = { plugin_name: "error" }
        ircbot.logger.setLevel("error")
        ircbot_factory = ircbot.IRCBotFactory(self.test_server)
        self.bot = ircbot.IrcBot()
        self.bot.factory = ircbot_factory
        self.bot.config = self.test_server
        self.bot.nickname = "TestBot"
        self.bot.load_server_plugins()
        self.bot.encoding_server = "utf-8"
        self.bot.encoding_channels = {}

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

    def setUp(self):
        self.init("example.Example")

    def test_private(self):
        '''Check 'private' functionality.'''
        self.disp.push(events.PRIVATE_MESSAGE, "testuser", "mensaje")
        self.assertEqual(self.answer[0][1], u'Me dijiste "mensaje"')

    def test_talkedtome(self):
        '''Check 'talked to me' functionality.'''
        self.disp.push(events.TALKED_TO_ME, "Usr", "chnl", "mensaje")
        self.assertEqual(self.answer[0][1],
                         u"Hola Usr, mi nombre es TestBot, :)")

    def test_cmd_foo_empty(self):
        '''Check 'foo' functionality, no msg.'''
        self.disp.push(events.COMMAND, "Usr", "chnl", "foo")
        self.assertEqual(self.answer[0][1],
                         u"Usr: Me tenés que decir algo para que lo repita!")

    def test_cmd_foo_sth(self):
        '''Check 'foo' functionality, with something.'''
        self.disp.push(events.COMMAND, "Usr", "chnl", "foo", "repite")
        self.assertEqual(self.answer[0][1], u"repite")

    def test_cmd_bar(self):
        '''Check 'bar' functionality.'''
        self.disp.push(events.COMMAND, "Usr", "chnl", "bar")
        self.assertEqual(self.answer[0][1], u"Del Zen de Python:")
        self.assertTrue(len(self.answer[1][1]))

    def test_cmd_twisted(self):
        '''Check 'twisted' functionality.'''
        self.disp.push(events.COMMAND, "Usr", "chnl", "enroscau")
        self.assertEqual(self.answer[0][1],
                         "Te prometo a futuro un saludo en el canal")
