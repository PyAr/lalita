# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

import unittest

from core import flowcontrol


class TestInit(unittest.TestCase):
    '''Instancing the class.'''

    def test_base(self):
        '''Instanced with right params quantity.'''

    def test_func(self):
        '''"func" parameter must be callable.'''

    def test_maxq(self):
        '''"maxq" parameter must be a number >0.'''

    def test_timeout(self):
        '''"timeout" parameter must be a number >0 or None.'''


class TestSend(unittest.TestCase):
    '''Using the .send() method.'''
    def setUp(self):
        self.rec = []
        self.fc = flowcontrol.FlowController(self.rec.append, 3)

    def test_base(self):
        '''Called with right params quantity.'''

    def test_called_once(self):
        '''With one call, the function is called.'''

    def test_called_maxq_less1(self):
        '''With one less than maxq calls, the function is called.'''

    def test_called_maxq(self):
        '''With exact maxq calls, the function is called.'''

    def test_called_maxq_plus1(self):
        '''With one plus than maxq calls, function is called, and queue!.'''

    def test_called_a_lot_different_tos(self):
        '''A lot of calls, but different 'to's.'''
        # call 2 to A, 5 to B, 1 to C

        # A and C are called all the times, no queue

        # B is called maxq, and the rest is queued


class TestMore(unittest.TestCase):
    '''Using the .more() method.'''
    def setUp(self):
        self.rec = []
        self.fc = flowcontrol.FlowController(self.rec.append, 3)

    def test_base(self):
        '''Called with right params quantity.'''

    def test_nothing_queued(self):
        '''Nothing queued, don't produce anything.'''

    def test_something_queued(self):
        '''Something queued, produce it.'''

    def test_a_lot_queued(self):
        '''Lot of messages queued, produce until maxq.'''

        # first call, go until maxq

        # second call, produce the rest

    def test_different_to(self):
        '''Queued for different users, produce the for asked one.'''


class TestReset(unittest.TestCase):
    '''Using the .reset() method.'''
    def setUp(self):
        self.rec = []
        self.fc = flowcontrol.FlowController(self.rec.append, 3)

    def test_base(self):
        '''Called with right params quantity.'''

    def test_nothing_queued(self):
        '''Nothing was queued.'''

    def test_reset_queue(self):
        '''Something was queued, reset it.'''

    def test_different_queues(self):
        '''Queue existed for different users, reset the right one.'''


class TestTimeout(unittest.TestCase):
    '''Check the timeout functionality.'''
    def setUp(self):
        self.rec = []
        self.fc = flowcontrol.FlowController(self.rec.append, 3, 1)

    def test_called_within_time(self):
        '''The queue is there before the timeout.'''

    def test_called_after_time(self):
        '''After timeout, no more queue.'''

    def test_different_users(self):
        '''Timeout clears the queue per user.'''



