# -*- coding: utf8 -*-

import itertools

from twisted.internet import defer

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


class Dispatcher(object):
    def __init__(self, ircclient):
        self._callbacks = {}
        self.bot = ircclient
        # FIXME: restringir i/o según canal

    def new_plugin (self, plugin, channel):
        pass

    def register(self, event, func, extra=None):
        '''Register one function to an event.

        The extra method is usefuld according to the event.  For some
        it should be a regexp telling if the message is useful, for
        command is a list of which commands, etc.
        '''
        instance= func.im_self
        self._callbacks.setdefault(event, []).append((func, extra))

    def msg(self, result):
        # support the plugin method returning nothing
        if result is None:
            return

        try:
            where, msg = result
        except ValueError:
            print "ERROR: The plugin must return (where, msg), got %r" % result
        self.bot.msg(where, msg.encode("utf8"), LENGTH_MSG)

    def _error(self, error):
        print "ERROR:", error

    def push(self, event, *args):
        '''Pushes the received event to the registered method(s).'''
        # meta commands
        if event == events.COMMAND:
            user, channel, command = args[:3]
            if command in META_COMMANDS:
                meth = getattr(self, "handle_" + META_COMMANDS[command])
                meth(*args)
                return

            cmds = [x[1] for x in self._callbacks[events.COMMAND]]
            if command not in itertools.chain(*cmds):
                self.msg((channel, u"%s: No existe esa órden!" % user))
                return

        # FIXME: hacer que lo que devuelven los plugins sean un lista de tuplas

        all_registered = self._callbacks.get(event)
        if all_registered is None:
            # nothing registered for this event
            return

        for regist, extra in all_registered:
            if event in MAP_EVENTS:
                meth = getattr(self, "handle_" + MAP_EVENTS[event])
                if extra is not None and not meth(extra, *args):
                    # have an extra, and the handle says "this is not for us"
                    continue

            # dispatch!
            d = defer.maybeDeferred(regist, *args)
            if event in SILENTS:
                d.addErrback(self._callback_error)
            else:
                d.addCallbacks(self.msg, self._error)

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
            self.msg((channel, txt))
            return

        # see if there's any command event
        try:
            registered = self._callbacks[events.COMMAND]
        except KeyError:
            self.msg((channel, u"No hay ninguna órden registrada..."))
            return

        # get the docstrings
        docs = []
        for (meth, cmds) in registered:
            print cmds
            if args[0] in cmds:
                docs.append(meth.__doc__)

        # no docs!
        if not docs:
            self.msg((channel, u"Esa órden no existe..."))
            return

        # only one method for that command
        if len(docs) == 1:
            self.msg((channel, docs[0]))
            return

        # several methods for the same command
        self.msg((channel, u"Hay varios métodos para esa órden:"))
        for doc in docs:
            self.msg((channel, u" - " + doc))

    def handle_meta_list(self, user, channel, command, *args):
        '''Handles the LIST meta command.'''
        try:
            cmds = [x[1] for x in self._callbacks[events.COMMAND]]
        except KeyError:
            txt = u"Decí alpiste, no hay órdenes todavía..."
        else:
            txt = u"Las órdenes son: %s" % list(itertools.chain(*cmds))
        self.msg((channel, txt))
