# -*- coding: utf8 -*-

# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file


from lalita import events
from .helper import PluginTest


class WelcomeTest(PluginTest):
    '''
    Unit test for the Welcome plugin.
    '''

    def setUp(self):
        '''Just init your module.Class.'''
        config = {'message': u'$user: Bienvenido a $channel!'}
        self.init(client_plugin=('lalita.plugins.welcome.Welcome', config, 'chnl'))

    def test_user_joined(self):
        '''Lalita welcomes user after she joined'''
        self.disp.push(events.JOIN, 'testuser', 'chnl')
        self.assertMessageInAnswer(0, u'testuser: Bienvenido a chnl!')

    def test_user_joined_safe_string_formatting(self):
        '''Configured message can define any number of placeholders'''
        config = {'message': u'$user: Bienvenido!'}
        self.init(client_plugin=('lalita.plugins.welcome.Welcome', config, 'chnl'))
        self.disp.push(events.JOIN, 'testuser', 'chnl')
        self.assertMessageInAnswer(0, u'testuser: Bienvenido!')
