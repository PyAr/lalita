#!/usr/bin/env python

# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

# based on irc client example, Copyright (c) 2001-2004 Twisted Matrix Laboratories.

# system imports
import sys
import logging
import os.path
import optparse
from traceback import print_exc

# twisted imports
from twisted.internet import reactor, protocol, ssl
from twisted.words.protocols import irc

# local imports
from lalita import dispatcher, events

LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

log_stdout_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s %(name)s:%(lineno)-4d "
                              "%(levelname)-8s %(message)s",
                              '%Y-%m-%d %H:%M:%S')
log_stdout_handler.setFormatter(formatter)
logger = logging.getLogger('ircbot')
logger.addHandler(log_stdout_handler)
logger.setLevel(logging.DEBUG)


class IrcBot (irc.IRCClient):
    """A IRC bot."""
    def __init__ (self, *more):
        self.dispatcher = dispatcher.Dispatcher(self)
        self._plugins = {}
        logger.info("We're in(ited)!")

    def load_plugin (self, plugin_name, config, params, channel=None):
        if "plugins_dir" in self.config:
            path = self.config["plugins_dir"]
        else:
            path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                                'plugins')
        logger.debug("Adding plugin's path %r", path)
        sys.path.append(path)

        modname, klassname= plugin_name.rsplit ('.', 1)
        loglvl = self.config["log_config"].get(plugin_name)
        try:
            module = __import__(modname, globals(), locals(), [''])
            klass = getattr(module, klassname)
            instance = klass(params, loglvl)
            self.dispatcher.new_plugin(instance, channel)
            instance.init(config)
        except ImportError, e:
            logger.error('%s not instanced: %s', plugin_name, e)
        except AttributeError, e:
            logger.error('%s not instanced: %s', plugin_name, e)
        except Exception, e:
            logger.error('%s not instanced: %s', plugin_name, e)
            print_exc (e)
        else:
            logger.info('%s instanced for %s', plugin_name,
                        (channel is not None) and channel or 'server')

    def load_server_plugins(self):
        params = {'nickname': self.nickname,
                  'encoding': self.encoding_server}

        plugins = self.config.get('plugins', {})
        logger.debug("server plugins: %s", plugins)
        for plugin, config in plugins.items():
            self.load_plugin(plugin, config, params)

    def load_channel_plugins(self, channel):
        params = {'nickname': self.nickname,
                  'encoding': self.encoding_channels.get('channel',
                                       self.encoding_server)}

        plugins = self.config['channels'][channel].get('plugins', {})
        logger.debug("channel plugins: %s", plugins)
        for plugin, config in plugins.items ():
            self.load_plugin(plugin, config, params, channel)

    def connectionMade(self):
        # configure the bot
        self.config = self.factory.config
        self.nickname = self.config.get('nickname', 'lalita')
        self.encoding_server = self.config.get('encoding', 'utf8')
        self.encoding_channels = dict((k, v["encoding"])
                                    for k,v in self.config["channels"].items()
                                      if "encoding" in v)
        self.password = self.config.get('password', None)
        self.command_char = self.config.get('command_char', '@')
        irc.IRCClient.connectionMade (self)
        logger.info("connected to %s:%d",
                    self.config['host'], self.config['port'])
        self.load_server_plugins()
        # configure the dispatcher
        self.dispatcher.init(self.config)
        self.dispatcher.push(events.CONNECTION_MADE)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        logger.info("disconnected from %s:%d",
                    self.config.get('host'), self.config.get('port'))
        self.dispatcher.push(events.CONNECTION_LOST)

    def signedOn(self):
        logger.debug("signed on %s:%d",
                     self.config['host'], self.config['port'])
        self.dispatcher.push(events.SIGNED_ON)
        for channel in self.config.get ('channels', []):
            logger.debug("joining %s on %s:%d",
                         channel, self.config['host'], self.config['port'])
            self.join (channel)

    def receivedMOTD(self, motd):
        logger.debug("motd from %s:%d",
                     self.config['host'], self.config['port'])

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        logger.info("joined to %s", channel)
        self.load_channel_plugins (channel)
        self.dispatcher.push(events.JOINED, channel)

    def get_config(self, channel, parameter):
        """Get the configuration for the server, overwritten by channel."""
        chancfg = self.config['channels']
        if channel in chancfg and parameter in chancfg[channel]:
            return self.config['channels'][channel][parameter]
        return self.config.get(parameter)  # default to None

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        # decode according to channel (that can be an user), or server/default
        encoding = self.encoding_channels.get(channel, self.encoding_server)
        msg = msg.decode(encoding)

        logger.debug("[%s] %s: %s", channel, user, msg)
        user = user.split('!', 1)[0]
        indirect = bool(self.get_config(channel, 'indirect_command'))

        # Check to see if they're sending me a private message
        if channel == self.nickname:
            self.dispatcher.push(events.PRIVATE_MESSAGE, user, msg)
        # Otherwise check to see if it is a message directed at me
        elif msg.startswith(self.nickname):
            rest = msg[len(self.nickname):]
            if rest[0] in (":", " ", ","):
                rest = rest[1:].strip()
                if indirect:
                    args = rest.split()
                    command = args.pop(0)
                    self.dispatcher.push(events.COMMAND, user, channel,
                                         command, *args)
                else:
                    self.dispatcher.push(events.TALKED_TO_ME, user,
                                         channel, rest)
            else:
                self.dispatcher.push(events.PUBLIC_MESSAGE, user, channel, msg)
        elif msg[0] == self.command_char:
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
    def userJoined(self, user, channel):
        """Called when I see another user joining a channel."""
        logger.debug("%s joined to %s", user, channel)
        self.dispatcher.push(events.JOIN, user, channel)

    def userLeft(self, user, channel):
        """Called when I see another user leaving a channel."""
        logger.debug("%s left %s", user, channel)
        self.dispatcher.push(events.LEFT, user, channel)

    def userQuit(self, user, quit_message):
        """Called when I see another user disconnect from the network."""
        logger.debug("%s quited IRC: %s", user, quit_message)
        self.dispatcher.push(events.QUIT, user, quit_message)

    def userKicked(self, kickee, channel, kicker, message):
        """Called when I observe someone else being kicked from a channel."""
        logger.debug("%s was kicked by %s from %s because of:",
                     kickee, channel, kicker, message)
        self.dispatcher.push(events.KICK, kickee, channel, kicker, message)

    def userRenamed(self, oldname, newname):
        """Called when I see another user to change their nick."""
        logger.debug("%s changed its nick to %s", oldname, newname)
        self.dispatcher.push(events.RENAME, oldname, newname)


class IRCBotFactory(protocol.ReconnectingClientFactory):
    """
    A factory for PyAr Bots.
    A new protocol instance will be created each time we connect to the server.
    """

    # the class of the protocol to build when new connection is made
    protocol = IrcBot

    def __init__(self, server_config):
        self.config = server_config
        self.bot = None

    def clientConnectionLost(self, connector, reason):
        """
        If we get disconnected, reconnect to server.
        """
        logger.debug("We got disconnected because of %s", reason)
        protocol.ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        """
        Stop main loop if connection failed, this should be changed to stop
        only when no client remains connected
        """
        logger.debug("Connection failed because of %s", reason)
        protocol.ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

    def buildProtocol(self, addr):
        """Setup the protocol."""
        logger.debug('Connected!, resetting reconnection delay.')
        self.resetDelay()
        p = protocol.ReconnectingClientFactory.buildProtocol(self, addr)
        self.bot = p
        return p

def start_manhole(servers, port, user, password):
    """Starts manhole with the specified options, if it's available."""
    try:
        from twisted.conch import manhole, manhole_ssh
        from twisted.cred import portal, checkers
    except ImportError, e:
        logger.warning('Manhole not available: %s', e)
        return

    def getManholeFactory(namespace, **passwords):
        realm = manhole_ssh.TerminalRealm()
        def getManhole(_):
            return manhole.Manhole(namespace)
        realm.chainedProtocolFactory.protocolFactory = getManhole
        p = portal.Portal(realm)
        p.registerChecker(
        checkers.InMemoryUsernamePasswordDatabaseDontUse(**passwords))
        f = manhole_ssh.ConchFactory(p)
        return f
    manhole_factory = getManholeFactory({'servers':servers}, **{user:password})
    reactor.listenTCP(port, manhole_factory, interface='127.0.0.1')


class FactoriesWrapper(object):
    """
    dict like object that simplifies the access to IRCBot instances.
    Only keys() and __getitem__ are supported.
    """
    __slots__ = ('factories',)

    def __init__(self, factories):
        """Create the instance"""
        self.factories = factories

    def keys(self):
        """return the list of servers"""
        return self.factories.keys()

    def __getitem__(self, server):
        """Return the IRCBot instance of 'server'"""
        return self.factories[server].bot

    def __str__(self):
        return str(repr(self))

    def __repr__(self):
        d = {}
        for k, f in self.factories.items():
            d[k] = f.bot
        return d.__repr__()


def main(to_use, plugin_loglvl, manhole_opts=None):
    factories = {}
    for server in to_use:
        server["log_config"] = plugins_loglvl
        bot = IRCBotFactory(server)
        factories[server.get('host')] = bot
        if server.get('ssl', False):
            reactor.connectSSL(server.get('host', '10.100.0.194'),
                               server.get('port', 6667), bot,
                               ssl.ClientContextFactory())
        else:
            reactor.connectTCP(server.get('host', '10.100.0.194'),
                               server.get('port', 6667), bot)
    if manhole_opts:
        manhole_opts['servers'] = FactoriesWrapper(factories)
        start_manhole(**manhole_opts)
    reactor.run()


if __name__ == '__main__':
    msg = """
  ircbot.py config_filename [-t][-a][-o output_loglvl][-p plugins_loglvl]
            [-f fileloglvl][-n logfname] [server1, [...]]

  the config_filename is required
  the servers are optional if -a is passed
  the output_loglevel is the log level for the standard output
  the file_loglevel is the log level for the output that goes to file
  the pluginloglevel is a list of plugin_name:loglevel separated by commas
  the logfname is the filename to write the logs to
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
    parser.add_option("-f", "--file-log-level", dest="fileloglvl",
                      help="sets the output log level.")
    parser.add_option("-n", "--log-filename", dest="logfname",
                      help="specifies the name of the log file.")
    # manhole option group
    manhole = parser.add_option_group('manhole')
    manhole.add_option("--manhole", dest="manhole", action="store_true",
                       help="Enable manhole ssh server (listening on 127.0.0.1)" + \
                       "\n*WARNING*: Note that this will open up a serious " + \
                       "security hole on your computer as now anybody knowing " + \
                       "this password may login to the Python console and get " + \
                       "full access to the system with the permissions of the user " + \
                       "running the script.")
    manhole.add_option("--manhole-port", dest="manhole_port", type='int',
                       metavar='PORT', default=2222,
                       help="Use the specified port, default: 2222")
    manhole.add_option("--manhole-user", dest="manhole_user", default='admin',
                       metavar='USER',
                       help="Use the specified user for manhole ssh, default: admin")
    manhole.add_option("--manhole-password", dest="manhole_password",
                       metavar='PASSWORD', default='admin',
                       help="Use the specified password for manhole ssh, default: admin")

    (options, args) = parser.parse_args()
    test = bool(options.test)
    all_servers = bool(options.all_servers)

    # control the configuration file
    if len(args) < 1:
        parser.print_help()
        exit()
    else:
        config_filename = args[0]

    # control the servers
    if len(args) < 2 and not all_servers and not test:
        parser.print_help()
        exit()

    # control the output log level
    if options.outloglvl is None:
        output_loglevel = "info"
    else:
        output_loglevel = options.outloglvl.lower()
    try:
        log_stdout_handler.setLevel(LOG_LEVELS[output_loglevel])
    except KeyError:
        print "The log level can be only:", LOG_LEVELS.keys()
        exit(1)

    # control the plugins log level
    plugins_loglvl = {}
    if options.plugloglvl is not None:
        try:
            for pair in options.plugloglvl.split(","):
                plugin, loglvl = pair.split(":")
                loglvl = loglvl.lower()
                logger.debug("plugin %s, loglevel %s" % (plugin, loglvl))
                if loglvl not in LOG_LEVELS:
                    print "The log level can be only:", LOG_LEVELS.keys()
                    exit(1)
                plugins_loglvl[plugin] = LOG_LEVELS[loglvl]
        except:
            print "Remember that the plugin log level format is"
            print "   a list of plugin_name:loglevel separated by commas"
            print "Example:   misc.Ping:debug,example.Example:info"
            raise

    try:
        config = {}
        execfile(config_filename, config)
    except ImportError:
        print "A config file is needed to run this program."
        print "See as an example the included here lalita.cfg.sample"
        sys.exit()

    # handles the log file and its level
    if options.logfname is None:
        log_filename = "lalita.log"
    else:
        log_filename = options.logfname

    if options.fileloglvl is None:
        file_loglevel = logging.INFO
    else:
        try:
            file_loglevel = LOG_LEVELS[options.fileloglvl.lower()]
        except KeyError:
            print "The log level can be only:", LOG_LEVELS.keys()
            exit(1)

    fh = logging.FileHandler(log_filename)
    fh.setLevel(file_loglevel)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # get all servers or the indicated ones
    servers = config.get('servers', {})
    if all_servers:
        to_use = [v for k,v in servers.items() if not k.startswith("testbot")]
    elif test:
        to_use = [servers[x] for x in ("testbot-a", "testbot-b")]
    else:
        to_use = [servers[x] for x in args[1:]]

    if options.manhole:
        manhole_opts = dict(user=options.manhole_user,
                            port=options.manhole_port,
                            password=options.manhole_password)

    else:
        manhole_opts = None

    main(to_use, plugins_loglvl, manhole_opts=manhole_opts)
