# This is not a standard test case, but a special plugin that expect
# to be instantiated twice to talk to each other

from core import dispatcher
from core import events as evt


class TestPlugin(object):
    def __init__(self, client, config):
        self.identity = config["test_side"]
        self.client = client
        register = client.dispatcher.register

        # register to stuff
        register(evt.CONNECTION_MADE, self.conn_made)
        register(evt.CONNECTION_LOST, self.conn_lost)
        register(evt.SIGNED_ON, self.signed)
        register(evt.JOINED, self.joined)

    def conn_made(self):
        print "==================== Connection made!"

    def conn_lost(self):
        print "==================== Connection lost!"

    def signed(self):
        print "==================== Signed!"

    def joined(self, channel):
        print "==================== Joined!"
        return (channel, u"Hola! Soy %s" % self.client.nickname)
