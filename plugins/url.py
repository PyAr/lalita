# -*- coding: utf8 -*-

# (c) 2009 Marcos Dione <mdione@grulic.org.ar>

import re
from twisted.web import client
from twisted.internet import defer
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
# import mimetypes
import magic
# import pdb

import logging
logger = logging.getLogger ('ircbot.plugins.url')
logger.setLevel (logging.DEBUG)

class Url (object):
    url_re= re.compile ('((https?|ftp)://[^ ]*)', re.IGNORECASE|re.DOTALL)
    title_re= re.compile (
        '< *title *>([^<]+)< */ *title *>', re.IGNORECASE|re.DOTALL)
    content_type_re= re.compile (
        '<meta http-equiv="Content-Type" content="([^"]+)">',
        re.IGNORECASE|re.DOTALL)
    xhtml_re= re.compile ('<!DOCTYPE +html')
    mimetype_re= re.compile ('([a-z-/]+);?( charset=(.*))?')

    def __init__ (self, config, events, params):
        register= params['register']
        register (events.PUBLIC_MESSAGE, self.message)
        logger.debug (config)
        self.config= dict (block_size=4096)
        self.config.update (config)
        logger.debug (self.config)
        self.titleFound= False
        self.magic= magic.open (magic.MAGIC_MIME)
        self.magic.load ()

    def message (self, user, channel, message):
        g= self.url_re.search (message)
        if g is not None:
            url= g.groups()[0]
            logger.debug ('fetching %s' % url)
            promise= client.getPage (str (url))
            #, headers=dict (
                #Range="bytes=0-%d" % self.config['block_size'])
            #)
            #downloader= client._makeGetterFactory (url.encode ('ascii'),
                #client.HTTPClientFactory, headers=dict (
                    #Range="bytes=0-%d" % self.config['block_size']
                #))
            #downloader.handleStatus_206= .handleStatus_200
            #promise= downloader.deferred
            promise.addCallback (self.guessFile, user, channel, url)
            promise.addErrback (self.failed, user, channel, url)
            return promise

    def guessFile (self, page, user, channel, url):
        # logger.debug (u"[%s] %s" % (type (page), page.decode ('utf-8')))
        mimetype_enc= self.magic.buffer (page)
        logger.debug (mimetype_enc)
        # text/html; charset=utf-8
        g= self.mimetype_re.search (mimetype_enc)
        if g is not None:
            mimetype= g.groups ()[0]
            encoding= g.groups ()[2]
        else:
            logger.warn ("initial mimetype detection failed: %s" % mimetype_enc)

        # xhtml detection
        g= self.xhtml_re.search (page)
        # text/plain? yes, text/plain too...
        # see http://blog.nixternal.com/2009.03.30/where-is-ctrlaltbackspace/
        if (mimetype in ('text/html', 'text/plain') or
                mimetype in ('text/xml', 'application/xml') and g is not None):
            g= self.title_re.search (page)
            if g is not None:
                self.titleFound= True
                title= g.groups ()[0]

                if encoding is None:
                    # guess the encoding from the page itself
                    g= self.content_type_re.search (page)
                    if g is not None:
                        mimetype_enc= g.groups ()[0]
                        logger.debug (mimetype_enc)
                        # text/html; charset=utf-8
                        g= self.mimetype_re.search (mimetype_enc)
                        if g is not None:
                            mimetype= g.groups ()[0]
                            encoding= g.groups ()[2]
                        else:
                            logger.warn ("further mimetype detection failed: %s" % mimetype_enc)

                        # still no encoding?!?
                        if encoding is None:
                            logger.debug ("still no encoding: %s" % mimetype_enc)
                            # good as any
                            encoding= 'utf-8'
                    else:
                        # user an encoding guesser
                        logger.debug ('no mimetype in the page')
                        # good as any
                        encoding= 'utf-8'

                # convert xhtml entities
                title= BeautifulStoneSoup (title.decode (encoding),
                    convertEntities=BeautifulStoneSoup.XHTML_ENTITIES).contents[0]

                # this takes out the \n\r\t's
                titleParts= title.split ()
                title= ' '.join (titleParts)
                logger.debug (u"[%s] >%s< %s" % (type (title), title, encoding))

                return [(channel, u"%s: %s" % (user, title))]
            else:
                return [(channel, u"%s: no tiene titulo?!?" % (user, ))]
        else:
            return [(channel, u"%s: %s" % (user, mimetype))]

    def failed (self, bongs, user, channel, url):
        logger.debug (bongs)
        return [(channel, u"%s: error con la página: %s" % (user, bongs.value))]

# end
