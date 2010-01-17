# -*- coding: utf-8 -*-

# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

from time import time
from twisted.web import client
from BeautifulSoup import BeautifulSoup, Tag

from lalita import Plugin

def txtize(soup):
    if not isinstance(soup,Tag):
        return soup
    return ''.join(map(txtize,soup.childGenerator()))

class MoinSearch(Plugin):
    _site = 'http://www.python.com.ar'
    _places = {'body':
                     {'path':'moin?action=fullsearch&context=180&value=%s&fullsearch=Texto',
                      'tag': 'dt'},
               'title':
                     {'path': 'moin?action=fullsearch&context=180&value=%s&titlesearch=T%%C3%%ADtulos',
                      'tag': 'li'}
                    }
    _max_results = 1

    def init(self, config):
        self._internals = {}
        self.register(self.events.COMMAND, self.search, ['wiki'])

    def get_full_query(self,where,query):
        return '%s/%s' % (self._site,self._places[where]['path'] % query)

    def set_mode(self,id,mode):
        full_query = self.get_full_query(mode,self.get_internal(id,'query'))
        self._internals[id]['where'] = mode
        self._internals[id]['full_query'] = full_query

    def get_internal(self,id,key):
        return self._internals[id][key]

    def search(self, user, channel, command, *args):
        """First searchs for title, later if nothing found
        searchs for text"""
        id = time()
        query = ' '.join(map(str,args))
        self._internals[id] = {'command':command,
                               'user':user,
                               'channel': channel,
                               'query':query,
                               }
        self.set_mode(id,'title')
        d = client.getPage(self.get_internal(id,'full_query'))
        d.addCallback(self.parse_page,id)
        d.addCallback(self.search_body,id)
        return d

    def search_body(self,titleresults,id):
        if titleresults:
            return titleresults
        self.set_mode(id,'body')
        d = client.getPage(self.get_internal(id,'full_query'))
        d.addCallback(self.parse_page,id)
        return d

    def parse_page(self,page,id):
        where = self._internals[id]['where']
        soup = BeautifulSoup(page)
        div = soup.find('div','searchresults')
        if div is None:
            try:
                href = soup.find('ul',attrs = {'id':'navibar'}).find('li','current').find('a').get('href')
            except AttributeError, e:
                results = ['Encontré un problema: %s' % e]
            else:
                results = ['Hay 1 solo resultado: %s%s' % (self._site,href)]
        else:
            results = []
            for item in div.findAll(self._places[where]['tag']):
                anchor = item.find('a')
                href = self._site + anchor.get('href')
                name = txtize(anchor)
                results.append('%s: %s' % (name,href))
        return self.process_results(results,id)

    def drop_internal(self,id):
        del self._internals[id]

    def process_results(self,results,id):
        mode = self.get_internal(id,'where')
        channel = self.get_internal(id,'channel')
        full_query = self.get_internal(id,'full_query')
        if not results:
            if mode == 'title':
                return []
            else:
                self.say(channel,u'No econtré resultados')
        elif len(results) > self._max_results:
            self.say(channel, 'Hay %i resultados %s' % (len(results),full_query))
        else:
            self.say(channel,' '.join(results))
        self.drop_internal(id)

