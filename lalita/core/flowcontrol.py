# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

import collections
import logging

from twisted.internet import reactor

logger = logging.getLogger ('ircbot.core.flowcontroller')

class FlowController(object):
    '''Queue that gets in the middle to control flow and avoid excess.

    It let pass "maxq" messages per user ("who" or "to").  The excess is
    queued.  The queued messages can be retrieved, or reset the queue to
    zero for that user.

    The queue also times out (per user).
    '''

    def __init__(self, func, maxq, timeout=None):
        self._queue = {}

        if not callable(func):
            raise TypeError("The func must be callable, received: %r" % func)
        self.func = func

        self.maxq = int(maxq)
        if self.maxq <= 0:
            raise ValueError("The maxq should be > 0, received: %r" % maxq)

        if timeout is None:
            self.timeout = None
        else:
            self.timeout = float(timeout)
            if self.timeout <= 0:
                raise ValueError("The timeout if present should be > 0, "
                                 "received: %r" % timeout)

    def send(self, to, what):
        '''Call "func" the first "maxq" times, the rest is queued.'''
        if to in self._queue:
            cant, queue, dcall = self._queue[to]
            if dcall is not None:
                dcall.reset(self.timeout)
        else:
            cant = 0
            queue = collections.deque()
            if self.timeout is None:
                dcall = None
            else:
                dcall = reactor.callLater(self.timeout, self.reset, to)

        if cant < self.maxq:
            self.func(to, what)
            cant += 1
            self._queue[to] = (cant, queue, dcall)
        else:
            logger.debug("Queuing msg to %r", to)
            queue.append(what)
            self._queue[to] = (cant, queue, dcall)

    def more(self, who):
        '''Call "func" the "maxq" times with what is queued for "who".'''
        if who not in self._queue:
            return False

        logger.debug("Unqueuing msgs from %r", who)
        cant, queue, dcall = self._queue[who]
        if dcall is not None:
            dcall.reset(self.timeout)
        if not queue:
            return False

        for i in xrange(self.maxq):
            try:
                what = queue.popleft()
            except IndexError:
                # queue is done!
                del self._queue[who]
                break
            self.func(who, what)
        return True

    def reset(self, who):
        '''Reset the queue for "who".'''
        if who in self._queue:
            logger.debug("Resetting queue of %r", who)
            del self._queue[who]

    def shutdown(self):
        '''Takes the flow controller down.'''
        for dcall in reactor.getDelayedCalls():
            dcall.cancel()
