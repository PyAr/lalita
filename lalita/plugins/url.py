# -*- coding: utf8 -*-

# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

import os
import re

from twisted.web import client
from twisted.internet import defer, reactor
from twisted.python import failure

from BeautifulSoup import BeautifulStoneSoup

import magic
import chardet

import sqlite3
import datetime

import random

from lalita import Plugin

class Url (Plugin):
    url_re= re.compile ('((https?|ftp)://[^ ]+)', re.IGNORECASE|re.DOTALL)
    title_re= re.compile (
        '< *title *>([^<]+)< */ *title *>', re.IGNORECASE|re.DOTALL)
    content_type_re = re.compile(
        '<meta http-equiv="Content-Type" content="([^"]+)" .*?>',
        re.IGNORECASE|re.DOTALL)
    xhtml_re= re.compile ('<!DOCTYPE +html')
    mimetype_re = re.compile('([a-z-/]+);?( *charset=(.*))?')

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

    ##### database handling #####
    def initDb (self):
        # sqlite stuff
        basedir = self.config.get('basedir', 'db')
        if not os.path.exists(basedir):
            os.mkdir(basedir)
        db = os.path.join(basedir, self.config.get('database', 'url.db'))
        self.logger.debug('connecting to %r', db)
        self.conn = sqlite3.connect(db)
        self.cursor = self.conn.cursor()

        self.cursor.execute ('''create table if not exists url (
            id integer primary key autoincrement,
            url text,
            date text,
            time text,
            poster text,
            title text)''')
        self.cursor.execute ('''create index if not exists url_idx on url (url)''')

    def addUrl (self, channel, poster, url, title='<no title>', mimetype=None, date=None, time=None):
        now= datetime.datetime.now ()
        if date is None:
            date= str (now.date ())
        if time is None:
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

    def dig(self, user, channel, command, *what):
        u'''Busca 'algo' en los títulos o URLs que se dijeron antes.'''
        self.logger.debug(u'looking for %s', what)
        if not what:
            self.say(channel,
                     u"%s: necesito que me pases algo a buscar..." % user)
            return

        self.cursor.execute ('''select * from url
            where title like '%%%s%%' or url like '%%%s%%' ''' % (what[0], what[0]))
        # self.cursor.execute (u"""select * from url where url like '%%%s%%'""" % (what[0], ))
        # self.cursor.execute ('''select * from url''')
        results= self.cursor.fetchall ()
        self.logger.debug('found %d results', len(results))
        if len(results) > 0:
            for result in results:
                data = dict(zip(('id', 'url', 'date', 'time', 'poster', 'title'), result))
                self.say(channel, self.config['found_format'] % data)
        else:
            self.say (channel, '%s: 404 Search term not found: %s' % (user, what[0]))

    def delete (self, user, channel, command, *what):
        u'''Borra de los registros los IDs indicados.'''
        if not what:
            self.say(channel,
                     u"%s: no pasaste ningún ID a borrar..." % user)
            return

        for uid in what:
            self.logger.debug (u'deleting %s' % uid)
            self.cursor.execute ('''delete from url
                where id = ?''', (uid, ))
        self.conn.commit ()
        self.say (channel, "%s: deleted %s" % (user, ", ".join (
            [ "[#%s]" % uid for uid in what ]
        )))

    def message (self, user, channel, message, date=None, time=None):
        g= self.url_re.search (message)
        if g is not None:
            url= g.groups()[0]

            # see if we can find it in the db
            self.cursor.execute ('''select * from url where url = ? ''', (url, ))
            result= self.cursor.fetchone ()
            if result is not None:
                data= dict (zip (('id', 'url', 'date', 'time', 'poster', 'title'), result))
                self.say (channel, self.config['found_format'] % data)
                return defer.fail ((url, False, 'already in db'))
            else:
                # go fetch it
                self.logger.debug ('fetching %s' % url)
                promise= client.getPage (str (url), headers=dict (
                    Range='bytes=1-%d' % self.config['block_size'])
                    )
                promise.addCallback (self.guessFile, user, channel, url, date, time)
                promise.addErrback (self.failed, user, channel, url, date, time)
                return promise

    ##### encoding detectors #####
    def pageContentType(self, page):
        encoding = None

        g = self.content_type_re.search(page)
        if g is not None:
            mimetype_enc = g.groups()[0]
            self.logger.debug(mimetype_enc)
            # text/html; charset=utf-8
            g = self.mimetype_re.search(mimetype_enc)
            if g is not None:
                mimetype = g.groups()[0]
                encoding = g.groups()[2]
            else:
                self.logger.warning ("further mimetype detection failed: %s" % mimetype_enc)
        else:
            self.logger.warning ("no mimetype in the page")

        return encoding

    def guess (self, page):
        encoding= None
        detect= chardet.detect (page)

        if detect['confidence']>self.config['guess_encoding']:
            encoding= detect['encoding']
            self.logger.debug ("chardet says it's %s" % encoding)
        else:
            self.logger.warning("chardet says it's %s, but with very "
                                "low confidence: %f",
                                encoding, detect['confidence'])

        return encoding

    def hardCoded (self, page):
        '''good as any'''
        return 'utf-8'

    def guessFile (self, page, user, channel, url, date, time):
        mimetype_enc= self.magic.buffer (page)
        g = self.mimetype_re.search(mimetype_enc)
        if g is not None:
            mimetype= g.groups()[0]
            encoding= g.groups()[2]
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

                # we leave self.guess to the end because chardet gets easily
                # confused if we use it too much (?)
                for method in (self.pageContentType, self.hardCoded, self.guess):
                    encoding = method(page)
                    self.logger.debug("Getting encoding with %s: %s",
                                      method.im_func.func_name, encoding)
                    if encoding is not None:
                        try:
                            data = title.decode(encoding)
                        except UnicodeDecodeError:
                            self.logger.debug("failed!")
                        else:
                            self.logger.debug("suceeded!")
                            title = data
                            break

                # convert xhtml entities
                title= BeautifulStoneSoup (title,
                    convertEntities=BeautifulStoneSoup.XHTML_ENTITIES).contents[0]

                # this takes out the \n\r\t's
                titleParts= title.split ()
                title= ' '.join (titleParts)
                self.logger.debug (u"[%s] >%s< %s" % (type (title), title, encoding))

                self.addUrl (channel, user, url, title, date=date, time=time)
            else:
                # the mimetype is better title than none
                self.addUrl (channel, user, url, mimetype=mimetype, date=date, time=time)
                title= mimetype
        else:
            self.addUrl (channel, user, url, mimetype=mimetype, date=date, time=time)
            title= mimetype
        return url, True, title

    def failed (self, failure, user, channel, url, date, time):
        self.logger.debug (failure)
        if str (failure.value).startswith ('206'):
            # this is not a failure, but a response to a '206 partial content'
            return self.guessFile (failure.value.response, user, channel, url, date, time)
        else:
            self.say(channel, u"%s: error con la página: %s" % (user, failure.value))
            return url, False, failure.value

    ##### log parsing #####
    def date_from_log (self, date):
        # shamelessly borrowed from the facundario
        # http://facundario.perrito666.com.ar/
        # tx perrito

        MONTHS = {
            "ene":  1,
            "jan":  1,
            "feb":  2,
            "mar":  3,
            "abr":  4,
            "apr":  4,
            "may":  5,
            "jun":  6,
            "jul":  7,
            "ago":  8,
            "aug":  8,
            "sep":  9,
            "oct": 10,
            "nov": 11,
            "dec": 12,
            "dic": 12,
        }

        # --- Day changed lun aug 27 2007
        # --- Log opened dom ago 26 00:33:58 2007
        if date.startswith("--- Day"):
            (x, x, x, x, m, d, y) = date.split()
        elif date.startswith("--- Log"):
            (x, x, x, x, m, d, x, y) = date.split()
        else:
            raise ValueError("Linea invalida, no es fecha: %r" % date)
        d, y = int(d), int(y)
        m = MONTHS[m.lower()]
        realDate = datetime.date(year=y, month=m, day=d)
        return realDate

    def parse_logs (self, logfile, channel):
        # irssi logs:
        # --- Log opened Mon May 04 10:38:38 2009
        # 10:38 < perrito666> que pasó?
        # --- Day changed Sat May 02 2009
        for logline in logfile.xreadlines ():
            if logline.startswith ('---'):
                date= self.date_from_log (logline)
            elif logline[6:9]!='-!-' and logline[7]!='*':
                time, logline = logline.split(' ', 1)
                # time should include seconds
                # good as any
                seconds= random.randint (0, 59)
                time+= ":%02d" % seconds
                nick, logline = logline.split('>', 1)
                logline = logline.strip()
                # take out the '< '
                nick = nick[2:]
                g= self.url_re.search (logline)
                if g is not None:
                    yield (date, time, channel, nick, logline)

    def import_logs (self, logfile, no_more_than=500):
        import os

        # monkeypatching say() and register () so they're noop()
        self.say = lambda perrito, gatito: None
        self.register= lambda *ignore: None

        # BUG: the config should be better
        self.init ({})

        channel= os.path.basename (logfile)
        if channel.endswith ('.log'):
            channel= channel[:-4]

        logfile= open(logfile)
        self.logfile_finished= False

        self.urlsFound= 0
        self.urlsFailed= 0
        self.urlsInDb= 0
        self.urlsOk= 0

        self.no_more_than= no_more_than
        self.batch= 0

        self.urls= []
        for data in self.parse_logs (logfile, channel):
            self.urls.append (data)
            self.urlsFound+= 1

        self.more ()

    def more (self):
        self.batch+= 1
        print "batch #%d" % self.batch
        data= self.urls[:self.no_more_than]
        self.urls= self.urls[self.no_more_than:]

        for date, time, channel, nick, log in data:
            promise= self.message (nick, channel, log, date, time)
            promise.addCallback (self.decay)
            promise.addErrback (self.decay)

    def decay (self, result):
        # handle failures
        if isinstance (result, failure.Failure):
            result= result.value

        url, ok, reason= result
        print url,
        if not ok:
            if reason=='already in db':
                self.urlsInDb+= 1
                print reason
            else:
                self.urlsFailed+= 1
                print 'failed:', reason
        else:
            self.urlsOk+= 1
            print 'ok', reason

        if (self.urlsOk+self.urlsInDb+self.urlsFailed)%self.no_more_than==0:
            self.more ()

        if self.urlsOk+self.urlsInDb+self.urlsFailed==self.urlsFound:
            # finished
            print "%d urls found, %d ok, %d in db, %d failed" % (self.urlsFound, self.urlsOk, self.urlsInDb, self.urlsFailed)
            reactor.stop ()

# end
