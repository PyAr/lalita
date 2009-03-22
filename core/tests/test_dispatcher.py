
from twisted.trial.unittest import TestCase as TwistedTestCase
from twisted.internet import defer

from core import events
from core import dispatcher

class EasyDeferredTests(TwistedTestCase):
    def setUp(self):
        self.deferred = defer.Deferred()
        self.timeout = 1

    def deferredAssertEqual(self, deferred, a, b):
        def f(_):
            self.assertEqual(a, b)
            return _
        deferred.addCallback(f)


class TestRegister(unittest.TestCase):

#   * register ('event_<>', callback)
#              ('event_command', callback, [c])
#              ('privmsg', callback, [regex])
#
    def setUp(self):
        super(TestRegister, self).setUp()
        self.disp = dispatcher.Dispatcher()

    def test_method_exists(self):
        self.assertTrue(hasattr(self.disp, "register"))

    def test_empty(self):
        '''Test no registration.'''
        self.assertEqual(self.disp._callbacks, {})
        return self.deferred

    def test_one_event(self):
        '''Test registration to events.'''
        def f(): pass

        self.disp.register(events.CONNECTION_MADE, f)
        self.assertEqual(self.disp._callbacks, {events.CONNECTION_MADE: [f]})
        return self.deferred

    def test_one_event_twice(self):
        '''Test two registrations to the same events.'''
        def f(): pass
        def g(): pass

        self.disp.register(events.CONNECTION_MADE, f)
        self.disp.register(events.CONNECTION_MADE, g)
        self.assertEqual(self.disp._callbacks,
                                            {events.CONNECTION_MADE: [f, g]})
        return self.deferred

    def test_mixed(self):
        '''Test several registration, several events.'''
        def f(): pass
        def g(): pass
        def h(): pass

        self.disp.register(events.CONNECTION_MADE, f)
        self.disp.register(events.CONNECTION_LOST, g)
        self.disp.register(events.CONNECTION_MADE, h)
        self.assertEqual(self.disp._callbacks, {events.CONNECTION_MADE: [f, h],
                                                events.CONNECTION_LOST: [g]})
        return self.deferred


class TestPush(EasyDeferredTests):

#   * register ('event_<>', callback)
#              ('event_command', callback, [c])
#              ('privmsg', callback, [regex])
#
    def setUp(self):
        super(TestRegister, self).setUp()
        self.disp = dispatcher.Dispatcher()

    def test_event(self):
        '''Test pushing events.'''
        self.assertTrue(hasattr(self.disp, "register"))

        def f(args):
            self.deferredAssertEqual(self.d, args, ("esperado",))
            self.deferred.callback(True)
            return ""

        self.disp.register(events.CONNECTION_MADE, f)
        self.disp.push(events.CONNECTION_MADE, "esperado")
        self.deferred.addCallback(lambda r: self.assertEqual(r, 100))
        return self.deferred


