# -*- coding: utf8 -*-

# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

from lalita import events
from .helper import PluginTest


class TestFumador(PluginTest):
    def setUp(self):
        '''Just init your module.Class.'''
        self.init("lalita.plugins.fumador.Fumador")

    def test_message(self):
        '''Check 'public' functionality.'''
        self.disp.push(events.PUBLIC_MESSAGE, "testuser", "channel", "vamos a fumar?")
        self.assertMessageInAnswer(0, u'Uhhhh... Está hablando del fasooo!')
