"""ZeroMQ proxy plugin."""

import json
import logging
import os
import re
import sys

import zmq

from twisted.internet import reactor, defer
from twisted.internet.protocol import ProcessProtocol

from txzmq.pubsub import ZmqSubConnection
from txzmq import ZmqFactory, ZmqEndpoint

from lalita import Plugin
from lalita.core import events


EVENT_MAP = {
    events.CONNECTION_MADE:("irc.connection_made", None, None),
    events.CONNECTION_LOST:("irc.connection_lost", None, None),
    events.SIGNED_ON:("irc.signed_on", None, None),
    events.JOINED:("irc.joined", 0, None),
    events.PRIVATE_MESSAGE:("irc.private_message", None, 0),
    events.TALKED_TO_ME:("irc.talked_to_me", 1, 0),
    events.COMMAND:("irc.command", 1, 0),
    events.PUBLIC_MESSAGE:("irc.public_message", 1, 0),
    events.ACTION:("irc.action", 1, 0),
    events.JOIN:("irc.join", 1, 0),
    events.LEFT:("irc.left", 1, 0),
    events.QUIT:("irc.quit", None, 0),
    events.KICK:("irc.kick", 1, 0),
    events.RENAME:("irc.rename", None, 0),
}


class PluginProcess(ProcessProtocol):

    def __init__(self, name):
        self.name = name
        self.deferred = defer.Deferred()

    def processExited(self, status):
        self.deferred.callback(status)

    def processEnded(self, status):
        if not self.deferred.called:
            self.deferred.callback(status)

    def outReceived(self, data):
        sys.stdout.flush()

    def errReceived(self, data):
        sys.stdout.flush()


class BotConnection(ZmqSubConnection):

    def __init__(self, plugin, factory, endpoint):
        ZmqSubConnection.__init__(self, factory, endpoint)
        self.plugin = plugin

    def messageReceived(self, *a, **kw):
        return ZmqSubConnection.messageReceived(self, *a, **kw)

    def gotMessage(self, message):
        info = json.loads(message)
        if info['action'] == "say":
            if isinstance(info['to_whom'], unicode):
                self.plugin.say(info['to_whom'].encode('utf-8'), info['msg'], *info['args'])
            else:
                self.plugin.say(info['to_whom'], info['msg'], *info['args'])

        if info["action"] == "restart":
            self.plugin.restart_process(info['name'])


class EventHandler(object):

    def __init__(self, plugin, event_name, channel_pos, user_pos):
        self.name = event_name
        self.channel_pos = channel_pos
        self.user_pos = user_pos
        self.plugin = plugin
        self.im_self = plugin
        self.im_func = self.__call__
        self.logger = plugin.logger

    def __call__(self, *args):
        self.logger.debug("event: %s", args)
        msg_args = {}
        if self.channel_pos is not None:
            msg_args['channel'] = args[self.channel_pos]
        if self.user_pos is not None:
            msg_args['user'] = args[self.user_pos]
        msg_args['args'] = [a for i, a in enumerate(args) \
                            if i != self.channel_pos and i != self.user_pos]
        self.logger.debug("publishing: %s - %s", self.name, msg_args)
        self.plugin.publish(self.name, msg_args)


class ZMQPlugin(Plugin):

    def init(self, config):
        self._plugins = {}
        self.config = config
        pub_address = self.config['pub_address']
        cmd_address = self.config['cmd_address']
        self.ctx = zmq.Context.instance()
        self.pub_socket = self.ctx.socket(zmq.PUB)
        self.pub_socket.bind(pub_address)
        # callback/command socket
        zmq_factory = ZmqFactory(context=self.ctx)
        rpc_endpoint = ZmqEndpoint("bind", cmd_address)
        self.cmd_socket = BotConnection(self, zmq_factory, rpc_endpoint)
        self.cmd_socket.subscribe("")
        self._start_plugins()
        for event, info in EVENT_MAP.items():
            if event == events.COMMAND:
                self.register(event, EventHandler(self, *info), None)
            else:
                self.register(event, EventHandler(self, *info), re.compile(".*"))

    def shutdown(self):
        self.cmd_socket.shutdown()
        self.pub_socket.close()
        self.ctx.term()
        for proc in self._plugins.values():
            proc.loseConnection()

    def publish(self, name, msg_args):
        self.pub_socket.send(name, zmq.SNDMORE)
        self.pub_socket.send(json.dumps(msg_args))

    def _start_plugins(self):
        for name in self.config.get('plugins', {}):
            self._start_process(name)

    def _start_process(self, name):
        plugin_cfg = self.config['plugins'][name]
        executable = plugin_cfg['executable']
        if executable == 'python':
            executable = sys.executable
        cmd_args = plugin_cfg.get('arguments', [])
        env = plugin_cfg.get('env', {})
        proto = PluginProcess(name)
        args = [executable] + cmd_args
        plugin_config = plugin_cfg.get('config', {})
        plugin_config['sub_address'] = self.config['pub_address']
        plugin_config['bot_address'] = self.config['cmd_address']
        env['plugin_config'] = json.dumps(plugin_config)
        env.update(os.environ)
        process = reactor.spawnProcess(proto, executable, args, env)
        self._plugins[name] = process

    def restart_process(self, name):
        old_proc = self._plugins.pop(name)
        old_proc.loseConnection()
        self._start_process(name)


class SubProcessPlugin(object):

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger("lalita.zmq_plugin.%s" %
                                        (self.__class__.__name__,))
        self.ctx = zmq.Context()
        self.sub_socket = self.ctx.socket(zmq.SUB)
        self.sub_socket.connect(self.config['sub_address'])
        self.sub_socket.setsockopt(zmq.SUBSCRIBE, "irc")
        # create the bot socket
        self.bot_socket = self.ctx.socket(zmq.PUB)
        self.bot_socket.connect(self.config['bot_address'])
        # setup the event handler
        self._events = {}

    def register_command(self, function, command_name):
        self._events['irc.command'] = (function, command_name)

    def register(self, event, function, matcher=None):
        self._events[event] = (function, matcher)

    def say(self, to_whom, msg, *args):
        new_msg = {'action':'say', 'to_whom':to_whom, "msg":msg, "args":args}
        self.bot_socket.send(json.dumps(new_msg))

    def run(self):
        """Main loop"""
        while True:
            # block waiting for a message
            event = self.sub_socket.recv()
            payload = json.loads(self.sub_socket.recv())
            try:
                handler, matcher = self._events[event]
            except KeyError:
                self.logger.error("No handler for %s", event)
            else:
                if event == "irc.command" or matcher is not None:
                    match = matcher(payload['args'])
                else:
                    match = True
                if match:
                    user = payload.get('user')
                    channel = payload.get('channel')
                    args = [a for a in [user, channel] + payload['args'] \
                            if a is not None]
                    handler(*args)
                else:
                    self.logger.debug("No match for %s", payload)

