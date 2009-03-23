from twisted.internet import defer

from core import events

map_events = {
    events.PRIVATE_MESSAGE: "private_message",
    events.TALKED_TO_ME: "talked_to_me",
    events.PUBLIC_MESSAGE: "public_message",
    events.COMMAND: "command",
}

class Dispatcher(object):
    def __init__(self):
        self._callbacks = {}

    def register(self, event, func, extra=None):
        '''Register one function to an event.

        The extra method is usefuld according to the event.  For some
        it should be a regexp telling if the message is useful, for
        command is a list of which commands, etc.
        '''
        self._callbacks.setdefault(event, []).append((func, extra))

    def _callback_done(self, msg):
        print "MSG", msg

    def _callback_error(self, error):
        print "ERROR:", error

    def push(self, event, *args):
        '''Pushes the received event to the registered method(s).'''
        all_registered = self._callbacks.get(event)
        print all_registered
        if all_registered is None:
            # nothing registered for this event
            return

        for regist, extra in all_registered:
            if event in map_events:
                meth = getattr(self, "handle_" + map_events[event])
                if extra is None or meth(extra, *args):
                    d = defer.maybeDeferred(regist, *args)
                    d.addCallbacks(self._callback_done, self._callback_error)
            else:
                d = defer.maybeDeferred(regist, *args)
                d.addCallbacks(self._callback_done, self._callback_error)

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


dispatcher = Dispatcher()
