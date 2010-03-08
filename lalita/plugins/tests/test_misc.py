# -*- coding: utf8 -*-

# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

from lalita import events
from .helper import PluginTest


class TestPing(PluginTest):
    def setUp(self):
        self.init(client_plugin=("lalita.plugins.misc.Ping", {}, "channel"))

    def test_ping(self):
        '''Test ping.'''
        self.disp.push(events.COMMAND, "pepe", "channel", "ping")
        self.assertEqual(self.answer[0][1], u"pepe: pong")
