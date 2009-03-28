
from . import dispatcher

class Plugin(object):

    from . import events

    def __init__(self, params):
        self.nickname = params["nickname"]

