"""ZeroMQ proxy plugin."""

import json
import logging
import re

import zmq

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


class BotConnection(ZmqSubConnection):
    """Bot zmq connection."""

    def __init__(self, plugin, factory, endpoint):
        ZmqSubConnection.__init__(self, factory, endpoint)
        self.plugin = plugin

    def messageReceived(self, *a, **kw):
        return ZmqSubConnection.messageReceived(self, *a, **kw)

    def gotMessage(self, message):
        info = json.loads(message)
        if info['action'] == "say":
            if isinstance(info['to_whom'], unicode):
                self.plugin.say(info['to_whom'].encode('utf-8'),
                                info['msg'], *info['args'])
            else:
                self.plugin.say(info['to_whom'], info['msg'], *info['args'])
        elif info["action"] == "register_command":
            self.plugin.register_command(info['command'])
        else:
            self.plugin.log.error("Invalid Action %s", message)



class EventHandler(object):
    """Bridge of lalita event's to zmq messages."""

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
    """ZeroMQ plugin."""

    def init(self, config):
        self._plugins = {}
        self.config = config
        pub_address = self.config['events_address']
        cmd_address = self.config['bot_address']
        self.commands = set() # hold all the commands
        self.ctx = zmq.Context.instance()
        self.pub_socket = self.ctx.socket(zmq.PUB)
        self.pub_socket.bind(pub_address)
        # callback/command socket
        zmq_factory = ZmqFactory(context=self.ctx)
        rpc_endpoint = ZmqEndpoint("bind", cmd_address)
        self.cmd_socket = BotConnection(self, zmq_factory, rpc_endpoint)
        self.cmd_socket.subscribe("")
        for event, info in EVENT_MAP.items():
            if event != events.COMMAND:
                self.register(event, EventHandler(self, *info), re.compile(".*"))

    def shutdown(self):
        self.cmd_socket.shutdown()
        self.pub_socket.close()
        self.ctx.term()
        for proc in self._plugins.values():
            proc.loseConnection()

    def register_command(self, commands):
        """Register a list of commands."""
        if not self.commands.intersection(set(commands)):
            for command in commands:
                self.commands.add(command)
            self.register(events.COMMAND,
                          EventHandler(self, *EVENT_MAP[events.COMMAND]),
                          commands)
        # else, already registered.

    def publish(self, name, msg_args):
        """Publish a message/event."""
        self.pub_socket.send(name, zmq.SNDMORE)
        self.pub_socket.send(json.dumps(msg_args))


class PluginProcess(object):
    """Base class for ZeroMQ plugins."""

    def __init__(self, events_address, bot_address, config):
        self.config = config
        self.logger = logging.getLogger("zmq_plugin.%s" %
                                        (self.__class__.__name__,))
        self.ctx = zmq.Context()
        self.sub_socket = self.ctx.socket(zmq.SUB)
        self.sub_socket.connect(events_address)
        self.sub_socket.setsockopt(zmq.SUBSCRIBE, "irc")
        # create the bot socket
        self.bot_socket = self.ctx.socket(zmq.PUB)
        self.bot_socket.connect(bot_address)
        # setup the event handler
        self._events = {}

    def register_command(self, function, command_name):
        """Register a command."""
        self._events['irc.command'] = (function, lambda a: command_name in a)
        new_msg = {'action':'register_command', 'command':[command_name]}
        self.bot_socket.send(json.dumps(new_msg))

    def register(self, event, function, matcher=None):
        """Register a event handler."""
        self._events[event] = (function, matcher)

    def say(self, to_whom, msg, *args):
        """Say something."""
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

