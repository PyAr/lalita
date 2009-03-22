
from twisted.trial.unittest import TestCase as TwistedTestCase
from twisted.internet import defer

from core import events
from core import dispatcher

class TestRegister(TwistedTestCase):

#   * register ('event_<>', callback)
#              ('event_command', callback, [c])
#              ('privmsg', callback, [regex])
#
    def setUp(self):
        self.d = defer.Deferred()
        self.disp = dispatcher.Dispatcher()
        self.timeout = 1

    def deferredAssertEqual(self, deferred, a, b):
        def f(_):
            self.assertEqual(a, b)
        deferred.addCallback(f)

    def test_event(self):
        '''Test registration to events.'''
        self.assertTrue(hasattr(self.disp, "register"))

        def f(args):
            self.deferredAssertEqual(self.d, args, ("esperado",))
            self.d.callback(True)
            return ""

        self.disp.register(events.CONNECTION_MADE, f)
        self.disp.push(events.CONNECTION_MADE, "eserado")
        return self.d


