# This is not a standard test case, but a special plugin that expect
# to be instantiated twice to talk to each other

from core import dispatcher
from core import events as evt


class TestPlugin(object):
    def __init__(self, config):
        self.identity = config["test_side"]
        register = dispatcher.dispatcher.register

        # register to stuff
        register(evt.CONNECTION_MADE, self.conn_made)

    def conn_made(self):
        print "==================== Connection made!"
