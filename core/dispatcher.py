from twisted.internet import defer

class Dispatcher(object):

    def register(self, event, func):
        self.registrado = func

    def _callback_done(self, msg):
        print msg

    def _callback_error(self, error):
        print error

    def push(self, event, *args):
        d = defer.maybeDeferred(self.registrado, *args)
        d.addCallbacks(self._callback_done, self._callback_error)

