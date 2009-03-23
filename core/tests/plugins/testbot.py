# This is not a standard test case, but a special plugin that expect
# to be instantiated twice to talk to each other

from core import dispatcher
from core import events as evt


class TestPlugin(object):
    def __init__(self, config, params):
        self.other = config["general"]["other"]
        register = params["register"]
        self.nickname = params["nickname"]

        # register to stuff
        register(evt.CONNECTION_MADE, self.conn_made)
        register(evt.CONNECTION_LOST, self.conn_lost)
        register(evt.SIGNED_ON, self.signed)
        register(evt.JOINED, self.joined)

        # helpers for testing
        self.state = "disconnected"

    def _check_state(self, from_st, to_st):
        if self.state == from_st:
            self.state = to_st
        else:
            raise ValueError(
                "Bad state going to %s: %r" % (to_st, self.state))

    def conn_made(self):
        self._check_state("disconnected", "connected")
        print "==================== Connection made!"

    def conn_lost(self):
        self._check_state("joined", "disconnected")
        print "==================== Connection lost!"

    def signed(self):
        self._check_state("connected", "signed")
        print "==================== Signed!"

    def joined(self, channel):
        self._check_state("signed", "joined")
        print "==================== Joined!"
        return (channel, u"Hola! Soy %s" % self.nickname)


