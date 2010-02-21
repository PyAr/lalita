# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

import logging

from . import dispatcher

class _PluginLogger(object):
    '''Logging magic for plugins.'''

    def __init__(self, instance, log_level):
        klass = instance.__class__
        name = "%s.%s" % (klass.__module__, klass.__name__)
        self.logger = logging.getLogger('ircbot.plugins.%s' % name)
        if log_level is not None:
            self.logger.setLevel(log_level)

    def debug(self, *a, **k):
        self.logger.debug(*a, **k)

    def info(self, *a, **k):
        self.logger.info(*a, **k)

    def warning(self, *a, **k):
        self.logger.warning(*a, **k)

    def error(self, *a, **k):
        self.logger.error(*a, **k)

    def critical(self, *a, **k):
        self.logger.critical(*a, **k)


class Plugin(object):
    '''Inheritable class for plugins, which only need to subclass this.'''

    from . import events

    def __init__(self, params, log_level):
        self.nickname = params["nickname"]
        self.encoding = params['encoding']
        self.logger = _PluginLogger(self, log_level)
