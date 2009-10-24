# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

import unittest
from collections import deque

from twisted.trial.unittest import TestCase as TwistedTestCase
from twisted.internet import defer, reactor

from core import flowcontrol


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
        self.assertRaises(ValueError, flowcontrol.FlowController, f, None)
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
        flowcontrol.FlowController(f, 1, None)
        flowcontrol.FlowController(f, 1, 1)


class TestSend(unittest.TestCase):
    '''Using the .send() method.'''
    def setUp(self):
        self.rec = []
        self.fc = flowcontrol.FlowController(self.rec.append, 3)

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
        self.fc.send("foo", 5)
        self.fc.send("bar", 5)
        self.fc.send("baz", 5)
        self.fc.send("nop", 5)
        self.assertEqual(self.rec, [("foo", 5), ("bar", 5), ("baz", 5)])
        self.assertEqual(self.fc._queue, {5: deque("nop")})

    def test_called_order(self):
        '''Different 'to's, check order.'''
        for what, who in zip("1234", "ABAC"):
            self.fc.send(what, who)

        self.assertEqual(self.rec, [("1", "A"), ("2", "B"),
                                    ("3", "A"), ("4", "C"),
                                   ])

    def test_called_a_lot_different_tos(self):
        '''A lot of calls, but different 'to's.'''
        # call 2 to A, 5 to B, 1 to C
        for what, who in zip("12345678", "ABABBCBB"):
            self.fc.send(what, who)

        # A and C are called all the times, no queue
        self.assertTrue(("A", "1") in self.rec)
        self.assertTrue(("A", "3") in self.rec)
        self.assertTrue(("C", "6") in self.rec)
        self.assertFalse("A" in self.fc._queue)
        self.assertFalse("C" in self.fc._queue)

        # B is called maxq, and the rest is queued
        self.assertTrue(("B", "2") in self.rec)
        self.assertTrue(("B", "4") in self.rec)
        self.assertTrue(("B", "5") in self.rec)
        self.assertTrue(("B", "7") not in self.rec)
        self.assertTrue(("B", "8") not in self.rec)
        self.assertEqual(self.fc._queue["B"], deque([7, 8]))


class TestMore(unittest.TestCase):
    '''Using the .more() method.'''
    def setUp(self):
        self.rec = []
        self.fc = flowcontrol.FlowController(self.rec.append, 3)

    def test_base(self):
        '''Called with right params quantity.'''
        self.assertRaises(TypeError, self.fc.more)
        self.assertRaises(TypeError, self.fc.more, 1, 2)
        self.fc.more(1)

    def test_nothing_queued(self):
        '''Nothing queued, don't produce anything.'''
        self.fc.more(1)
        self.assertEqual(self.rec, [])

    def test_something_queued(self):
        '''Something queued, produce it.'''
        for what in zip("12345"):
            self.fc.send(what, "pepe")
        self.rec[:] = []

        self.fc.more("pepe")
        self.assertEqual(self.rec, [(4, "pepe"), (5, "pepe")])

    def test_a_lot_queued(self):
        '''Lot of messages queued, produce until maxq.'''
        for what in zip("12345678"):
            self.fc.send(what, "pepe")
        self.rec[:] = []

        # first call, go until maxq
        self.fc.more("pepe")
        self.assertEqual(self.rec, [(4, "pepe"), (5, "pepe"), (6, "pepe")])

        # second call, produce the rest
        self.fc.more("pepe")
        self.assertEqual(self.rec, [(4, "pepe"), (5, "pepe"), (6, "pepe"),
                                    (7, "pepe"), (8, "pepe"),
                                   ])

    def test_different_to(self):
        '''Queued for different users, produce the for asked one.'''
        for what, who in zip("123456789", "AABBABBBA"):
            self.fc.send(what, who)
        self.rec[:] = []

        # this should produce B and leave A intact
        self.fc.more("B")
        self.assertEqual(self.rec, [(7, "B"), (8, "B")])
        self.assertEqual(self.fc._queue["A"], deque([4]))


class TestReset(unittest.TestCase):
    '''Using the .reset() method.'''
    def setUp(self):
        self.fc = flowcontrol.FlowController(lambda: None, 3)

    def test_base(self):
        '''Called with right params quantity.'''
        self.assertRaises(TypeError, self.fc.reset)
        self.assertRaises(TypeError, self.fc.reset, 1, 2)
        self.fc.reset(1)

    def test_nothing_queued(self):
        '''Nothing was queued.'''
        self.fc.reset(1)
        self.assertEqual(self.fc._queue, {})

    def test_reset_queue(self):
        '''Something was queued, reset it.'''
        for what in zip("12345"):
            self.fc.send(what, "pepe")
        self.assertEqual(self.fc._queue, {"pepe": deque([4, 5])})

        self.reset("pepe")
        self.assertEqual(self.fc._queue, {})

    def test_different_queues(self):
        '''Queue existed for different users, reset the right one.'''
        for what, who in zip("123456789", "AABBABBBA"):
            self.fc.send(what, who)
        self.assertEqual(self.fc._queue, {"A": deque([4]), "B": deque([4, 5])})

        self.reset("A")
        self.assertEqual(self.fc._queue, {"B": deque([4, 5])})


class TestTimeout(TwistedTestCase):
    '''Check the timeout functionality.'''
    timeout = 2

    def setUp(self):
        self.rec = []
        self.fc = flowcontrol.FlowController(self.rec.append, 3, 1)

    def test_called_within_time(self):
        '''The queue is there before the timeout.'''
        d = defer.Deferred()

        for what in zip("12345"):
            self.fc.send(what, "pepe")

        def check():
            self.assertEqual(self.fc._queue, {"pepe": deque([4, 5])})
            d.callback(True)

        reactor.callLater(.1, check)
        return d

    def test_called_after_time(self):
        '''After timeout, no more queue.'''
        d = defer.Deferred()

        for what in zip("12345"):
            self.fc.send(what, "pepe")

        def check():
            self.assertEqual(self.fc._queue, {})
            d.callback(True)

        reactor.callLater(1.5, check)
        return d

    def test_different_users(self):
        '''Timeout clears the queue per user.'''
        d = defer.Deferred()

        for what in zip("12345"):
            self.fc.send(what, "pepe")

        def add_more():
            for what in zip("54321"):
                self.fc.send(what, "juan")

        def check():
            self.assertEqual(self.fc._queue, {"juan": deque([2, 1])})
            d.callback(True)

        reactor.callLater(1, add_more)
        reactor.callLater(1.5, check)
        return d

