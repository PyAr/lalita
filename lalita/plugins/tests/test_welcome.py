# -*- coding: utf8 -*-

# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file


from lalita import events
from .helper import PluginTest
from os import remove

class WelcomeTest(PluginTest):
    '''
    Unit test for the Welcome plugin.
    '''

    def setUp(self):
        '''Just init your module.Class.'''
        self.config = {'basedir': '.'}
        self.init(client_plugin=('lalita.plugins.welcome.Welcome', self.config, 'chnl'))

    def test_not_pythonista_user_joined(self):
        '''Lalita send public message to regular users'''
        self.disp.push(events.JOIN, 'saraza3', 'chnl')
        self.assertMessageInAnswer(0, u'saraza3: Bienvenido a chnl!')

    def test_not_pythonista_user_rejoined(self):
        '''Lalita send one public message to regular users'''
        self.disp.push(events.JOIN, 'saraza', 'chnl')
        self.assertMessageInAnswer(0, u'saraza: Bienvenido a chnl!')
        self.disp.push(events.JOIN, 'saraza', 'chnl')
        self.assertEqual(len(self.answer), 1)

    def test_public_message_to_pythonista_joined(self):
        '''Lalita send public message to pythonista users'''
        self.disp.push(events.JOIN, 'pyarense_1234', 'chnl')
        self.assertMessageInAnswer(0, u'pyarense_1234: Bienvenido a chnl!')

    def test_private_message_to_pythonista_joined(self):
        '''Lalita send private message to pythonista users'''
        self.disp.push(events.JOIN, 'pyarense_1234', 'chnl')
        self.assertMessageInAnswer(1, u'Aqui van algunas instrucciones')

    def test_not_pythonista_user_rejoined_in_other_channel(self):
        '''Lalita send public message to regular users in all channels'''
        self.disp.push(events.JOIN, 'saraza2', 'chnl')
        self.assertMessageInAnswer(0, u'saraza2: Bienvenido a chnl!')
        self.init(client_plugin=('lalita.plugins.welcome.Welcome', self.config, 'chnl2'))
        self.disp.push(events.JOIN, 'saraza2', 'chnl2')
        self.assertMessageInAnswer(0, u'saraza2: Bienvenido a chnl2!')

    def tearDown(self):
        try:
            remove('./users')
        except OSError:
            pass