# -*- coding: utf8 -*-

# Copyright 2010 laliputienses
# License: GPL v3
# For further info, see LICENSE file
import json
import time

from twisted.trial.unittest import TestCase as TwistedTestCase
from twisted.internet import defer, reactor, error

from lalita import events
from lalita.core.dispatcher import USER_POS, CHANNEL_POS

from .helper import PluginTest
from lalita.plugins.zmq_proxy import EVENT_MAP, PluginProcess

try:
    import zmq, txzmq
    zmq_available = True
except ImportError:
    zmq_available = False


class TestZMQPlugin(TwistedTestCase, PluginTest):

    if not zmq_available:
        skip = "pyzmq and txzmq required."

    def setUp(self):
        super(TestZMQPlugin, self).setUp()
        self.init(server_plugin=("lalita.plugins.zmq_proxy.ZMQPlugin",
                                 {"events_address":"inproc://pub_addr",
                                  "bot_address":"inproc://sub_addr"}))
        self.ctx = zmq.Context.instance()
        self.sub = self.ctx.socket(zmq.SUB)
        while True:
            try:
                self.sub.connect("inproc://pub_addr")
            except zmq.ZMQError:
                continue
            else:
                break
        self.sub.setsockopt(zmq.SUBSCRIBE, "")
        self.cmd = self.ctx.socket(zmq.PUB)
        while True:
            try:
                self.cmd.connect("inproc://sub_addr")
            except zmq.ZMQError:
                time.sleep(0.2)
                continue
            else:
                break

    def tearDown(self):
        self.sub.close()
        self.cmd.close()
        self.plugin.shutdown()
        return super(TestZMQPlugin, self).tearDown()

    @defer.inlineCallbacks
    def test_say_action(self):
        """Say something via zmq."""
        called = []
        self.patch(self.plugin, 'say', lambda *a: called.append(a))
        msg = {'action':'say', 'to_whom':"channel", "msg":"hola", "args":[]}
        self.cmd.send(json.dumps(msg))
        d = defer.Deferred()
        reactor.callLater(0.2, lambda: d.callback(None))
        yield d
        self.assertEqual(called[0], (msg['to_whom'].encode('utf-8'), msg['msg'].decode("utf-8")))

    def test_event_handler(self):
        """Handle all events."""
        called = []
        self.patch(self.plugin, 'publish', lambda *a: called.append(a))
        tested_events = {
            events.CONNECTION_MADE:(),
            events.CONNECTION_LOST:(),
            events.SIGNED_ON:(),
            events.JOINED:("channel",),
            events.PRIVATE_MESSAGE:("channel",),
            events.TALKED_TO_ME:("channel", "user"),
            events.PUBLIC_MESSAGE:("channel", "user"),
            events.ACTION:("channel", "user"),
            events.JOIN:("channel", "user"),
            events.LEFT:("channel", "user"),
            events.QUIT:("user",),
            events.KICK:("channel", "user"),
            events.RENAME:("user",)
        }
        for event, fixed_args in tested_events.items():
            msg = "a message"
            args = fixed_args + (msg,)
            self.disp.push(event, *args)
            kwargs = {}
            if CHANNEL_POS[event] is not None:
                kwargs['channel'] = args[CHANNEL_POS[event]]
            if USER_POS[event] is not None:
                kwargs['user'] = args[USER_POS[event]]
            kwargs['args'] = [msg]
            self.assertIn((EVENT_MAP[event][0], kwargs), called)


class TestPluginProcess(TwistedTestCase, PluginTest):
    """Tests for PluginProcess."""

    class TestPlugin(PluginProcess):
        def __init__(self, addr1, addr2, called, config=None):
            self.called = called
            super(TestPluginProcess.TestPlugin, self).__init__(addr1, addr2,
                                                               config=config)

        def init(self, config):
            self.config = config
            self.called.append(("init", config))

        def _connect(self, events_address, bot_address):
            self.ctx = zmq.Context.instance()
            self.sub_socket = self.ctx.socket(zmq.SUB)
            while True:
                try:
                    self.sub_socket.connect(events_address)
                except zmq.ZMQError:
                    time.sleep(0.1)
                    continue
                else:
                    break
            self.sub_socket.setsockopt(zmq.SUBSCRIBE, "")
            self.bot_socket = self.ctx.socket(zmq.PUB)
            while True:
                try:
                    self.bot_socket.connect(bot_address)
                except zmq.ZMQError:
                    time.sleep(0.1)
                    continue
                else:
                    break

    def setUp(self):
        super(TestPluginProcess, self).setUp()
        events_address = "inproc://pub_addr"
        bot_address = "inproc://sub_addr"
        self.init(server_plugin=("lalita.plugins.zmq_proxy.ZMQPlugin",
                                 {"events_address":events_address,
                                  "bot_address":bot_address}))
        self.called = []
        try:
            self.zmq_plugin = TestPluginProcess.TestPlugin(events_address,
                                                           bot_address,
                                                           self.called)
        except Exception, e:
            import traceback;
            traceback.print_exc()

    def tearDown(self):
        self.zmq_plugin.bot_socket.close()
        self.zmq_plugin.sub_socket.close()
        self.plugin.shutdown()
        return super(TestPluginProcess, self).tearDown()

    def test_init(self):
        """Test init is called."""
        self.assertEquals(self.called, [("init", None)])

    def test_register(self):
        """Register to en event."""
        matcher = lambda a: True
        func = lambda *a: True
        self.zmq_plugin.register(events.JOINED, func, matcher)
        self.assertIn(events.JOINED, self.zmq_plugin._events)
        self.assertEquals(self.zmq_plugin._events[events.JOINED], (func, matcher))

    def test_register_command(self):
        func = lambda a: None
        self.patch(self.zmq_plugin, '_send', self.called.append)
        self.zmq_plugin.register_command(func, "command")
        self.assertIn("irc.command", self.zmq_plugin._events)
        self.assertEquals(self.zmq_plugin._events["irc.command"][0][0], func)
        self.assertIn({'action':'register_command',
                       'command':["command"]}, self.called)

    def test_register_commands(self):
        func = lambda a: None
        self.patch(self.zmq_plugin, '_send', self.called.append)
        self.zmq_plugin.register_command(func, "command")
        self.assertIn("irc.command", self.zmq_plugin._events)
        self.assertEquals(self.zmq_plugin._events["irc.command"][0][0], func)
        self.assertIn({'action':'register_command',
                       'command':["command"]}, self.called)
        func1 = lambda a: None
        self.zmq_plugin.register_command(func1, "command1")
        self.assertEqual(len(self.zmq_plugin._events["irc.command"]), 2)
        self.assertEquals(self.zmq_plugin._events["irc.command"][1][0], func1)
        self.assertIn({'action':'register_command',
                       'command':["command1"]}, self.called)



    def test_say(self):
        self.patch(self.zmq_plugin, '_send', self.called.append)
        self.zmq_plugin.say("me", "message")
        self.assertIn({'action':'say', 'to_whom':'me', 'msg':"message",
                                  'args':()}, self.called)
