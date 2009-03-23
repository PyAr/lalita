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
logger = logging.getLogger ('ircbot')
logger.setLevel (logging.INFO)

# local imports
from core import events
from core.dispatcher import Dispatcher
import config

class IrcBot (irc.IRCClient):
    """A IRC bot."""
    def __init__ (self):
        irc.IRCClient.__init__ (self)
        self.nickname= self.config.get ('nickname', 'lalita')
        self.dispatcher= Dispatcher (self.nickname)
        self.config= self.factory.config
        logger.debug ("we're in(ited)!")

    def connectionMade (self):
        irc.IRCClient.connectionMade (self)
        logger.info ("connected to %s:%d" %
            (self.config['host'], self.config['port']))
        self.dispatcher.push (events.CONNECTION_MADE)

    def connectionLost (self, reason):
        irc.IRCClient.connectionLost(self, reason)
        logger.info ("disconnected from %s:%d" %
            (self.config['host'], self.config['port']))
        self.dispatcher.push (events.CONNECTION_LOST)

    def signedOn(self):
        logger.debug ("signed on %s:%d" %
        self.dispatcher.push (events.SIGNED_ON)
        for channel in config.get ('channels', []):
            logger.debug ("joining %s on %s:%d" %
                (channel, self.config['host'], self.config['port']))
            self.join (channel)

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        logger.info ("joined to %s" % channel)
        self.dispatcher.push (events.JOINED, channel)

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        user = user.split('!', 1)[0]
        # self.logger.log("<%s> %s" % (user, msg))

        # Check to see if they're sending me a private message
        if channel==self.nickname:
            self.dispatcher.push (events.PRIVATE_MESSAGE, user, msg)
        # Otherwise check to see if it is a message directed at me
        elif msg.startswith (self.nickname + ":"):
            self.dispatcher.push (events.TALKED_TO_ME, user, channel, msg)
            pass
        elif msg[0]=='@':
            args= msg.split()
            command= args.pop (0)[1:]
            self.dispatcher.push (events.COMMAND, command, user, channel, args)
        else:
            self.dispatcher.push (events.PUBLIC_MESSAGE, user, channel, msg)

    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        user = user.split('!', 1)[0]
        self.logger.log("* %s %s" % (user, msg))

    # irc callbacks

    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        self.logger.log("%s is now known as %s" % (old_nick, new_nick))


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
        reactor.stop()



if __name__ == '__main__':
    for server in irc_servers:
        bot = IRCBotFactory(irc_servers[server])
        reactor.connectTCP(irc_servers[server].get('host', 'localhost'), irc_servers[server].get('port', 6667), bot)

    reactor.run()
