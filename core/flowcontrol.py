# -*- coding: utf8 -*-

# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

class FlowController(object):
    '''Queue that gets in the middle to control flow and avoid excess.

    It let pass "maxq" messages per user ("who" or "to").  The excess is
    queued.  The queued messages can be retrieved, or reset the queue to
    zero for that user.

    The queue also times out (per user).
    '''

    def __init__(self, func, maxq, timeout=None):
        pass

    def send(self, what, to):
        '''Call "func" the first "maxq" times, the rest is queued.'''

    def more(self, who):
        '''Call "func" the "maxq" times with what is queued for "who".'''

    def reset(self, who):
        '''Reset the queue for "who".'''
