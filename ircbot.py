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

class IrcBot (irc.IRCClient):
    """A IRC bot."""
    def __init__ (self):
        irc.IRCClient.__init__ (self)
        self.dispatcher= Dispatcher ()
        self.config= self.factory.config
        self.nickname= self.config.get ('nickname', 'lalita')
        logger.debug ("we're in(ited)!")

    def connectionMade (self):
        irc.IRCClient.connectionMade (self)
        logger.info ("connected to %s:%d" %
            (self.config['host'], self.config['port']))
        self.dispatcher.push (events.connection_made)

    def connectionLost (self, reason):
        irc.IRCClient.connectionLost(self, reason)
        logger.info ("disconnected from %s:%d" %
            (self.config['host'], self.config['port']))
        self.dispatcher.push (events.connection_lost)

    def signedOn(self):
        logger.debug ("signed on %s:%d" %
        self.dispatcher.push (events.signed_on)
        for channel in config.get ('channels', []):
            logger.debug ("joining %s on %s:%d" %
                (channel, self.config['host'], self.config['port']))
            self.join (channel)

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        logger.info ("joined to %s" % channel)
        self.dispatcher.push (events.joined, channel)

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        user = user.split('!', 1)[0]
        # self.logger.log("<%s> %s" % (user, msg))

        # Check to see if they're sending me a private message
        if channel==self.nickname:
            self.dispatcher.push (events.privmsg, user, msg)
        # Otherwise check to see if it is a message directed at me
        elif msg.startswith (self.nickname + ":"):
            self.dispatcher.push (events.talkedtome, user, channel, msg)
            pass
        elif msg[0]=='@':
            args= msg.split()
            command= args.pop (0)[1:]
            self.dispatcher.push (events.command, command user, channel, args)

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


class IrcBotFactory(protocol.ClientFactory):
    # the class of the protocol to build when new connection is made
    protocol = IrcBot

    def __init__(self, channel, filename):
        self.channel = channel
        self.filename = filename

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()


if __name__ == '__main__':
    # initialize logging
    log.startLogging(sys.stdout)

    # create factory protocol and application
    f = LogBotFactory(sys.argv[1], sys.argv[2])

    # connect factory to this host and port
    reactor.connectTCP("irc.freenode.net", 6667, f)

    # run bot
    reactor.run()
