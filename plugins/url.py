# -*- coding: utf8 -*-

import re
from twisted.web import client
from twisted.internet import defer
from BeautifulSoup import BeautifulStoneSoup, HTMLParser

import logging
logger = logging.getLogger ('ircbot.url')
logger.setLevel (logging.DEBUG)

from core import dispatcher
from core import events

class _HTMLParser (HTMLParser):
    def __init__ (self, deferred):
        HTMLParser.__init__ (self)
        self.foundTitleTag= False
        self.deferred= deferred
        self.title= u''

    def handle_starttag (self, tag, *args):
        if tag=='title':
            self.foundTitleTag= True
        else:
            self.foundTitleTag= False

    def handle_data (self, data, *args):
        if self.foundTitleTag:
            # TODO: set the correct encoding
            self.title+= unicode (data, 'iso-8859-1')

    def handle_entityref (self, ref, *args):
        if self.foundTitleTag:
            # TODO: set the correct encoding
            self.title+= unicode ("&%s;" % ref, 'iso-8859-1')

    def handle_charref (self, ref, *args):
        if self.foundTitleTag:
            # TODO: set the correct encoding
            self.title+= unicode ("&#%s;" % ref, 'iso-8859-1')


    def handle_endtag (self, tag, *args):
        if tag=='title':
            title= BeautifulStoneSoup (self.title,
                convertEntities=BeautifulStoneSoup.XHTML_ENTITIES).contents[0]
            logger.debug ('found title: %s' % title)
            self.deferred.callback (title.strip ())

class Url (object):
    re= re.compile ('((https?|ftp)://[^ ]*)')

    def __init__ (self, config, params):
        register= params['register']
        register (events.PUBLIC_MESSAGE, self.message)
        self.config= dict (block_size=4096).update (config)

    def message (self, user, channel, message):
        g= self.re.search (message)
        if g is not None:
            url= g.groups()[0]
            print 'fetching %s' % url
            promise= client.getPage (str (url))
            promise.addCallback (self.parsePage, channel, url)
            return promise

    def parsePage (self, page, channel, url):
        promise= defer.Deferred ()
        parse= _HTMLParser (promise, )
        parse.feed (page)
        promise.addCallback (self.answer, channel, url)
        return promise #?

    def answer (self, title, channel, url):
        return (channel, title)

# end
