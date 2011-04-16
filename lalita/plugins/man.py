# -*- coding: utf-8 -*-
from twisted.web import client
from lalita import Plugin


class Man(Plugin):
    """Respond with the link to the docs of the module."""
    def init(self, config):
        self.register(self.events.COMMAND, self.respond, ['man', 'man3'])

    def respond(self, user, channel, command, *args):
        """Answer with the link to the module."""
        modules = _parse_modules(args)
        self._look_up_docs(command, channel, modules)

    def _look_up_docs(self, command, channel, modules):
        """Look for the docs in docs.python.org.

        If found, say the link, else say it couldn't be found.
        """
        if command == 'man3':
            url_template = u"http://docs.python.org/py3k/library/%s.html"
        else:
            url_template = u"http://docs.python.org/library/%s.html"

        for module in modules:
            manurl = url_template % (module,)

            def success(page, module, manurl):
                """Say where are the docs."""
                msg = u"The documentation for %s is here: %s"
                self.say(channel, msg, module, manurl)

            def error(failure, module):
                """There are no docs."""
                msg = u"I don't know where the docs for %s are"
                self.say(channel, msg, module)

            d = client.getPage(str(manurl))
            d.addCallbacks(success,
                           error,
                           callbackArgs=(module, manurl,),
                           errbackArgs=(module,))


def _parse_modules(args):
    """ Parse modules names in args

    Examples:
    (u'urllib', u'socket',) -> [u'urllib', u'socket']
    (u'urllib,socket',) -> [u'urllib', u'socket']

    """
    modules = []
    for arg in args:
        for dirty in arg.split(','):
            modules.append(dirty.strip(', '))
    return modules
