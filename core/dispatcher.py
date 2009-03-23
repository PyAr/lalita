from twisted.internet import defer

from core import events

map_events_with_msg = {
    events.PRIVATE_MESSAGE: "private_message",
    events.TALKED_TO_ME: "talked_to_me",
    events.PUBLIC_MESSAGE: "public_message",
}

class Dispatcher(object):
    def __init__(self):
        self._callbacks = {}

    def register(self, event, func, regexp=None):
        self._callbacks.setdefault(event, []).append((func, regexp))

    def _callback_done(self, msg):
        print "MSG", msg

    def _callback_error(self, error):
        print "ERROR:", error

    def push(self, event, *args):
        all_registered = self._callbacks.get(event)
        if all_registered is None:
            # nothing registered for this event
            return

        for regist, regexp in all_registered:
            if event in map_events_with_msg:
                meth = getattr(self, "handle_" + map_events_with_msg[event])
                if regexp is None or meth(regexp, *args):
                    d = defer.maybeDeferred(regist, *args)
                    d.addCallbacks(self._callback_done, self._callback_error)
            else:
                d = defer.maybeDeferred(regist, *args)
                d.addCallbacks(self._callback_done, self._callback_error)

    def handle_private_message(self, regexp, user, msg):
        return regexp.match(msg)

    def handle_talked_to_me(self, regexp, user, channel, msg):
        return regexp.match(msg)

    def handle_public_message(self, regexp, user, channel, msg):
        return regexp.match(msg)


dispatcher = Dispatcher()
