# -*- coding: utf8 -*-

# Copyright 2010 laliputienses
# License: GPL v3
# For further info, see LICENSE file

from lalita import events

from .helper import PluginTest


class TestSet(PluginTest):
    def setUp(self):
        self.init(client_plugin=("lalita.plugins.photo.Photo", {}, "canal"))

    def test_set_self(self):
        """Sets own photo."""
        self.disp.push(events.COMMAND, "pepe", "canal", "foto", "pepe", "url")
        self.assertEqual(self.answer[0][1], u"pepe: URL configured!")
        self.assertEqual(self.plugin._get_photo("pepe"), "url")

    def test_unset_initial(self):
        """Unset own photo, without having no one."""
        self.disp.push(events.COMMAND, "pepe", "canal", "foto", "pepe", "None")
        self.assertEqual(self.answer[0][1],
                         u"pepe: doesn't have configured URL")
        self.assertEqual(self.plugin._get_photo("pepe"), None)

    def test_unset_having(self):
        """Unset own photo."""
        self.disp.push(events.COMMAND, "pepe", "canal", "foto", "pepe", "url")
        self.disp.push(events.COMMAND, "pepe", "canal", "foto", "pepe", "None")
        self.assertEqual(self.answer[1][1], u"pepe: URL removed (was: url )")
        self.assertEqual(self.plugin._get_photo("pepe"), None)

    def test_set_self_twice(self):
        """Sets own photo twice."""
        self.disp.push(events.COMMAND, "pepe", "canal", "foto", "pepe", "url1")
        self.assertEqual(self.answer[0][1], u"pepe: URL configured!")
        self.disp.push(events.COMMAND, "pepe", "canal",
                       "foto", "pepe", "url2")
        self.assertEqual(self.answer[1][1], u"pepe: URL configured!")
        self.assertEqual(self.plugin._get_photo("pepe"), "url2")

    def test_set_twice_otheruser(self):
        """Two different users set own photo."""
        self.disp.push(events.COMMAND, "juan", "canal", "foto", "juan", "url1")
        self.assertEqual(self.answer[0][1], u"juan: URL configured!")
        self.disp.push(events.COMMAND, "pepe", "canal",
                       "foto", "pepe", "url2")
        self.assertEqual(self.answer[1][1], u"pepe: URL configured!")
        self.assertEqual(self.plugin._get_photo("juan"), "url1")
        self.assertEqual(self.plugin._get_photo("pepe"), "url2")

    def test_set_baduser(self):
        """You can not set other's photo."""
        self.disp.push(events.COMMAND, "juan", "canal", "foto", "pepe", "url1")
        self.assertEqual(self.answer[0][1],
                         u"juan: can't change other user's photo")

    def test_baduser_not_affects(self):
        """Bad user error does not affect any previous config."""
        self.disp.push(events.COMMAND, "juan", "canal", "foto", "juan", "url1")
        self.disp.push(events.COMMAND, "pepe", "canal", "foto", "pepe", "url2")
        self.disp.push(events.COMMAND, "juan", "canal", "foto", "pepe", "url3")
        self.assertEqual(self.answer[2][1],
                         u"juan: can't change other user's photo")
        self.assertEqual(self.plugin._get_photo("juan"), "url1")
        self.assertEqual(self.plugin._get_photo("pepe"), "url2")


class TestGet(PluginTest):
    def setUp(self):
        self.init(client_plugin=("lalita.plugins.photo.Photo", {}, "canal"))

    def test_noparams(self):
        """No parameters."""
        self.disp.push(events.COMMAND, "pepe", "canal", "foto")
        self.assertEqual(self.answer[0][1],
                         u"pepe: tell me the nick")

    def test_no_url(self):
        """No url configured."""
        self.disp.push(events.COMMAND, "pepe", "canal", "foto", "pepe")
        self.assertEqual(self.answer[0][1],
                         u"pepe: doesn't have configured URL")

    def test_url_own(self):
        """Own url configured."""
        self.disp.push(events.COMMAND, "pepe", "canal", "foto", "pepe", "url")
        self.disp.push(events.COMMAND, "pepe", "canal", "foto", "pepe")
        self.assertEqual(self.answer[1][1], u"pepe: url")

    def test_url_other(self):
        """Other url configured."""
        self.disp.push(events.COMMAND, "juan", "canal", "foto", "juan", "url")
        self.disp.push(events.COMMAND, "pepe", "canal", "foto", "juan")
        self.assertEqual(self.answer[1][1], u"pepe: url")

    def test_url_mixed(self):
        """Several urls configured."""
        self.disp.push(events.COMMAND, "juan", "canal", "foto", "juan", "url1")
        self.disp.push(events.COMMAND, "pepe", "canal", "foto", "pepe", "url2")
        self.disp.push(events.COMMAND, "pepe", "canal", "foto", "juan")
        self.assertEqual(self.answer[2][1], u"pepe: url1")
        self.disp.push(events.COMMAND, "pepe", "canal", "foto", "pepe")
        self.assertEqual(self.answer[3][1], u"pepe: url2")
        self.disp.push(events.COMMAND, "juan", "canal", "foto", "juan")
        self.assertEqual(self.answer[4][1], u"juan: url1")
        self.disp.push(events.COMMAND, "juan", "canal", "foto", "pepe")
        self.assertEqual(self.answer[5][1], u"juan: url2")

