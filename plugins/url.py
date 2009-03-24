# -*- coding: utf8 -*-

import re
from twisted.web import client
from twisted.internet import defer
import BeautifulSoup

from core import dispatcher
from core import events

class _HTMLParser (BeautifulSoup.HTMLParser):
    def __init__ (self, deferred):
        BeautifulSoup.HTMLParser.__init__ (self)
        self.foundTitleTag= False
        self.deferred= deferred
        self.title= u''

    def handle_starttag (self, tag, *args):
        if tag=='title':
            self.foundTitleTag= True
        else:
            self.foundTitleTag= False

    def handle_data (self, data, *args):
        # print data, args
        if self.foundTitleTag:
            print 'found title: %s' % data
            # TODO: set the correct encoding
            self.title+= unicode (data, 'iso-8859-1')

    def handle_endtag (self, tag, *args):
        if tag=='title':
            self.deferred.callback (self.title.strip ())

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
        # print u'got %s, parsing... [%s]' % (url, page[:4096])
        promise= defer.Deferred ()
        parse= _HTMLParser (promise, )
        parse.feed (page)
        promise.addCallback (self.answer, channel, url)
        return promise #?

    def answer (self, title, channel, url):
        return (channel, title)

# end
