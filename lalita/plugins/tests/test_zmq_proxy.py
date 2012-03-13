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
                                 {"pub_address":"inproc://pub_addr",
                                  "cmd_address":"inproc://sub_addr"}))
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

    @defer.inlineCallbacks
    def test_restart_action(self):
        """Restart a plugin."""
        called = []
        self.patch(self.plugin, 'restart_process', called.append)
        msg = {'action':'restart', 'name':"foo"}
        self.cmd.send(json.dumps(msg))
        d = defer.Deferred()
        reactor.callLater(0.2, lambda: d.callback(None))
        yield d
        self.assertEqual(called[0], 'foo')

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
            events.COMMAND:("channel", "user"),
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

    @defer.inlineCallbacks
    def test_start_process(self):
        """Handle all events."""
        plugin = self.disp._plugins.keys()[0]
        cmd_args = ("-c \"import zmq; c=zmq.Context(); s=c.socket(zmq.SUB); "
                    "s.setsockopt(zmq.SUBSCRIBE, 'irc'); s.recv()\"")
        plugin.config["plugins"] = {
            'test_process':{
                'executable':'python',
                'arguments':[cmd_args],
                'config':{}
            }
        }
        plugin._start_process("test_process")
        proc = plugin._plugins["test_process"]
        self.assertTrue(proc.pid > 0)
        self.assertEqual(proc.status, -1)
        proto = proc.proto
        self.assertIsInstance(proto, PluginProcess)
        proc.loseConnection()
        try:
            yield proto.deferred
        except error.ProcessTerminated:
            self.assertEqual(proc.pid, None)
            self.assertEqual(proc.status, 256)
            pass
        else:
            self.fail("Should get ProcessTerminated")


class TestSubProcessPlugin(TwistedTestCase):

    def test_init(self):
        self.fail()

    def test_register(self):
        self.fail()

    def test_register_command(self):
        self.fail()

    def test_say(self):
        self.fail()
