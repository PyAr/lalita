# -*- coding: utf8 -*-

from core import events

from .helper import PluginTest

import re

class TestLog(PluginTest):
    def setUp(self):
        self.init("seen.Seen")

    def test_joined(self):
        '''Logs joined.'''
        self.disp.push(events.JOIN, "channel", "pepe")
        self.assertEqual(self.plugin.iolog["pepe"][0], "joined")
        self.assertEqual(self.plugin.saidlog, {})

    def test_parted(self):
        '''Logs parted.'''
        self.disp.push(events.PART, "channel", "pepe")
        self.assertEqual(self.plugin.iolog["pepe"][0], "parted")
        self.assertEqual(self.plugin.saidlog, {})

    def test_public_message(self):
        '''Logs public_message.'''
        self.disp.push(events.PUBLIC_MESSAGE, "pepe", "channel", "blah")
        self.assertEqual(self.plugin.saidlog["pepe"][0], "blah")
        self.assertEqual(self.plugin.iolog, {})

    def test_talked_to_me(self):
        '''Logs talked_to_me.'''
        self.disp.push(events.TALKED_TO_ME, "pepe", "channel", "blah")
        self.assertEqual(self.plugin.saidlog["pepe"][0], "blah")
        self.assertEqual(self.plugin.iolog, {})

    def test_log(self):
        '''How the logger works.'''
        # pepe joins
        self.plugin.log("channel", "pepe", "joined")
        self.assertEqual(self.plugin.iolog["pepe"][0], "joined")
        self.assertEqual(self.plugin.saidlog, {})

        # pepe says something
        self.plugin.log("channel", "pepe", "blah")
        self.assertEqual(self.plugin.iolog["pepe"][0], "joined")
        self.assertEqual(self.plugin.saidlog["pepe"][0], "blah")

        # pepe parts
        self.plugin.log("channel", "pepe", "parted")
        self.assertEqual(self.plugin.iolog["pepe"][0], "parted")
        self.assertEqual(self.plugin.saidlog["pepe"][0], "blah")

        # somebody else says something
        self.plugin.log("channel", "juan", "cuick")
        self.assertEqual(self.plugin.iolog["pepe"][0], "parted")
        self.assertEqual(self.plugin.saidlog["pepe"][0], "blah")
        self.assertEqual(self.plugin.saidlog["juan"][0], "cuick")

        # pepe says something more
        self.plugin.log("channel", "pepe", "more")
        self.assertEqual(self.plugin.iolog["pepe"][0], "parted")
        self.assertEqual(self.plugin.saidlog["pepe"][0], "more")
        self.assertEqual(self.plugin.saidlog["juan"][0], "cuick")


class TestSeen(PluginTest):
    def setUp(self):
        self.init("seen.Seen")

    def test_plugin(self):
        '''User asks about the bot.'''
        self.disp.push(events.COMMAND, "pepe", "channel",
                       "seen", self.plugin.nickname)
        self.assertEqual(self.answer[0][1], u"pepe: acástoi, papafrita!")

    def test_self(self):
        '''User asks about self.'''
        self.disp.push(events.COMMAND, "pepe", "channel", "seen", "pepe")
        self.assertEqual(self.answer[0][1],
                         u"pepe: andá mirate en el espejo del baño")

    def test_nothing(self):
        '''User asks about a silent one.'''
        self.disp.push(events.COMMAND, "pepe", "channel", "seen", "juan")
        self.assertEqual(self.answer[0][1],
                         u"pepe: se me quedó en la otra pollera :|")

    def test_joined(self):
        '''User asks about one that joined.'''
        self.disp.push(events.JOIN, "channel", "juan")
        self.disp.push(events.COMMAND, "pepe", "channel", "seen", "juan")
        m = re.match(u"pepe: \[.*\] -- joined", self.answer[0][1])
        self.assertTrue(m)

    def test_parted(self):
        '''User asks about one that parted.'''
        self.disp.push(events.PART, "channel", "juan")
        self.disp.push(events.COMMAND, "pepe", "channel", "seen", "juan")
        m = re.match(u"pepe: \[.*\] -- parted", self.answer[0][1])
        self.assertTrue(m)

    def test_said(self):
        '''User asks about one that said something.'''
        self.disp.push(events.PUBLIC_MESSAGE, "juan", "channel", "blah")
        self.disp.push(events.COMMAND, "pepe", "channel", "seen", "juan")
        m = re.match(u"pepe: \[.*\] blah", self.answer[0][1])
        self.assertTrue(m)

    def test_said_twice(self):
        '''User asks about one that said more than one thing.'''
        self.disp.push(events.PUBLIC_MESSAGE, "juan", "channel", "blah")
        self.disp.push(events.PUBLIC_MESSAGE, "juan", "channel", "juaz")
        self.disp.push(events.COMMAND, "pepe", "channel", "seen", "juan")
        m = re.match(u"pepe: \[.*\] juaz", self.answer[0][1])
        self.assertTrue(m)

    def test_joined_and_parted(self):
        '''User asks about one that joined and parted.'''
        self.disp.push(events.JOIN, "channel", "juan")
        self.disp.push(events.PART, "channel", "juan")
        self.disp.push(events.COMMAND, "pepe", "channel", "seen", "juan")
        m = re.match(u"pepe: \[.*\] -- parted", self.answer[0][1])
        self.assertTrue(m)

    def test_parted_and_joined(self):
        '''User asks about one that parted and joined.'''
        self.disp.push(events.PART, "channel", "juan")
        self.disp.push(events.JOIN, "channel", "juan")
        self.disp.push(events.COMMAND, "pepe", "channel", "seen", "juan")
        m = re.match(u"pepe: \[.*\] -- joined", self.answer[0][1])
        self.assertTrue(m)

    def test_joined_and_said(self):
        '''User asks about one that joined and said something.'''
        self.disp.push(events.JOIN, "channel", "juan")
        self.disp.push(events.PUBLIC_MESSAGE, "juan", "channel", "blah")
        self.disp.push(events.COMMAND, "pepe", "channel", "seen", "juan")
        m = re.match(u"pepe: \[.*\] blah", self.answer[0][1])
        self.assertTrue(m)

    def test_said_and_parted(self):
        '''User asks about one that said something and parted.'''
        self.disp.push(events.PUBLIC_MESSAGE, "juan", "channel", "blah")
        self.disp.push(events.PART, "channel", "juan")
        self.disp.push(events.COMMAND, "pepe", "channel", "seen", "juan")
        m = re.match(u"pepe: \[.*\] -- parted", self.answer[0][1])
        self.assertTrue(m)


class TestLast(PluginTest):
    def setUp(self):
        self.init("seen.Seen")

    def test_plugin(self):
        '''User asks about the bot.'''
        self.disp.push(events.COMMAND, "pepe", "channel",
                       "last", self.plugin.nickname)
        self.assertEqual(self.answer[0][1],
                         u'pepe: lo último fue "lo último fue ..."')

    def test_self(self):
        '''User asks about self.'''
        self.disp.push(events.COMMAND, "pepe", "channel", "last", "pepe")
        self.assertEqual(self.answer[0][1], u"pepe: me tiraste la órden")

    def test_nothing(self):
        '''User asks about a silent one.'''
        self.disp.push(events.COMMAND, "pepe", "channel", "last", "juan")
        self.assertEqual(self.answer[0][1], u"pepe: yo no oí nada...")

    def test_joined(self):
        '''User asks about one that joined.'''
        self.disp.push(events.JOIN, "channel", "juan")
        self.disp.push(events.COMMAND, "pepe", "channel", "last", "juan")
        self.assertEqual(self.answer[0][1], u"pepe: yo no oí nada...")

    def test_parted(self):
        '''User asks about one that parted.'''
        self.disp.push(events.PART, "channel", "juan")
        self.disp.push(events.COMMAND, "pepe", "channel", "last", "juan")
        self.assertEqual(self.answer[0][1], u"pepe: yo no oí nada...")

    def test_said(self):
        '''User asks about one that said something.'''
        self.disp.push(events.PUBLIC_MESSAGE, "juan", "channel", "blah")
        self.disp.push(events.COMMAND, "pepe", "channel", "last", "juan")
        m = re.match(u"pepe: \[.*\] blah", self.answer[0][1])
        self.assertTrue(m)

    def test_said_twice(self):
        '''User asks about one that said more than one thing.'''
        self.disp.push(events.PUBLIC_MESSAGE, "juan", "channel", "blah")
        self.disp.push(events.PUBLIC_MESSAGE, "juan", "channel", "juaz")
        self.disp.push(events.COMMAND, "pepe", "channel", "last", "juan")
        m = re.match(u"pepe: \[.*\] juaz", self.answer[0][1])
        self.assertTrue(m)

    def test_joined_and_parted(self):
        '''User asks about one that joined and parted.'''
        self.disp.push(events.JOIN, "channel", "juan")
        self.disp.push(events.PART, "channel", "juan")
        self.disp.push(events.COMMAND, "pepe", "channel", "last", "juan")
        self.assertEqual(self.answer[0][1], u"pepe: yo no oí nada...")

    def test_parted_and_joined(self):
        '''User asks about one that parted and joined.'''
        self.disp.push(events.PART, "channel", "juan")
        self.disp.push(events.JOIN, "channel", "juan")
        self.disp.push(events.COMMAND, "pepe", "channel", "last", "juan")
        self.assertEqual(self.answer[0][1], u"pepe: yo no oí nada...")

    def test_joined_and_said(self):
        '''User asks about one that joined and said something.'''
        self.disp.push(events.JOIN, "channel", "juan")
        self.disp.push(events.PUBLIC_MESSAGE, "juan", "channel", "blah")
        self.disp.push(events.COMMAND, "pepe", "channel", "last", "juan")
        m = re.match(u"pepe: \[.*\] blah", self.answer[0][1])
        self.assertTrue(m)

    def test_said_and_parted(self):
        '''User asks about one that said something and parted.'''
        self.disp.push(events.PUBLIC_MESSAGE, "juan", "channel", "blah")
        self.disp.push(events.PART, "channel", "juan")
        self.disp.push(events.COMMAND, "pepe", "channel", "last", "juan")
        m = re.match(u"pepe: \[.*\] blah", self.answer[0][1])
        self.assertTrue(m)

