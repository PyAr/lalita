# -*- coding: utf8 -*-

from core import events

from .helper import PluginTest

class TestPing(PluginTest):
    def setUp(self):
        self.init("misc.Ping")

    def test_ping(self):
        '''Test ping.'''
        self.disp.push(events.COMMAND, "pepe", "channel", "ping")
        self.assertEqual(self.answer[0][1], u"pepe: pong")
