# -*- coding: utf8 -*-

# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

import os
import re
import shutil
import tempfile

from lalita import events
from .helper import PluginTest


class TestLog(PluginTest):
    def setUp(self):
        self.init(client_plugin=("lalita.plugins.seen.Seen", {}, "channel"))

    def test_joined(self):
        '''Logs joined.'''
        self.disp.push(events.JOIN, "pepe", "channel")
        self.assertEqual(self.plugin.iolog["pepe"][0], "joined")
        self.assertEqual(self.plugin.saidlog, {})

    def test_quit(self):
        '''Logs quit.'''
        self.disp.push(events.QUIT, "pepe", "why")
        self.assertEqual(self.plugin.iolog["pepe"][0], "quit IRC (why)")
        self.assertEqual(self.plugin.saidlog, {})

    def test_left(self):
        '''Logs left.'''
        self.disp.push(events.LEFT, "pepe", "channel")
        self.assertEqual(self.plugin.iolog["pepe"][0], "left")
        self.assertEqual(self.plugin.saidlog, {})

    def test_public_msg(self):
        '''Logs public_msg.'''
        self.disp.push(events.PUBLIC_MESSAGE, "pepe", "channel", "blah")
        self.assertEqual(self.plugin.saidlog["pepe"][0], "blah")
        self.assertEqual(self.plugin.iolog, {})

    def test_talked_to_me(self):
        '''Logs talked_to_me.'''
        self.disp.push(events.TALKED_TO_ME, "pepe", "channel", "blah")
        self.assertEqual(self.plugin.saidlog["pepe"][0], "blah")
        self.assertEqual(self.plugin.iolog, {})


class TestSeen(PluginTest):
    def setUp(self):
        self.init(client_plugin=("lalita.plugins.seen.Seen", {}, "channel"))

    def test_missing(self):
        '''User asks about nothing.'''
        self.disp.push(events.COMMAND, "pepe", "channel", "seen")
        self.assertEqual(self.answer[0][1], u"pepe: tenés que indicar un nick")

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
        self.disp.push(events.JOIN, "juan", "channel")
        self.disp.push(events.COMMAND, "pepe", "channel", "seen", "juan")
        m = re.match(u"pepe: \[.*\] -- joined", self.answer[0][1])
        self.assertTrue(m)

    def test_left(self):
        '''User asks about one that left.'''
        self.disp.push(events.LEFT, "juan", "channel")
        self.disp.push(events.COMMAND, "pepe", "channel", "seen", "juan")
        m = re.match(u"pepe: \[.*\] -- left", self.answer[0][1])
        self.assertTrue(m)

    def test_quit(self):
        '''User asks about one that quit.'''
        self.disp.push(events.QUIT, "juan", "msg")
        self.disp.push(events.COMMAND, "pepe", "channel", "seen", "juan")
        m = re.match(u"pepe: \[.*\] -- quit IRC \(msg\)", self.answer[0][1])
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

    def test_joined_and_left(self):
        '''User asks about one that joined and left.'''
        self.disp.push(events.JOIN, "juan", "channel")
        self.disp.push(events.LEFT, "juan", "channel")
        self.disp.push(events.COMMAND, "pepe", "channel", "seen", "juan")
        m = re.match(u"pepe: \[.*\] -- left", self.answer[0][1])
        self.assertTrue(m)

    def parted(self, nick, channel):
        '''Logs that the user has parted.'''
        self.logger.debug("%s parted %s", nick, channel)
        self.log(channel, nick, 'parted')

    def test_left_and_joined(self):
        '''User asks about one that left and joined.'''
        self.disp.push(events.LEFT, "juan", "channel")
        self.disp.push(events.JOIN, "juan", "channel")
        self.disp.push(events.COMMAND, "pepe", "channel", "seen", "juan")
        m = re.match(u"pepe: \[.*\] -- joined", self.answer[0][1])
        self.assertTrue(m)

    def test_joined_and_quit(self):
        '''User asks about one that joined and quit.'''
        self.disp.push(events.JOIN, "juan", "channel")
        self.disp.push(events.QUIT, "juan", "msg")
        self.disp.push(events.COMMAND, "pepe", "channel", "seen", "juan")
        m = re.match(u"pepe: \[.*\] -- quit IRC \(msg\)", self.answer[0][1])
        self.assertTrue(m)

    def test_quit_and_joined(self):
        '''User asks about one that quit and joined.'''
        self.disp.push(events.QUIT, "juan", "msg")
        self.disp.push(events.JOIN, "juan", "channel")
        self.disp.push(events.COMMAND, "pepe", "channel", "seen", "juan")
        m = re.match(u"pepe: \[.*\] -- joined", self.answer[0][1])
        self.assertTrue(m)

    def test_joined_and_said(self):
        '''User asks about one that joined and said something.'''
        self.disp.push(events.JOIN, "juan", "channel")
        self.disp.push(events.PUBLIC_MESSAGE, "juan", "channel", "blah")
        self.disp.push(events.COMMAND, "pepe", "channel", "seen", "juan")
        m = re.match(u"pepe: \[.*\] blah", self.answer[0][1])
        self.assertTrue(m)

    def test_said_and_left(self):
        '''User asks about one that said something and left.'''
        self.disp.push(events.PUBLIC_MESSAGE, "juan", "channel", "blah")
        self.disp.push(events.LEFT, "juan", "channel")
        self.disp.push(events.COMMAND, "pepe", "channel", "seen", "juan")
        m = re.match(u"pepe: \[.*\] -- left", self.answer[0][1])
        self.assertTrue(m)

    def test_said_and_quit(self):
        '''User asks about one that said something and quit.'''
        self.disp.push(events.PUBLIC_MESSAGE, "juan", "channel", "blah")
        self.disp.push(events.QUIT, "juan", "msg")
        self.disp.push(events.COMMAND, "pepe", "channel", "seen", "juan")
        m = re.match(u"pepe: \[.*\] -- quit IRC \(msg\)", self.answer[0][1])
        self.assertTrue(m)


class TestLast(PluginTest):
    def setUp(self):
        self.init(client_plugin=("lalita.plugins.seen.Seen", {}, "channel"))

    def test_missing(self):
        '''User asks about nothing.'''
        self.disp.push(events.COMMAND, "pepe", "channel", "last")
        self.assertEqual(self.answer[0][1], u"pepe: tenés que indicar un nick")

    def test_plugin(self):
        '''User asks about the bot.'''
        self.disp.push(events.COMMAND, "pepe", "channel",
                       "last", self.plugin.nickname)
        self.assertEqual(self.answer[0][1],
                         u'pepe: lo último fue "lo último fue ..."')

    def test_self(self):
        '''User asks about self.'''
        self.disp.push(events.COMMAND, "pepe", "channel", "last", "pepe")
        self.assertEqual(self.answer[0][1], u"pepe: me tiraste la orden")

    def test_nothing(self):
        '''User asks about a silent one.'''
        self.disp.push(events.COMMAND, "pepe", "channel", "last", "juan")
        self.assertEqual(self.answer[0][1], u"pepe: yo no oí nada...")

    def test_joined(self):
        '''User asks about one that joined.'''
        self.disp.push(events.JOIN, "juan", "channel")
        self.disp.push(events.COMMAND, "pepe", "channel", "last", "juan")
        self.assertEqual(self.answer[0][1], u"pepe: yo no oí nada...")

    def test_left(self):
        '''User asks about one that left.'''
        self.disp.push(events.LEFT, "juan", "channel")
        self.disp.push(events.COMMAND, "pepe", "channel", "last", "juan")
        self.assertEqual(self.answer[0][1], u"pepe: yo no oí nada...")

    def test_quit(self):
        '''User asks about one that quit.'''
        self.disp.push(events.QUIT, "juan", "msg")
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

    def test_joined_and_left(self):
        '''User asks about one that joined and left.'''
        self.disp.push(events.JOIN, "juan", "channel")
        self.disp.push(events.LEFT, "juan", "channel")
        self.disp.push(events.COMMAND, "pepe", "channel", "last", "juan")
        self.assertEqual(self.answer[0][1], u"pepe: yo no oí nada...")

    def test_left_and_joined(self):
        '''User asks about one that left and joined.'''
        self.disp.push(events.LEFT, "juan", "channel")
        self.disp.push(events.JOIN, "juan", "channel")
        self.disp.push(events.COMMAND, "pepe", "channel", "last", "juan")
        self.assertEqual(self.answer[0][1], u"pepe: yo no oí nada...")

    def test_joined_and_quit(self):
        '''User asks about one that joined and quit.'''
        self.disp.push(events.JOIN, "juan", "channel")
        self.disp.push(events.QUIT, "juan", "msg")
        self.disp.push(events.COMMAND, "pepe", "channel", "last", "juan")
        self.assertEqual(self.answer[0][1], u"pepe: yo no oí nada...")

    def test_quit_and_joined(self):
        '''User asks about one that quit and joined.'''
        self.disp.push(events.QUIT, "juan", "msg")
        self.disp.push(events.JOIN, "juan", "channel")
        self.disp.push(events.COMMAND, "pepe", "channel", "last", "juan")
        self.assertEqual(self.answer[0][1], u"pepe: yo no oí nada...")

    def test_joined_and_said(self):
        '''User asks about one that joined and said something.'''
        self.disp.push(events.JOIN, "juan", "channel")
        self.disp.push(events.PUBLIC_MESSAGE, "juan", "channel", "blah")
        self.disp.push(events.COMMAND, "pepe", "channel", "last", "juan")
        m = re.match(u"pepe: \[.*\] blah", self.answer[0][1])
        self.assertTrue(m)

    def test_said_and_left(self):
        '''User asks about one that said something and left.'''
        self.disp.push(events.PUBLIC_MESSAGE, "juan", "channel", "blah")
        self.disp.push(events.LEFT, "juan", "channel")
        self.disp.push(events.COMMAND, "pepe", "channel", "last", "juan")
        m = re.match(u"pepe: \[.*\] blah", self.answer[0][1])
        self.assertTrue(m)

    def test_said_and_quit(self):
        '''User asks about one that said something and quit.'''
        self.disp.push(events.PUBLIC_MESSAGE, "juan", "channel", "blah")
        self.disp.push(events.QUIT, "juan", "msg")
        self.disp.push(events.COMMAND, "pepe", "channel", "last", "juan")
        m = re.match(u"pepe: \[.*\] blah", self.answer[0][1])
        self.assertTrue(m)



class TestLogPersistent(TestLog):

    def setUp(self):
        self.base_dir = tempfile.mktemp()
        os.makedirs(self.base_dir)
        self.init(client_plugin=("lalita.plugins.seen.Seen",
                                 {'base_dir':self.base_dir}, "channel"))

    def tearDown(self):
        shutil.rmtree(self.base_dir)


class TestSeenPersistent(TestSeen):

    def setUp(self):
        self.base_dir = tempfile.mktemp()
        os.makedirs(self.base_dir)
        self.init(client_plugin=("lalita.plugins.seen.Seen",
                                 {'base_dir':self.base_dir}, "channel"))

    def tearDown(self):
        shutil.rmtree(self.base_dir)


class TestLastPersistent(TestLast):

    def setUp(self):
        self.base_dir = tempfile.mktemp()
        os.makedirs(self.base_dir)
        self.init(client_plugin=("lalita.plugins.seen.Seen",
                                 {'base_dir':self.base_dir}, "channel"))

    def tearDown(self):
        shutil.rmtree(self.base_dir)
