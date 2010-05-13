# -*- coding: utf8 -*-

# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

from lalita import events
from .helper import PluginTest


class TestFumador(PluginTest):
    def setUp(self):
        '''Just init your module.Class.'''
        self.init(client_plugin=(
                  "lalita.plugins.fumador.Fumador", {}, 'channel'))

    def test_message_yes(self):
        '''When the word is mentioned, it answers.'''
        self.disp.push(events.PUBLIC_MESSAGE, "testuser", "channel",
                       "vamos a fumar?")
        self.assertMessageInAnswer(0, u'Uhhhh... Está hablando del fasooo!')

    def test_message_no(self):
        '''When the word is not mentioned, it does not answer.'''
        self.disp.push(events.PUBLIC_MESSAGE, "testuser", "channel", "foo bar")
        self.assertEqual(len(self.answer), 0)
