# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

import unittest

from twisted.trial.unittest import TestCase as TwistedTestCase
from twisted.internet import defer, reactor

from lalita.core import flowcontrol


class TestBaseFC(unittest.TestCase):
    '''Base class.'''
    def setUp(self, timeout=None):
        self.rec = []
        def f(a, b):
            self.rec.append((a, b))
        self.fc = flowcontrol.FlowController(f, 3, timeout)

    def get_queue(self, who):
        '''Returns the queue for who.'''
        if who in self.fc._queue:
            return list(self.fc._queue[who][1])
        else:
            return list()


class TestInit(unittest.TestCase):
    '''Instancing the class.'''

    def test_base(self):
        '''Instanced with right params quantity.'''
        self.assertRaises(TypeError, flowcontrol.FlowController)
        self.assertRaises(TypeError, flowcontrol.FlowController, 1)
        self.assertRaises(TypeError, flowcontrol.FlowController, 1, timeout=1)
        self.assertRaises(TypeError, flowcontrol.FlowController, 1, 2, 3, 4)
        flowcontrol.FlowController(lambda: None, 1)
        flowcontrol.FlowController(lambda: None, 1, 1)

    def test_func(self):
        '''"func" parameter must be callable.'''
        self.assertRaises(TypeError, flowcontrol.FlowController, 1, 2)
        self.assertRaises(TypeError, flowcontrol.FlowController, None, 2)
        flowcontrol.FlowController(lambda: None, 1)

    def test_maxq(self):
        '''"maxq" parameter must be a number >0.'''
        f = lambda: None
        self.assertRaises(ValueError, flowcontrol.FlowController, f, "a")
        self.assertRaises(ValueError, flowcontrol.FlowController, f, 0)
        self.assertRaises(ValueError, flowcontrol.FlowController, f, -5)
        flowcontrol.FlowController(f, 1)

    def test_timeout(self):
        '''"timeout" parameter must be a number >0 or None.'''
        f = lambda: None
        self.assertRaises(ValueError, flowcontrol.FlowController, f, 1, "a")
        self.assertRaises(ValueError, flowcontrol.FlowController, f, 1, 0)
        self.assertRaises(ValueError, flowcontrol.FlowController, f, 1, -5)
        self.assertRaises(ValueError, flowcontrol.FlowController, f, 1, '-5')
        flowcontrol.FlowController(f, 1, None)
        flowcontrol.FlowController(f, 1, 1)


class TestSend(TestBaseFC):
    '''Using the .send() method.'''

    def test_base(self):
        '''Called with right params quantity.'''
        self.assertRaises(TypeError, self.fc.send)
        self.assertRaises(TypeError, self.fc.send, 1)
        self.assertRaises(TypeError, self.fc.send, 1, 2, 3)

    def test_called_once(self):
        '''With one call, the function is called.'''
        self.fc.send("foo", 5)
        self.assertEqual(self.rec, [("foo", 5)])

    def test_called_maxq_less1(self):
        '''With one less than maxq calls, the function is called.'''
        self.fc.send("foo", 5)
        self.fc.send("bar", 5)
        self.assertEqual(self.rec, [("foo", 5), ("bar", 5)])

    def test_called_maxq(self):
        '''With exact maxq calls, the function is called.'''
        self.fc.send("foo", 5)
        self.fc.send("bar", 5)
        self.fc.send("baz", 5)
        self.assertEqual(self.rec, [("foo", 5), ("bar", 5), ("baz", 5)])

    def test_called_maxq_plus1(self):
        '''With one plus than maxq calls, function is called, and queue!.'''
        self.fc.send(5, "foo")
        self.fc.send(5, "bar")
        self.fc.send(5, "baz")
        self.fc.send(5, "nop")
        self.assertEqual(self.rec, [(5, "foo"), (5, "bar"), (5, "baz")])
        self.assertEqual(self.get_queue(5), ["nop"])

    def test_called_order(self):
        '''Different 'to's, check order.'''
        for who, what in zip("ABAC", "1234"):
            self.fc.send(who, what)

        self.assertEqual(self.rec, [("A", "1"), ("B", "2"),
                                    ("A", "3"), ("C", "4"),
                                   ])

    def test_called_a_lot_different_tos(self):
        '''A lot of calls, but different 'to's.'''
        # call 2 to A, 5 to B, 1 to C
        for who, what in zip("ABABBCBB", "12345678"):
            self.fc.send(who, what)

        # A and C are called all the times, no queue
        self.assertTrue(("A", "1") in self.rec)
        self.assertTrue(("A", "3") in self.rec)
        self.assertTrue(("C", "6") in self.rec)
        self.assertEqual(self.get_queue("A"), [])
        self.assertEqual(self.get_queue("C"), [])

        # B is called maxq, and the rest is queued
        self.assertTrue(("B", "2") in self.rec)
        self.assertTrue(("B", "4") in self.rec)
        self.assertTrue(("B", "5") in self.rec)
        self.assertTrue(("B", "7") not in self.rec)
        self.assertTrue(("B", "8") not in self.rec)
        self.assertEqual(self.get_queue("B"), ["7", "8"])

    def test_reset_middle(self):
        '''With a reset in the middle it starts again.'''
        self.fc.send("foo", 5)
        self.fc.send("bar", 5)
        self.fc.reset(5)
        self.fc.send("xxx", 5)
        self.fc.send("yyy", 5)
        self.assertEqual(self.get_queue(5), [])


class TestMore(TestBaseFC):
    '''Using the .more() method.'''

    def test_base(self):
        '''Called with right params quantity.'''
        self.assertRaises(TypeError, self.fc.more)
        self.assertRaises(TypeError, self.fc.more, 1, 2)
        self.fc.more(1)

    def test_virgin_queue(self):
        '''Never used queue, don't produce anything.'''
        r = self.fc.more(1)
        self.assertEqual(self.rec, [])
        self.assertFalse(r)

    def test_nothing_queued(self):
        '''Nothing queued, don't produce anything.'''
        self.fc.send("pepe", 1)
        self.rec[:] = []
        r = self.fc.more("pepe")
        self.assertEqual(self.rec, [])
        self.assertFalse(r)

    def test_something_queued(self):
        '''Something queued, produce it.'''
        for what in "12345":
            self.fc.send("pepe", what)
        self.rec[:] = []

        r = self.fc.more("pepe")
        self.assertEqual(self.rec, [("pepe", "4"), ("pepe", "5")])
        self.assertTrue(r)

    def test_a_lot_queued(self):
        '''Lot of messages queued, produce until maxq.'''
        for what in "12345678":
            self.fc.send("foo", what)
        self.rec[:] = []

        # first call, go until maxq
        self.fc.more("foo")
        self.assertEqual(self.rec, [("foo", "4"), ("foo", "5"), ("foo", "6")])

        # second call, produce the rest
        self.fc.more("foo")
        self.assertEqual(self.rec, [("foo", "4"), ("foo", "5"), ("foo", "6"),
                                    ("foo", "7"), ("foo", "8"),
                                   ])
        self.assertFalse("foo" in self.fc._queue)

    def test_different_to(self):
        '''Queued for different users, produce the for asked one.'''
        for who, what in zip("AABBABBBA", "123456789"):
            self.fc.send(who, what)
        self.rec[:] = []

        # this should produce B and leave A intact
        self.fc.more("B")
        self.assertEqual(self.rec, [("B", "7"), ("B", "8")])
        self.assertEqual(self.get_queue("A"), ["9"])


class TestReset(TestBaseFC):
    '''Using the .reset() method.'''

    def test_base(self):
        '''Called with right params quantity.'''
        self.assertRaises(TypeError, self.fc.reset)
        self.assertRaises(TypeError, self.fc.reset, 1, 2)
        self.fc.reset(1)

    def test_nothing_queued(self):
        '''Nothing was queued.'''
        self.fc.reset(1)
        self.assertEqual(self.get_queue(1), [])

    def test_reset_queue(self):
        '''Something was queued, reset it.'''
        for what in "12345":
            self.fc.send("pepe", what)
        self.assertEqual(self.get_queue("pepe"), ["4", "5"])

        self.fc.reset("pepe")
        self.assertEqual(self.get_queue("pepe"), [])

    def test_different_queues(self):
        '''Queue existed for different users, reset the right one.'''
        for who, what in zip("AABBABBBA", "123456789"):
            self.fc.send(who, what)
        self.assertEqual(self.get_queue("A"), ["9"])
        self.assertEqual(self.get_queue("B"), ["7", "8"])

        self.fc.reset("A")
        self.assertEqual(self.get_queue("B"), ["7", "8"])


class TestTimeout(TwistedTestCase, TestBaseFC):
    '''Check the timeout functionality.'''
    timeout = 2

    def setUp(self):
        TestBaseFC.setUp(self, timeout=1)
        TwistedTestCase.setUp(self)

    def tearDown(self):
        self.fc.shutdown()

    def test_called_within_time(self):
        '''The queue is there before the timeout.'''
        d = defer.Deferred()

        for what in "12345":
            self.fc.send("pepe", what)

        def check():
            self.assertEqual(self.get_queue("pepe"), ["4", "5"])
            d.callback(True)

        reactor.callLater(.1, check)
        return d

    def test_called_after_time(self):
        '''After timeout, no more queue.'''
        d = defer.Deferred()

        for what in "12345":
            self.fc.send("pepe", what)

        def check():
            self.assertEqual(self.get_queue("pepe"), [])
            d.callback(True)

        reactor.callLater(1.5, check)
        return d

    def test_different_users(self):
        '''Timeout clears the queue per user.'''
        d = defer.Deferred()

        for what in "12345":
            self.fc.send("pepe", what)

        def add_more():
            for what in "54321":
                self.fc.send("juan", what)

        def check():
            self.assertEqual(self.get_queue("juan"), ["2", "1"])
            d.callback(True)

        reactor.callLater(1, add_more)
        reactor.callLater(1.5, check)
        return d

