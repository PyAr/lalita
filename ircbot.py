# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.

# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

# system imports
import time
import sys
import logging
import optparse

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(message)s",
                              '%H:%M:%S')
handler.setFormatter(formatter)
logger = logging.getLogger ('ircbot')
logger.addHandler(handler)
logger.setLevel (logging.DEBUG)
# logger.setLevel (logging.INFO)

# local imports
from core import events
from core import dispatcher
from config import servers

class IrcBot (irc.IRCClient):
    """A IRC bot."""
    def __init__ (self):
        self.dispatcher= dispatcher.dispatcher
        logger.debug ("we're in(ited)!")

    def connectionMade (self):
        self.config= self.factory.config
        self.nickname= self.config.get ('nickname', 'lalita')
        irc.IRCClient.connectionMade (self)
        logger.info ("connected to %s:%d" %
            (self.config['host'], self.config['port']))
        self.dispatcher.push (events.CONNECTION_MADE)

    def connectionLost (self, reason):
        irc.IRCClient.connectionLost(self, reason)
        logger.info ("disconnected from %s:%d" %
            (self.config.get('host'), self.config.get('port')))
        self.dispatcher.push (events.CONNECTION_LOST)

    def signedOn (self):
        logger.debug ("signed on %s:%d" %
            (self.config['host'], self.config['port']))
        self.dispatcher.push (events.SIGNED_ON)
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
        self.dispatcher.push (events.JOINED, channel)

    def privmsg (self, user, channel, msg):
        """This will get called when the bot receives a message."""
        logger.debug (msg)
        user = user.split('!', 1)[0]
        # self.logger.log("<%s> %s" % (user, msg))

        # Check to see if they're sending me a private message
        if channel == self.nickname:
            self.dispatcher.push (events.PRIVATE_MESSAGE, user, msg)
        # Otherwise check to see if it is a message directed at me
        elif msg.startswith (self.nickname + ":"):   # FIXME ":" puede ser cualquier signo de puntuacion o espacio
            self.dispatcher.push (events.TALKED_TO_ME, user, channel, msg)
            pass
        elif msg[0] == '@':   # FIXME: esta @ hay que sacarla de la config
            args = msg.split()
            command = args.pop(0)[1:]
            self.dispatcher.push(events.COMMAND, user, channel, command, *args)
        else:
            self.dispatcher.push(events.PUBLIC_MESSAGE, user, channel, msg)

    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        user = user.split('!', 1)[0]
        # FIXME: la llamada al push!!

    # irc callbacks

    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]


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

def main(to_use):
    for server in to_use:
        bot = IRCBotFactory(server)
        reactor.connectTCP(server.get('host', '10.100.0.194'),
                           server.get('port', 6667),
                           bot)
    reactor.run()


if __name__ == '__main__':
    msg = u"""
  ircbot.py [-t][-a] [server1, [...]]

  the servers are optional if -a is passed
"""

    parser = optparse.OptionParser()
    parser.set_usage(msg)
    parser.add_option("-t", "--test", action="store_true", dest="test",
                      help="runs two bots that talk to each other, tesing")
    parser.add_option("-a", "--all", action="store_true", dest="all_servers",
                      help="runs the bot to all the configured servers")

    (options, args) = parser.parse_args()
    test = bool(options.test)
    all_servers = bool(options.all_servers)

    if not args and not all_servers and not test:
        parser.print_help()
        exit()

    # get all servers or the indicated ones
    if all_servers:
        to_use = servers.values()
        if "testbot" in to_use:
            del to_use["testbot"]
    elif test:
        to_use = servers["testbot"]
    else:
        to_use = [servers[x] for x in args]

    main(to_use)
