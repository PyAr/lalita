# -*- coding: utf-8 -*-
import unittest

import twisted.web.client as client
from twisted.internet import defer

from lalita import events
from lalita.plugins import man
from .helper import PluginTest


class ManTest(PluginTest):
    """ Tests for Man plugin """

    def setUp(self):
        """ Init Man plugin """
        self.init(client_plugin=("lalita.plugins.man.Man", {}, "chnl"))
        self.patched = []

    def tearDown(self):
        for obj, attr, value in self.patched:
            setattr(obj, attr, value)

    def test_not_found(self):
        """ Test not found module """
        mock = lambda _: defer.fail(1)
        self.patch(client, 'getPage', mock)
        self.disp.push(events.COMMAND, "testuser", "chnl",
                       "man", "nosuchmodule")
        expected_response = u"I don't know where the docs for nosuchmodule are"
        self.assertMessageInAnswer(0, expected_response)

    def test_found(self):
        """ Test found module """
        mock = lambda _: defer.succeed(1)
        self.patch(client, 'getPage', mock)
        self.disp.push(events.COMMAND, "testuser", "chnl",
                       "man", "existingmodule")
        manurl = u"http://docs.python.org/library/%s.html" % "existingmodule"
        expected_response = u"The documentation for %s is here: %s" % \
                            ("existingmodule", manurl)
        self.assertMessageInAnswer(0, expected_response)

    def test_not_found_py3(self):
        """ Test not found module for Python 3"""
        mock = lambda _: defer.fail(1)
        self.patch(client, 'getPage', mock)
        self.disp.push(events.COMMAND, "testuser", "chnl",
                       "man3", "nosuchmodule")
        expected_response = u"I don't know where the docs for nosuchmodule are"
        self.assertMessageInAnswer(0, expected_response)

    def test_found_py3(self):
        """ Test found module for Python 3"""
        mock = lambda _: defer.succeed(1)
        self.patch(client, 'getPage', mock)
        self.disp.push(events.COMMAND, "testuser", "chnl",
                       "man3", "existingmodule")
        manurl = u"http://docs.python.org/py3k/library/%s.html" % \
                 "existingmodule"
        expected_response = u"The documentation for %s is here: %s" % \
                            ("existingmodule", manurl)
        self.assertMessageInAnswer(0, expected_response)

    def patch(self, obj, attr, value):
        self.patched.append((obj, attr, getattr(obj, attr)))
        setattr(obj, attr, value)


class ParseModulesTest(unittest.TestCase):

    def test_basic(self):
        mods = man._parse_modules((u'urllib', u'socket',))
        self.assertEqual(mods, [u'urllib', u'socket'])

    def test_comma_separated(self):
        mods = man._parse_modules((u'urllib,socket',))
        self.assertEqual(mods, [u'urllib', u'socket'])

    def test_comma_and_space(self):
        mods = man._parse_modules((u'urllib, socket',))
        self.assertEqual(mods, [u'urllib', u'socket'])
