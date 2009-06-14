# -*- coding: utf8 -*-

# (c) 2009 Marcos Dione <mdione@grulic.org.ar>

import re
from twisted.web import client
from twisted.internet import defer

from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup

import magic
import chardet

import sqlite3
import datetime

from lalita import Plugin

class Url (Plugin):
    url_re= re.compile ('((https?|ftp)://[^ ]+)', re.IGNORECASE|re.DOTALL)
    title_re= re.compile (
        '< *title *>([^<]+)< */ *title *>', re.IGNORECASE|re.DOTALL)
    content_type_re= re.compile (
        '<meta http-equiv="Content-Type" content="([^"]+)">',
        re.IGNORECASE|re.DOTALL)
    xhtml_re= re.compile ('<!DOCTYPE +html')
    mimetype_re= re.compile ('([a-z-/]+);?( charset=(.*))?')

    def init(self, config):
        self.register (self.events.PUBLIC_MESSAGE, self.message)
        self.config= dict (
            block_size=4096,
            in_format=u'%(poster)s: [#%(id)d] %(title)s',
            found_format=u'[#%(id)d] %(url)s: %(title)s [by %(poster)s, %(date)s, %(time)s]',
            guess_encoding=0.0,
            )
        self.config.update (config)
        self.logger.debug (self.config)
        self.titleFound= False
        self.magic= magic.open (magic.MAGIC_MIME)
        self.magic.load ()

        self.register(self.events.COMMAND, self.dig, ['dig'])
        self.register(self.events.COMMAND, self.delete, ['del'])

        self.initDb ()

    def initDb (self):
        # sqlite stuff
        db= 'db/'+self.config.get ('database', 'url.db')
        self.logger.debug ('connecting to '+db)
        self.conn= sqlite3.connect (db)
        self.cursor= self.conn.cursor ()

        self.cursor.execute ('''create table if not exists url (
            id integer primary key autoincrement,
            url text,
            date text,
            time text,
            poster text,
            title text)''')
        self.cursor.execute ('''create index if not exists url_idx on url (url)''')

    def addUrl (self, channel, poster, url, title='<no title>', mimetype=None):
        now= datetime.datetime.now ()
        date= str (now.date ())
        # '16:15:50.417804'
        time= str (now.time ()).split ('.')[0]

        data= [url, date, time, poster, title]
        self.logger.debug ('inserting data '+str (data))
        self.cursor.execute ('''insert into url
            (url, date, time, poster, title)
            values (?, ?, ?, ?, ?)
            ''', data)
        self.conn.commit ()

        # hate to fetch the id this way
        self.cursor.execute ('''select * from url where url = ? ''', (url, ))
        # 'tuple' object does not support item assignment
        result= list (self.cursor.fetchone ())

        if mimetype is not None:
            result[5]= mimetype
        self.logger.debug (result)
        data= dict (zip (('id', 'url', 'date', 'time', 'poster', 'title'), result))
        self.say(channel, (self.config['in_format'] % data))

    def dig (self, user, channel, command, *what):
        self.logger.debug (u'looking for %s' % what)
        self.cursor.execute ('''select * from url
            where title like '%%%s%%' or url like '%%%s%%' ''' % (what[0], what[0]))
        # self.cursor.execute (u"""select * from url where url like '%%%s%%'""" % (what[0], ))
        # self.cursor.execute ('''select * from url''')
        results= self.cursor.fetchall ()
        self.logger.debug (results)
        if len (results)>0:
            for result in results:
                data= dict (zip (('id', 'url', 'date', 'time', 'poster', 'title'), result))
                self.logger.debug (u'found %s' % data['url'])
                self.say (channel, self.config['found_format'] % data)
        else:
            self.say (channel, '%s: 404 Search term not found: %s' % (user, what[0]))

    def delete (self, user, channel, command, *what):
        for uid in what:
            self.logger.debug (u'deleting %s' % uid)
            self.cursor.execute ('''delete from url
                where id = ?''', (uid, ))
        self.conn.commit ()
        self.say (channel, "%s: deleted %s" % (user, ", ".join (
            [ "[#%s]" % uid for uid in what ]
        )))

    def message (self, user, channel, message):
        g= self.url_re.search (message)
        if g is not None:
            url= g.groups()[0]

            # see if we can find it in the db
            self.cursor.execute ('''select * from url where url = ? ''', (url, ))
            result= self.cursor.fetchone ()
            if result is not None:
                data= dict (zip (('id', 'url', 'date', 'time', 'poster', 'title'), result))
                self.say (channel, self.config['found_format'] % data)
            else:
                # go fetch it
                self.logger.debug ('fetching %s' % url)
                promise= client.getPage (str (url), headers=dict (
                    Range='bytes=0-%d' % self.config['block_size'])
                    )
                promise.addCallback (self.guessFile, user, channel, url)
                promise.addErrback (self.failed, user, channel, url)
                return promise

    # encoding detectors
    def pageContentType (self, page):
        encoding= None

        g= self.content_type_re.search (page)
        if g is not None:
            mimetype_enc= g.groups ()[0]
            self.logger.debug (mimetype_enc)
            # text/html; charset=utf-8
            g= self.mimetype_re.search (mimetype_enc)
            if g is not None:
                mimetype= g.groups ()[0]
                encoding= g.groups ()[2]
            else:
                self.logger.warn ("further mimetype detection failed: %s" % mimetype_enc)
        else:
            self.logger.warn ("no mimetype in the page")

        return encoding

    def guess (self, page):
        encoding= None
        detect= chardet.detect (page)

        if detect['confidence']>self.config['guess_encoding']:
            encoding= detect['encoding']
            self.logger.debug ("chardet says it's %s" % encoding)
        else:
            self.logger.debug ("chardet says it's %s, but with very low confidence: %f" % (encoding, confidence))

        return encoding

    def hardCoded (self, page):
        # good as any
        encoding= 'utf-8'

        return encoding

    def guessFile (self, page, user, channel, url):
        encodings= set ()

        mimetype_enc= self.magic.buffer (page)
        g= self.mimetype_re.search (mimetype_enc)
        if g is not None:
            mimetype= g.groups ()[0]
            encoding= g.groups ()[2]
        else:
            self.logger.warn ("initial mimetype detection failed: %s" % mimetype_enc)

        # xhtml detection
        g= self.xhtml_re.search (page)

        # text/plain? yes, text/plain too...
        # see http://blog.nixternal.com/2009.03.30/where-is-ctrlaltbackspace/
        # text/x-c should be some kind of xml,
        # but of course not everybody says the correct things
        # see http://www.cadena3.com.ar/contenido/2009/06/13/32131.asp
        if (mimetype in ('text/html', 'text/plain', 'text/x-c') or
                mimetype in ('text/xml', 'application/xml') and g is not None):

            g= self.title_re.search (page)
            if g is not None:
                self.titleFound= True
                title= g.groups ()[0]

                for method in (self.pageContentType, self.guess, self.hardCoded):
                    # returns an encoding and a dict to update the locals
                    # encoding, local= method (page)
                    # locals ().update (local)
                    encoding= method (page)
                    if encoding is not None:
                        encodings.add (encoding)

                for encoding in encodings:
                    try:
                        data= title.decode (encoding)
                    except UnicodeDecodeError:
                        self.logger.debug ("tried encoding %s but failed" % encoding)
                    else:
                        self.logger.debug ("suceeded with encoding %s" % encoding)
                        break

                # convert xhtml entities
                title= BeautifulStoneSoup (title,
                    convertEntities=BeautifulStoneSoup.XHTML_ENTITIES).contents[0]

                # this takes out the \n\r\t's
                titleParts= title.split ()
                title= ' '.join (titleParts)
                self.logger.debug (u"[%s] >%s< %s" % (type (title), title, encoding))

                self.addUrl (channel, user, url, title)
            else:
                self.addUrl (channel, user, url)
        else:
            self.addUrl (channel, user, url, mimetype=mimetype)

    def failed (self, failure, user, channel, url):
        self.logger.debug (failure)
        if str (failure.value).startswith ('206'):
            # this is not a failure, but a response to a '206 partial content'
            self.guessFile (failure.value.response, user, channel, url)
        else:
            self.say(channel, u"%s: error con la página: %s" % (user, failure.value))

# end
