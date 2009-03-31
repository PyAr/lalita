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
    url_re= re.compile ('((https?|ftp)://[^ ]*)')
    title_re= re.compile ('< *title *>([^<]+)< */ *title *>')
    encoding_re= re.compile ('<meta http-equiv="Content-Type" content="([^"]+)">')

    def __init__ (self, config, events, params):
        register= params['register']
        register (events.PUBLIC_MESSAGE, self.message)
        self.config= dict (block_size=4096).update (config)
        self.titleFound= False
        self.magic= magic.open (magic.MAGIC_MIME)
        self.magic.load ()

    def message (self, user, channel, message):
        g= self.url_re.search (message)
        if g is not None:
            url= g.groups()[0]
            logger.debug ('fetching %s' % url)
            promise= client.getPage (str (url))
            promise.addCallback (self.guessFile, user, channel, url)
            # downloader= client._makeGetterFactory (url.encode ('ascii'),
            #     client.HTTPClientFactory)
            # promise= downloader.deferred
            # promise.addCallback (self.guessFile, downloader, user, channel, url)
            promise.addErrback (self.failed, user, channel, url)
            return promise

    def guessFile (self, page, user, channel, url):
    # def guessFile (self, page, downloader, user, channel, url):
        # logger.debug (u"[%s] %s" % (type (page), page[:1024].decode ('utf-8')))
        mimetype_enc= self.magic.buffer (page)
        try:
            # text/html; charset=utf-8
            mimetype, encoding= mimetype_enc.split (';')
            encoding= encoding.split ('=')[1]
        except ValueError:
            logger.debug ("no encoding %s" % mimetype_enc)
            mimetype= mimetype_enc
            encoding= None

        if mimetype=='text/html':
            g= self.title_re.search (page)
            if g is not None:
                self.titleFound= True
                title= g.groups ()[0]

                if encoding=='' or encoding is None:
                    # guess the encoding from the page itself
                    g= self.encoding_re.search (page)
                    if g is not None:
                        mimetype_enc= g.groups ()[0]
                        try:
                            mimetype, encoding= mimetype_enc.split (';')
                            encoding= encoding.split ('=')[1]
                        except ValueError:
                            logger.debug ("no encoding, again %s" % mimetype_enc)
                            mimetype= mimetype_enc
                            # good as any
                            encoding= 'utf-8'
                    else:
                        # user an encoding guesser
                        logger.debug ('still no encoding!')
                        # good as any
                        encoding= 'utf-8'

                # convert entities
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
