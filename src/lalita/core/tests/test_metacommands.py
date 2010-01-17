# -*- coding: utf8 -*-

# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

import unittest

from collections import defaultdict

from lalita import dispatcher, events, ircbot

ircbot_factory = ircbot.IRCBotFactory(dict(log_config="error", channels=defaultdict(lambda: {})))
ircbot.logger.setLevel("error")
bot = ircbot.IrcBot()
bot.factory = ircbot_factory
bot.config = ircbot_factory.config
bot.msg = lambda *a:None

# FIXME: all these messages should be internationalized per server (not locale)
PREFIX_LIST = u"Las órdenes son: ".encode("utf8")
GENERIC_HELP = u'"list" para ver las órdenes; "help cmd" para cada uno'.encode("utf8")
NODOCSTRING = u"No tiene documentación, y yo no soy adivina...".encode("utf8")
MULTI_NODOCSTRING = u"%sNo tiene documentación, y yo no soy adivina...".encode("utf8")
SEVERALDOCS = u"Hay varios métodos para esa orden:".encode("utf8")
NOSUCHCMD = u"Esa orden no existe..."

trans_table = dispatcher.TRANSLATION_TABLE
PREFIX_LIST_EN = trans_table[u"Las órdenes son: %s"]['en'].encode("utf8")
GENERIC_HELP_EN = trans_table[u'"list" para ver las órdenes; "help cmd" para cada uno']['en'].encode("utf8")
NODOCSTRING_EN = trans_table[u"No tiene documentación, y yo no soy adivina..."]['en'].encode("utf8")
MULTI_NODOCSTRING_EN = trans_table[u"%sNo tiene documentación, y yo no soy adivina..."]['en'].encode("utf8")
SEVERALDOCS_EN = trans_table[u"Hay varios métodos para esa orden:"]['en'].encode("utf8")
NOSUCHCMD_EN = u"No such command..."


class TestList(unittest.TestCase):

    class Helper(object):
        def f(self, *a): pass
        def g(self, *a): pass

    def setUp(self):
        self.disp = dispatcher.Dispatcher(bot)
        self.disp.init({})

        self.said = []
        bot.msg = lambda *a: self.said.append(a)

        self.helper = self.Helper()
        self.disp.new_plugin(self.helper, "channel")
        self.prefix_list = PREFIX_LIST

    def test_1met_1cmd(self):
        self.disp.register(events.COMMAND, self.helper.f, ("t1",))
        self.disp.push(events.COMMAND, "user", "channel", "list")
        self.assertEqual(self.said[0][1],
                         self.prefix_list + "['help', 'list', 'more', 't1']")

    def test_1met_2cmd(self):
        self.disp.register(events.COMMAND, self.helper.f, ("t1", "t2"))
        self.disp.push(events.COMMAND, "user", "channel", "list")
        self.assertEqual(self.said[0][1], self.prefix_list +
                                        "['help', 'list', 'more', 't1', 't2']")

    def test_2met_1cmd(self):
        self.disp.register(events.COMMAND, self.helper.f, ("t1",))
        self.disp.register(events.COMMAND, self.helper.g, ("t2",))
        self.disp.push(events.COMMAND, "user", "channel", "list")
        self.assertEqual(self.said[0][1], self.prefix_list +
                                        "['help', 'list', 'more', 't1', 't2']")

    def test_2met_2cmd(self):
        self.disp.register(events.COMMAND, self.helper.f, ("t1", "t2"))
        self.disp.register(events.COMMAND, self.helper.g, ("t3", "t4"))
        self.disp.push(events.COMMAND, "user", "channel", "list")
        self.assertEqual(self.said[0][1], self.prefix_list +
                            "['help', 'list', 'more', 't1', 't2', 't3', 't4']")

    def test_different_channels(self):
        helper2 = self.Helper()
        self.disp.new_plugin(helper2, "channel2")
        self.disp.register(events.COMMAND, self.helper.f, ("t1",))
        self.disp.register(events.COMMAND, helper2.f, ("t2",))
        self.disp.push(events.COMMAND, "user", "channel", "list")
        self.assertEqual(self.said[0][1],
                         self.prefix_list + "['help', 'list', 'more', 't1']")


class TestHelp(unittest.TestCase):
    class Helper(object):
        def f(self, *a):
            pass
        def g(self, *a):
            "foo"
        def h(self, *a):
            "bar"
        def i(self, *a):
            pass

    def setUp(self):
        self.disp = dispatcher.Dispatcher(bot)
        self.disp.init({})

        self.said = []
        bot.msg = lambda *a: self.said.append(a)

        self.helper = self.Helper()
        self.disp.new_plugin(self.helper, "channel")
        self.generic_help = GENERIC_HELP
        self.nodocstring = NODOCSTRING
        self.severaldocs = SEVERALDOCS
        self.nosuchcmd = NOSUCHCMD

    def test_generic_help(self):
        self.disp.push(events.COMMAND, "user", "channel", "help")
        self.assertEqual(self.said[0][1], self.generic_help)

    def test_no_doc(self):
        self.disp.register(events.COMMAND, self.helper.f, ("cmd",))
        self.disp.push(events.COMMAND, "user", "channel", "help", "cmd")
        self.assertEqual(self.said[0][1], self.nodocstring)

    def test_simple_doc(self):
        self.disp.register(events.COMMAND, self.helper.g, ("cmd",))
        self.disp.push(events.COMMAND, "user", "channel", "help", "cmd")
        self.assertEqual(self.said[0][1], "foo")

    def test_repeated_doc(self):
        self.disp.register(events.COMMAND, self.helper.g, ("cmd",))
        self.disp.register(events.COMMAND, self.helper.h, ("cmd",))
        self.disp.push(events.COMMAND, "user", "channel", "help", "cmd")
        self.assertEqual(self.said[0][1], self.severaldocs)
        self.assertEqual(self.said[1][1], " - foo")
        self.assertEqual(self.said[2][1], " - bar")

    def test_repeated_no_doc(self):
        self.disp.register(events.COMMAND, self.helper.f, ("cmd",))
        self.disp.register(events.COMMAND, self.helper.i, ("cmd",))
        self.disp.push(events.COMMAND, "user", "channel", "help", "cmd")
        self.assertEqual(self.said[0][1], self.severaldocs)
        self.assertEqual(self.said[1][1], " - " + self.nodocstring)
        self.assertEqual(self.said[2][1], " - " + self.nodocstring)

    def test_mixed_no_doc(self):
        self.disp.register(events.COMMAND, self.helper.g, ("cmd",))
        self.disp.register(events.COMMAND, self.helper.i, ("cmd",))
        self.disp.push(events.COMMAND, "user", "channel", "help", "cmd")
        self.assertEqual(self.said[0][1], self.severaldocs)
        self.assertEqual(self.said[1][1], " - foo")
        self.assertEqual(self.said[2][1], " - " + self.nodocstring)

    def test_different_channels(self):
        helper2 = self.Helper()
        self.disp.new_plugin(helper2, "channel2")
        self.disp.register(events.COMMAND, self.helper.g, ("cmd1",))
        self.disp.register(events.COMMAND, helper2.g, ("cmd2",))

        # check from channel
        self.disp.push(events.COMMAND, "user", "channel", "help", "cmd1")
        self.assertEqual(self.said[0][1], "foo")

        # reset said, and check from channel2
        self.said[:] = []
        self.disp.push(events.COMMAND, "user", "channel2", "help", "cmd1")
        self.assertEqual(self.said[0][1], self.nosuchcmd)


class TestMoreHelp(unittest.TestCase):
    '''With the plugin in more channels.'''
    def setUp(self):
        self.disp = dispatcher.Dispatcher(bot)
        self.disp.init({})

        self.said = []
        bot.msg = lambda *a: self.said.append(a)

        class Helper(object):
            def f(self, *a):
                pass
            def g(self, *a):
                "foo"
            def h(self, *a):
                "bar"
            def i(self, *a):
                pass
        self.help1 = Helper()
        self.help2 = Helper()
        self.disp.new_plugin(self.help1, "channel")
        self.disp.new_plugin(self.help2, "chann2")
        self.generic_help = GENERIC_HELP
        self.nodocstring = NODOCSTRING
        self.severaldocs = SEVERALDOCS

    def test_generic_help(self):
        self.disp.push(events.COMMAND, "user", "channel", "help")
        self.assertEqual(self.said[0][1], self.generic_help)

    def test_no_doc(self):
        self.disp.register(events.COMMAND, self.help1.f, ("cmd",))
        self.disp.register(events.COMMAND, self.help2.f, ("cmd",))
        self.disp.push(events.COMMAND, "user", "channel", "help", "cmd")
        self.assertEqual(self.said[0][1], self.nodocstring)

    def test_simple_doc(self):
        self.disp.register(events.COMMAND, self.help1.g, ("cmd",))
        self.disp.register(events.COMMAND, self.help2.g, ("cmd",))
        self.disp.push(events.COMMAND, "user", "channel", "help", "cmd")
        self.assertEqual(self.said[0][1], "foo")

    def test_repeated_doc(self):
        self.disp.register(events.COMMAND, self.help1.g, ("cmd",))
        self.disp.register(events.COMMAND, self.help1.h, ("cmd",))
        self.disp.register(events.COMMAND, self.help2.g, ("cmd",))
        self.disp.register(events.COMMAND, self.help2.h, ("cmd",))
        self.disp.push(events.COMMAND, "user", "channel", "help", "cmd")
        self.assertEqual(self.said[0][1], self.severaldocs)
        self.assertEqual(self.said[1][1], " - foo")
        self.assertEqual(self.said[2][1], " - bar")

    def test_repeated_no_doc(self):
        self.disp.register(events.COMMAND, self.help1.f, ("cmd",))
        self.disp.register(events.COMMAND, self.help1.i, ("cmd",))
        self.disp.register(events.COMMAND, self.help2.f, ("cmd",))
        self.disp.register(events.COMMAND, self.help2.i, ("cmd",))
        self.disp.push(events.COMMAND, "user", "channel", "help", "cmd")
        self.assertEqual(self.said[0][1], self.severaldocs)
        self.assertEqual(self.said[1][1], " - " + self.nodocstring)
        self.assertEqual(self.said[2][1], " - " + self.nodocstring)

    def test_mixed_no_doc(self):
        self.disp.register(events.COMMAND, self.help1.g, ("cmd",))
        self.disp.register(events.COMMAND, self.help1.i, ("cmd",))
        self.disp.register(events.COMMAND, self.help2.g, ("cmd",))
        self.disp.register(events.COMMAND, self.help2.i, ("cmd",))
        self.disp.push(events.COMMAND, "user", "channel", "help", "cmd")
        self.assertEqual(self.said[0][1], self.severaldocs)
        self.assertEqual(self.said[1][1], " - foo")
        self.assertEqual(self.said[2][1], " - " + self.nodocstring)


class TestHelpI18n(TestHelp):

    def setUp(self):
        super(TestHelpI18n, self).setUp()
        self.generic_help = GENERIC_HELP_EN
        self.nodocstring = NODOCSTRING_EN
        self.severaldocs = SEVERALDOCS_EN
        self.nosuchcmd = NOSUCHCMD_EN
        self.disp.config['language'] = 'en'


class TestMoreHelpI18n(TestMoreHelp):

    def setUp(self):
        super(TestMoreHelpI18n, self).setUp()
        self.generic_help = GENERIC_HELP_EN
        self.nodocstring = NODOCSTRING_EN
        self.severaldocs = SEVERALDOCS_EN
        self.disp.config['language'] = 'en'


class TestHelpI18nChannel(TestHelp):

    def setUp(self):
        super(TestHelpI18nChannel, self).setUp()
        self.generic_help = GENERIC_HELP_EN
        self.nodocstring = NODOCSTRING_EN
        self.severaldocs = SEVERALDOCS_EN
        self.disp.config['channels'] = {'channel':{'language':'en'}}


class TestMoreHelpI18nChannel(TestMoreHelp):

    def setUp(self):
        super(TestMoreHelpI18nChannel, self).setUp()
        self.generic_help = GENERIC_HELP_EN
        self.nodocstring = NODOCSTRING_EN
        self.severaldocs = SEVERALDOCS_EN
        self.disp.config['channels'] = {'channel':{'language':'en'}}

class TestHelpI18nMissing(TestHelp):

    def setUp(self):
        super(TestHelpI18nMissing, self).setUp()
        self.disp.config['channels'] = {'channel':{'language':'ar'}}


class TestMoreHelpI18nMissing(TestMoreHelp):

    def setUp(self):
        super(TestMoreHelpI18nMissing, self).setUp()
        self.disp.config['channels'] = {'channel':{'language':'ar'}}
