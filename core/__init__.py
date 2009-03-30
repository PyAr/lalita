
import logging

from . import dispatcher

class Plugin(object):

    from . import events

    logger = logging.getLogger('ircbot.plugins')

    def __init__(self, params):
        self.nickname = params["nickname"]

