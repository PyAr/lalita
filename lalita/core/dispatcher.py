# -*- coding: utf8 -*-

# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

import itertools
import functools
import types

from twisted.internet import defer
from twisted.words.protocols.irc import numeric_to_symbolic

import logging
logger = logging.getLogger ('ircbot.core.dispatcher')

from . import events, flowcontrol

# messages longer than this will be splitted in different server commands
LENGTH_MSG = 512

# the default max used for the flow controller queue
DEFAULT_MAXQ = 5

# the timeout for the per process queue of the flow controller, in seconds
FLOW_TIMEOUT = 120

# these are special events that should be handled by their methods to
# validate the message reception
MAP_EVENTS = {
    events.PRIVATE_MESSAGE: "private_message",
    events.TALKED_TO_ME: "talked_to_me",
    events.PUBLIC_MESSAGE: "public_message",
    events.COMMAND: "command",
}

# these are the meta commands
META_COMMANDS = {
    "help": "meta_help",
    "list": "meta_list",
    "more": "meta_more",
}

# the position of the channel parameter in each event
CHANNEL_POS = {
    events.CONNECTION_MADE: None,
    events.CONNECTION_LOST: None,
    events.SIGNED_ON: None,
    events.JOINED: 0,
    events.PRIVATE_MESSAGE: None,
    events.TALKED_TO_ME: 1,
    events.COMMAND: 1,
    events.PUBLIC_MESSAGE: 1,
    events.ACTION: 1,
    events.JOIN: 1,
    events.LEFT: 1,
    events.QUIT: None,
    events.KICK: 1,
    events.RENAME: None,
}

# the position of the user parameter in each event
USER_POS = {
    events.CONNECTION_MADE: None,
    events.CONNECTION_LOST: None,
    events.SIGNED_ON: None,
    events.JOINED: None,
    events.PRIVATE_MESSAGE: 0,
    events.TALKED_TO_ME: 0,
    events.COMMAND: 0,
    events.PUBLIC_MESSAGE: 0,
    events.ACTION: 0,
    events.JOIN: 0,
    events.LEFT: 0,
    events.QUIT: 0,
    events.KICK: 0,
    events.RENAME: 0,
}


TRANSLATION_TABLE = {u"%s: No existe esa orden!":{'en': u"%s: No such command!"},
                     u'"list" para ver las órdenes; "help cmd" para cada uno':
                        {'en': u'"list" To see the available commands ; "help cmd" for specific command help'},
                     u"No hay ninguna orden registrada...":{'en': u"PANIC! I have no commands!!!"},
                     u"Esa orden no existe...":{'en': u"No such command..."},
                     u"%sNo tiene documentación, y yo no soy adivina...":{'en': u"%sMissing documentation"},
                     u"No tiene documentación, y yo no soy adivina...":{'en': u"Missing documentation"},
                     u"Hay varios métodos para esa orden:": {'en': u"Several handlers for the same command:"},
                     u"Decí alpiste, no hay órdenes todavía...": {'en': u"No commands available (yet)"},
                     u"Las órdenes son: %s": {'en': u"The available commands are: %s"},
                     u"No hay nada encolado para vos": {'en': u"Nothing queued for you"},
                    }


class ProxyBot(object):
    def __init__(self, plugin, bot):
        self.plugin = plugin
        self._bot = bot
        self.logger = logging.getLogger('ircbot.ProxyBot')

    def __getattr__(self, name):
        """Return a logging wrapper around ircbot."""

        def wrapper(*args, **kwargs):
            # log call attempt
            msg = "Plugin %s calling method %s on ircbot with args %s %s."
            self.logger.info(msg, self.plugin, name, args, kwargs)
            # proxy the call
            method = getattr(self._bot, name)
            return method(*args, **kwargs)

        return wrapper


class Dispatcher(object):
    def __init__(self, ircclient):
        self._callbacks = {}
        self.bot = ircclient
        self._plugins = {}
        self._to_whom = {}
        self._translations = {}
        self.register_translation(self, TRANSLATION_TABLE)

    def init(self, config):
        """Gets all the config at server level and init."""
        self.config = config
        self.length_msg = int(config.get('length_msg', LENGTH_MSG))
        maxq = int(config.get('flow_maxq', DEFAULT_MAXQ))
        self.flowcontroller = flowcontrol.FlowController(self._msg_unpacker,
                                                         maxq, FLOW_TIMEOUT)
        self.ircmaster = config.get('ircmaster')

    def shutdown(self):
        '''Takes the dispatcher down.'''
        self.flowcontroller.shutdown()

    def new_plugin(self, plugin, channel):
        plugin.register = self.register
        plugin.register_translation = self.register_translation
        plugin.add_irc_callback = self.add_irc_callback
        plugin.say = functools.partial(self._msg_from_plugin, plugin)
        plugin.bot = ProxyBot(plugin, self.bot)
        logger.debug('plugin %s is in channel %s', plugin, channel)
        self._plugins[plugin] = channel

    def register(self, event, func, extra=None):
        '''Register one function to an event.

        The extra method is usefuld according to the event.  For some
        it should be a regexp telling if the message is useful, for
        command is a list of which commands, etc.
        '''
        logger.debug('registering %s for event %s', func, event)
        instance = func.im_self
        self._callbacks.setdefault(event, []).append((instance, func, extra))

    def add_irc_callback(self, callback, func):
        '''Register a callback for an irc event.

        Callbacks are registered as irc_CALLBACK.
        '''
        callback = numeric_to_symbolic.get(callback, callback)
        setattr(self.bot, "irc_%s" % callback, func)

    def register_translation(self, instance, table):
        '''Register translation table for a plugin.'''
        logger.debug('registering translation table for %s', instance)
        self._translations[instance] = table

    def _msg_from_plugin(self, plugin, to_where, message, *args):
        """Message from the plugin."""
        user = self._to_whom.get(plugin)

        # translate it!
        message = self.get_translation(plugin, to_where, message, args)

        # send to the flow controller
        self.flowcontroller.send(user, (to_where, message))

    def _msg_unpacker(self, user, payload):
        '''Unpacks the payload.'''
        to_where, message = payload
        self._msg(to_where, message)

    def msg(self, to_where, message, *args):
        """Fills, and pushes to the bot."""
        message = self.get_translation(self, to_where, message, args)
        self._msg(to_where, message)

    def _msg(self, to, mess):
        """Really sends the message."""
        self.bot.msg(to, mess.encode("utf8"), self.length_msg)

    def get_translation(self, instance, channel, message, args):
        """Get the translated message for (instance, channel).

        If there is no language specified in the channel config, server config
        is used.  If there is no translation of message for the language,
        message is returned.
        """
        # channel might be an user if this is called from a privmsg handler
        channel_config = self.config.get('channels', {}).get(channel, {})
        lang = channel_config.get('language', self.config.get('language', None))
        trans =  self._translations.get(instance, {}).get(message, {}).get(lang, message)

        # fill it if have args
        if args:
            if len(args) == 1 and type(args[0]) == types.DictType:
                args = args[0]
            try:
                finalmsg = trans % args
            except TypeError, e:
                # log the error with all the info and raise the same exception
                logger.error('Unable to format message! Msg: %r   Args: %s',
                             trans, args)
                if self.ircmaster is not None:
                    m = 'Unable to format message! Msg: %r  Args: %s' % (trans, args)
                    self._msg(self.ircmaster, m)
                raise
        else:
            finalmsg = trans

        return finalmsg

    def _error(self, error, instance):
        logger.error("ERROR in instance %s: %s", instance, error)
        if self.ircmaster is not None:
            cls = instance.__class__
            m = "Error calling the plugin '%s.%s': %r" % (cls.__module__, cls.__name__, error.value)
            self._msg(self.ircmaster, m)

    def _done(self, _, instance):
        logger.debug("Done! instance: %s", instance)

    def push(self, event, *args):
        '''Pushes the received event to the registered method(s).'''
        logger.debug("Received push event %s (%s)", event, args)

        posuser = USER_POS[event]
        user = None if posuser is None else args[posuser]

        # meta commands
        if event == events.COMMAND:
            user, channel, command = args[:3]
            if command in META_COMMANDS:
                meth = getattr(self, "handle_" + META_COMMANDS[command])
                meth(*args)
                return

            # check if the command is one of those registered for the
            # plugins (the [None] is a special case when registering for
            # all of them)
            cmds = [x[2] for x in self._callbacks[events.COMMAND]]
            if cmds != [None] and command not in itertools.chain(*cmds):
                self.msg(channel, u"%s: No existe esa orden!", user)
                return

        # as it's not a meta command, the queue is reset for the user
        self.flowcontroller.reset(user)

        all_registered = self._callbacks.get(event)
        if all_registered is None:
            # nothing registered for this event
            return

        if CHANNEL_POS[event] is not None:
            channel= args[CHANNEL_POS[event]]
        else:
            channel= None

        # get all the useful plugins! to avoid duplicate calls, when there's
        # more than one instance that registered the same method for the
        # same event, just choose one
        useful = {}
        for instance, regist, extra in all_registered:
            allowed_channel = self._plugins[instance]
            # server messages go everywhere, or it's a channel message and
            # we're allowed
            if allowed_channel is None or channel is None or \
               channel == allowed_channel:
                useful[regist.im_func] = (instance, regist, extra)

        for instance, regist, extra in useful.values():
            # check "extra" restrictions
            if event in MAP_EVENTS:
                meth = getattr(self, "handle_" + MAP_EVENTS[event])
                if extra is not None and not meth(extra, *args):
                    # have an extra, and the handle says "this is not for us"
                    continue

            # dispatch!
            self._to_whom[instance] = user
            logger.debug("Dispatching event to %s", regist)
            d = defer.maybeDeferred(regist, *args)
            d.addCallback(self._done, instance)
            d.addErrback(self._error, instance)
            d.addBoth(lambda _: self._to_whom.pop(instance))

    def handle_private_message(self, extra, user, msg):
        '''The extra is a regexp that says if the msg is useful or not.'''
        return extra.match(msg)

    def handle_talked_to_me(self, extra, user, channel, msg):
        '''The extra is a regexp that says if the msg is useful or not.'''
        return extra.match(msg)

    def handle_public_message(self, extra, user, channel, msg):
        '''The extra is a regexp that says if the msg is useful or not.'''
        return extra.match(msg)

    def handle_command(self, extra, user, channel, command, *args):
        '''Let's see if the command is useful for this method.'''
        return command in extra

    def handle_meta_help(self, user, channel, command, *args):
        u"""Devuelve ayuda sobre una orden específica."""
        if not args:
            txt = u'"list" para ver las órdenes; "help cmd" para cada uno'
            self.msg(channel, txt)
            return

        # see if there's any command event
        try:
            registered = self._callbacks[events.COMMAND]
        except KeyError:
            self.msg(channel, u"No hay ninguna orden registrada...")
            return

        # get the docstrings... to get uniques we don't use a dictionary just
        # to keep the secuence ordered
        docs = []
        revised = set()
        for (inst, meth, cmds) in registered:
            chan = self._plugins[inst]
            if chan is not None and chan != channel:
                # if it's a channel plugin, it should be here
                continue

            if args[0] in cmds:
                modclsmeth = "%s.%s.%s" % (meth.__module__,
                                           meth.__class__.__name__,
                                           meth.im_func.func_name)
                if modclsmeth not in revised:
                    revised.add(modclsmeth)
                    docs.append(meth.__doc__)

        # check meta commands
        if args[0] in META_COMMANDS:
            meth = getattr(self, "handle_" + META_COMMANDS[args[0]])
            docs.append(meth.__doc__)

        # no docs!
        if not docs:
            self.msg(channel, u"Esa orden no existe...")
            return

        # only one method for that command
        nodoc = u"No tiene documentación, y yo no soy adivina..."
        if len(docs) == 1:
            t = docs[0] if docs[0] else nodoc
            self.msg(channel, t)
            return

        # several methods for the same command
        self.msg(channel, u"Hay varios métodos para esa orden:")
        for doc in docs:
            t = u"%s" + doc if doc else u"%s" + nodoc
            self.msg(channel, t, u" - ")

    def handle_meta_list(self, user, channel, command, *args):
        u"""Lista las órdenes disponibles."""
        try:
            all_cmds = []
            for (inst, meth, cmds) in self._callbacks[events.COMMAND]:
                chan = self._plugins[inst]
                if chan is not None and chan != channel:
                    # if it's a channel plugin, it should be here
                    continue
                all_cmds.append(cmds)
        except KeyError:
            onlys = []
        else:
            onlys = list(set(itertools.chain(*all_cmds)))
        cmds = onlys + META_COMMANDS.keys()
        self.msg(channel, u"Las órdenes son: %s", list(sorted(cmds)))

    def handle_meta_more(self, user, channel, command, *args):
        u"""Entrega respuestas encoladas para el usuario."""
        if not self.flowcontroller.more(user):
            self.msg(channel, u"No hay nada encolado para vos")

