# -*- coding: utf8 -*-

# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

from lalita import events
from .helper import PluginTest


class TestMethods(PluginTest):
    '''Example of unit test for plugins.

    You have the following info:

    - self.answer: what the plugin answered.
    - self.plugin: the instantiated and working plugin
    '''

    def setUp(self):
        '''Just init your module.Class.'''
        self.init(client_plugin=("lalita.plugins.example.Example", {}, "chnl"))

    def test_private(self):
        '''Check 'private' functionality.'''
        self.disp.push(events.PRIVATE_MESSAGE, "testuser", "mensaje")
        self.assertMessageInAnswer(0, u'Me dijiste "mensaje"')

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
        self.assertMessageInAnswer(0, u"repite")

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
