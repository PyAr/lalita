# -*- coding: utf8 -*-

from core import events

from .helper import PluginTest

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

#    def test_cmd_foo_empty(self):
#        '''Check 'foo' functionality, no msg.'''
#        self.disp.push(events.COMMAND, "Usr", "chnl", "foo")
#        self.assertEqual(self.answer[0][1],
#                         u"Usr: Me tenés que decir algo para que lo repita!")
#
#    def test_cmd_foo_sth(self):
#        '''Check 'foo' functionality, with something.'''
#        self.disp.push(events.COMMAND, "Usr", "chnl", "foo", "repite")
#        self.assertEqual(self.answer[0][1], u"repite")
#
#    def test_cmd_bar(self):
#        '''Check 'bar' functionality.'''
#        self.disp.push(events.COMMAND, "Usr", "chnl", "bar")
#        self.assertEqual(self.answer[0][1], u"Del Zen de Python:")
#        self.assertTrue(len(self.answer[1][1]))
#
#    def test_cmd_twisted(self):
#        '''Check 'twisted' functionality.'''
#        self.disp.push(events.COMMAND, "Usr", "chnl", "enroscau")
#        self.assertEqual(self.answer[0][1],
#                         "Te prometo a futuro un saludo en el canal")
