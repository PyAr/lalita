# -*- coding: utf8 -*-

# (c) 2009 Marcos Dione <mdione@grulic.org.ar>

import re
from twisted.web import client
from twisted.internet import defer
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
import mimetypes

import logging
logger = logging.getLogger ('ircbot.plugins.url')
logger.setLevel (logging.DEBUG)

class Url (object):
    url_re= re.compile ('((https?|ftp)://[^ ]*)')
    title_re= re.compile ('< *title *>([^<]+)< */ *title *>')

    def __init__ (self, config, events, params):
        register= params['register']
        register (events.PUBLIC_MESSAGE, self.message)
        self.config= dict (block_size=4096).update (config)
        self.titleFound= False

    def message (self, user, channel, message):
        g= self.url_re.search (message)
        if g is not None:
            url= g.groups()[0]
            mimetype, encoding= mimetypes.guess_type (url)
            if mimetype not in (None, 'text/html'):
                return [(channel, "%s: %s" % (user, mimetype))]
            else:
                logger.debug ('fetching %s' % url)
                promise= client.getPage (str (url))
                promise.addCallback (self.parsePage, user, channel, url)
                promise.addErrback (self.failed, user, channel, url)
                return promise

    def parsePage (self, page, user, channel, url):
        g= self.title_re.search (page)
        if g is not None:
            self.titleFound= True
            title= BeautifulStoneSoup (g.groups ()[0],
                convertEntities=BeautifulStoneSoup.XHTML_ENTITIES).contents[0]
            return [(channel, u"%s: %s" % (user, title))]
        else:
            return [(channel, u"%s: no tiene titulo?!?" % (user, ))]

    def answer (self, title, user, channel, url):
        # why this is return sarasa and not promise.callback (sarasa)?
        self.titleFound= True
        return [(channel, u"%s: %s" % (user, title))]

    def failed (self, bongs, user, channel, url):
        logger.debug (bongs)
        return [(channel, u"%s: error con la página: %s" % (user, bongs.value))]

# end
