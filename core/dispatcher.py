# -*- coding: utf8 -*-

import itertools
import functools

from twisted.internet import defer

import logging
logger = logging.getLogger ('ircbot.core.dispatcher')
logger.setLevel(logging.DEBUG)

from core import events

# messages longer than this will be splitted in different server commands
LENGTH_MSG = 128

# these are special events that should be handled by their methods to
# validate the message reception
MAP_EVENTS = {
    events.PRIVATE_MESSAGE: "private_message",
    events.TALKED_TO_ME: "talked_to_me",
    events.PUBLIC_MESSAGE: "public_message",
    events.COMMAND: "command",
}

# these events don't return any message
SILENTS = set((
    events.CONNECTION_MADE,
    events.CONNECTION_LOST,
    events.SIGNED_ON,
))

# these are the meta commands
META_COMMANDS = {
    "help": "meta_help",
    "list": "meta_list",
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
    events.JOIN: 0,
    events.PART: 0,
}


class Dispatcher(object):
    def __init__(self, ircclient):
        self._callbacks = {}
        self.bot = ircclient
        self._plugins = {}
        self._channel_filter = {}

    def new_plugin(self, plugin, channel):
        plugin.register = self.register
        plugin.say = functools.partial(self._msg_from_plugin, plugin)
        logger.debug('plugin %s is in channel %s', plugin, channel)
        self._plugins[plugin] = channel

    def register(self, event, func, extra=None):
        '''Register one function to an event.

        The extra method is usefuld according to the event.  For some
        it should be a regexp telling if the message is useful, for
        command is a list of which commands, etc.
        '''
        instance = func.im_self
        self._callbacks.setdefault(event, []).append((instance, func, extra))
        logger.debug('registering %s for event %s', func, event)
    def _msg_from_plugin(self, plugin, to_where, message):
        """Message from the plugin."""
        if plugin not in self._channel_filter:
            # don't allow to say anything out of order
            return

        from_channel = self._channel_filter[plugin]

        # from_channel can be None if msg() was used from here (not channel
        # passed), or if was a response from a plugin, but the original
        # message came from the server, outside a channel.
        if from_channel is not None and to_where.startswith("#"):
            # came from a channel, and it's going to a channel
            if from_channel != to_where:
                logger.debug("WARNING: the plugin is trying to answer in a "
                             "different channel! (from: %s  to: %s)",
                             from_channel, to_where)

        self.msg(to_where, message)

    def msg(self, to_where, message):
        self.bot.msg(to_where, message.encode("utf8"), LENGTH_MSG)

    def _error(self, error, instance):
        logger.debug("ERROR in instance %s: %s", instance, error)
        if instance in self._channel_filter:
            del self._channel_filter[instance]

    def _done(self, _, instance):
        logger.debug("Done! instance: %s", instance)
        if instance in self._channel_filter:
            del self._channel_filter[instance]

    def push(self, event, *args):
        '''Pushes the received event to the registered method(s).'''
        logger.debug("Received push event %s (%s)", event, args)
        # meta commands
        if event == events.COMMAND:
            user, channel, command = args[:3]
            if command in META_COMMANDS:
                meth = getattr(self, "handle_" + META_COMMANDS[command])
                meth(*args)
                return

            cmds = [x[2] for x in self._callbacks[events.COMMAND]]
            if command not in itertools.chain(*cmds):
                self.msg(channel, u"%s: No existe esa órden!" % user)
                return

        all_registered = self._callbacks.get(event)
        if all_registered is None:
            # nothing registered for this event
            return

        if CHANNEL_POS[event] is not None:
            channel= args[CHANNEL_POS[event]]
        else:
            channel= None

        for instance, regist, extra in all_registered:
            # see if the instances can listen in the channels
            allowed_channel = self._plugins[instance]
            if allowed_channel is not None:
                if channel is not None and channel != allowed_channel:
                    continue

            # check "extra" restrictions
            if event in MAP_EVENTS:
                meth = getattr(self, "handle_" + MAP_EVENTS[event])
                if extra is not None and not meth(extra, *args):
                    # have an extra, and the handle says "this is not for us"
                    continue

            # dispatch!
            if event not in SILENTS:
                self._channel_filter[instance] = channel

            logger.debug("Dispatching event to %s", regist)
            d = defer.maybeDeferred(regist, *args)
            d.addCallback(self._done, instance)
            d.addErrback(self._error, instance)

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
        '''Handles the HELP meta command.'''
        if not args:
            txt = u'"list" para ver las órdenes; "help cmd" para cada uno'
            self.msg(channel, txt)
            return

        # see if there's any command event
        try:
            registered = self._callbacks[events.COMMAND]
        except KeyError:
            self.msg(channel, u"No hay ninguna órden registrada...")
            return

        # get the docstrings
        docs = []
        for (inst, meth, cmds) in registered:
            if args[0] in cmds:
                docs.append(meth.__doc__)

        # no docs!
        if not docs:
            self.msg(channel, u"Esa órden no existe...")
            return

        # only one method for that command
        if len(docs) == 1:
            self.msg(channel, docs[0])
            return

        # several methods for the same command
        self.msg(channel, u"Hay varios métodos para esa órden:")
        for doc in docs:
            self.msg(channel, u" - " + doc)

    def handle_meta_list(self, user, channel, command, *args):
        '''Handles the LIST meta command.'''
        try:
            cmds = [x[2] for x in self._callbacks[events.COMMAND]]
        except KeyError:
            txt = u"Decí alpiste, no hay órdenes todavía..."
        else:
            onlys = set(itertools.chain(*cmds))
            txt = u"Las órdenes son: %s" % list(sorted(onlys))
        self.msg(channel, txt)
