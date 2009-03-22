
import unittest

from core import events
from core import dispatcher

class TestRegister(unittest.TestCase):

   * register ('event_<>', callback)
              ('event_command', callback, [c])
              ('privmsg', callback, [regex])

    def test_event(self):
        '''Test registration to events.'''
        self.assertTrue(hasattr(dispatcher, "register"))

        a = []
        def f():

            a.append(True)

        dispatcher.register(events.CONNECTION_MADE, f)
        dispatcher.push(events.CONNECTION_MADE)
        self.assertEqual(a, [True])

