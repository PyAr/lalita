# -*- coding: utf8 -*-

# based on irc client example, Copyright (c) 2001-2004 Twisted Matrix Laboratories.

# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

# system imports
import time
import sys
import logging
import os
import os.path
import inspect
import optparse
from traceback import print_exc

# if we're in production, this should work and no magic is necessary
try:
    import lalita
except ImportError:
    import core
    sys.modules["lalita"] = core

# local imports
from core import events
from core import dispatcher

LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
                            "%(asctime)s %(name)s:%(lineno)-4d %(levelname)-8s %(message)s",
                            '%H:%M:%S')
handler.setFormatter(formatter)
logger = logging.getLogger('ircbot')
logger.addHandler(handler)


def nick (user):
    return user.split('!')[0]

class IrcBot (irc.IRCClient):
    """A IRC bot."""
    def __init__ (self, *more):
        self.dispatcher = dispatcher.Dispatcher(self)
        self._plugins = {}
        logger.debug ("we're in(ited)!")
        # logger.debug (more)

    def load_plugin (self, plugin_name, config, params, channel=None):
        # logger.debug (config)
        if "plugins_dir" in self.config:
            path = self.config["plugins_dir"]
        else:
            path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                                'plugins')
        sys.path.append(path)

        modname, klassname= plugin_name.split ('.')
        loglvl = self.config["log_config"].get(plugin_name)
        try:
            module = __import__(modname)
            klass = getattr(module, klassname)
            instance = klass(params, loglvl)
            self.dispatcher.new_plugin(instance, channel)
            instance.init(config)
        except ImportError, e:
            logger.error('%s not instanced: %s' % (plugin_name, e))
        except AttributeError, e:
            logger.error('%s not instanced: %s' % (plugin_name, e))
        except Exception, e:
            logger.error('%s not instanced: %s' % (plugin_name, e))
            print_exc (e)
        else:
            logger.info ('%s instanced for %s' % (plugin_name,
                (channel is not None) and channel or 'server'))

    def load_server_plugins(self):
        params = {'nickname': self.nickname,
                  'encoding': self.encoding_server
                  }

        plugins= self.config.get ('plugins', {})
        logger.debug ("server plugins: %s" % plugins)
        for plugin, config in plugins.items ():
            self.load_plugin (plugin, config, params)

    def load_channel_plugins(self, channel):
        params = {'nickname': self.nickname,
                  'encoding': self.encoding_channels.get('channel',
                                                         self.encoding_server)
                  }

        plugins= self.config['channels'][channel].get ('plugins', {})
        logger.debug ("channel plugins: %s" % plugins)
        for plugin, config in plugins.items ():
            self.load_plugin (plugin, config, params, channel)

    def connectionMade(self):
        self.config = self.factory.config
        self.nickname = self.config.get('nickname', 'lalita')
        self.encoding_server = self.config.get('encoding', 'utf8')
        self.encoding_channels = dict((k, v["encoding"])
                                    for k,v in self.config["channels"].items()
                                      if "encoding" in v)
        irc.IRCClient.connectionMade (self)
        logger.info("connected to %s:%d" %
            (self.config['host'], self.config['port']))
        self.load_server_plugins()
        # configure the dispatcher
        self.dispatcher.init(self.config)
        self.dispatcher.push(events.CONNECTION_MADE)

    def connectionLost (self, reason):
        irc.IRCClient.connectionLost(self, reason)
        logger.info ("disconnected from %s:%d" %
            (self.config.get('host'), self.config.get('port')))
        self.dispatcher.push(events.CONNECTION_LOST)

    def signedOn (self):
        logger.debug ("signed on %s:%d" %
            (self.config['host'], self.config['port']))
        self.dispatcher.push(events.SIGNED_ON)
        for channel in self.config.get ('channels', []):
            logger.debug ("joining %s on %s:%d" %
                (channel, self.config['host'], self.config['port']))
            self.join (channel)

    def receivedMOTD (self, motd):
        logger.debug ("motd from %s:%d" %
            (self.config['host'], self.config['port']))

    def joined (self, channel):
        """This will get called when the bot joins the channel."""
        logger.info ("joined to %s" % channel)
        self.load_channel_plugins (channel)
        self.dispatcher.push(events.JOINED, channel)

    def privmsg (self, user, channel, msg):
        """This will get called when the bot receives a message."""
        # decode according to channel (that can be an user), or server/default
        encoding = self.encoding_channels.get(channel, self.encoding_server)
        msg = msg.decode(encoding)

        logger.debug ("[%s] %s: %s" % (channel, user, msg))
        user = user.split('!', 1)[0]
        # self.logger.log("<%s> %s" % (user, msg))

        # Check to see if they're sending me a private message
        if channel == self.nickname:
            self.dispatcher.push(events.PRIVATE_MESSAGE, user, msg)
        # Otherwise check to see if it is a message directed at me
        elif msg.startswith (self.nickname):
            msg = msg[len(self.nickname):]
            if msg[0] in (":", " ", ","):
                msg = msg[1:].strip()
                self.dispatcher.push(events.TALKED_TO_ME, user, channel, msg)
        elif msg[0] == '@':
            args = msg.split()
            command = args.pop(0)[1:]
            self.dispatcher.push(events.COMMAND, user, channel, command, *args)
        else:
            self.dispatcher.push(events.PUBLIC_MESSAGE, user, channel, msg)

    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        # decode according to channel (that can be an user), or server/default
        encoding = self.encoding_channels.get(channel, self.encoding_server)
        msg = msg.decode(encoding)
        user = user.split('!', 1)[0]
        self.dispatcher.push(events.ACTION, user, channel, msg)

    # irc callbacks
    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        old_nick = nick (prefix)
        new_nick = params[0]
        irc.IRCClient.irc_NICK (self, prefix, params)

    def irc_JOIN (self, prefix, params):
        logger.debug ("join: %s: %s" % (prefix, params))
        channel= params[0]
        nickname= nick (prefix)
        self.dispatcher.push (events.JOIN, channel, nickname)
        irc.IRCClient.irc_JOIN (self, prefix, params)

    def irc_PART (self, prefix, params):
        logger.debug ("part: %s: %s" % (prefix, params))
        channel= params[0]
        nickname= nick (prefix)
        self.dispatcher.push (events.PART, channel, nickname)
        irc.IRCClient.irc_PART (self, prefix, params)

class IRCBotFactory(protocol.ClientFactory):
    """
    A factory for PyAr Bots.
    A new protocol instance will be created each time we connect to the server.
    """

    # the class of the protocol to build when new connection is made
    protocol = IrcBot

    def __init__(self, server_config):
        self.config = server_config

    def clientConnectionLost(self, connector, reason):
        """
        If we get disconnected, reconnect to server.
        """
        logger.debug("We got disconnected because of %s" % str(reason))
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        """
        Stop main loop if connection failed, this should be changed to stop
        only when no client remains connected
        """
        logger.debug("Connection failed because of %s" % str(reason))
        # reactor.stop()

def main(to_use, plugin_loglvl):
    for server in to_use:
        # logger.debug (plugin_loglvl)
        server["log_config"] = plugin_loglvl
        bot = IRCBotFactory(server)
        reactor.connectTCP(server.get('host', '10.100.0.194'),
                           server.get('port', 6667),
                           bot)
    reactor.run()


if __name__ == '__main__':
    msg = u"""
  ircbot.py [-t][-a][-o output_loglvl][-p plugin_loglvl] [server1, [...]]

  the servers are optional if -a is passed
  the output_loglevel is the log level default for all the system
  the pluginloglevel is a list of plugin_name:loglevel separated by commas
"""

    parser = optparse.OptionParser()
    parser.set_usage(msg)
    parser.add_option("-t", "--test", action="store_true", dest="test",
                      help="runs two bots that talk to each other, tesing.")
    parser.add_option("-a", "--all", action="store_true", dest="all_servers",
                      help="runs the bot to all the configured servers.")
    parser.add_option("-o", "--output-log-level", dest="outloglvl",
                      help="sets the output log level.")
    parser.add_option("-p", "--plugin-log-level", dest="plugloglvl",
                      help="sets the plugin log level. format is plugin:level,...")

    (options, args) = parser.parse_args()
    test = bool(options.test)
    all_servers = bool(options.all_servers)

    # control the servers
    if not args and not all_servers and not test:
        parser.print_help()
        exit()

    # control the log level
    if options.outloglvl is None:
        output_loglevel = "debug"
    else:
        output_loglevel = options.outloglvl.lower()
    try:
        logger.setLevel(LOG_LEVELS[output_loglevel])
    except KeyError:
        print "The log level can be only:", LOG_LEVELS.keys()
        exit(1)

    plugins_loglvl = {}
    if options.plugloglvl is not None:
        try:
            for pair in options.plugloglvl.split(","):
                plugin, loglvl = pair.split(":")
                loglvl = loglvl.lower()
                logger.debug ("plugin %s, loglevel %s" % (plugin, loglvl))
                if loglvl not in LOG_LEVELS:
                    print "The log level can be only:", LOG_LEVELS.keys()
                    exit()
                plugins_loglvl[plugin] = LOG_LEVELS[loglvl]
        except:
            print "Remember that the plugin log level format is"
            print "   a list of plugin_name:loglevel separated by commas"
            print "Example:   misc.Ping:debug,example.Example:info"
            raise

    try:
        import config
    except ImportError:
        print "A config file is needed to run this program."
        print "See as an example the included here config.py.example"
        sys.exit()

    # get all servers or the indicated ones
    servers = config.servers
    if all_servers:
        to_use = [v for k,v in servers.items() if not k.startswith("testbot")]
    elif test:
        to_use = [servers[x] for x in ("testbot-a", "testbot-b")]
    else:
        to_use = [servers[x] for x in args]


    main(to_use, plugins_loglvl)
