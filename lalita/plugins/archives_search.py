# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

import urllib
from BeautifulSoup import BeautifulSoup, Tag

def register ():
    pass

def txtize(soup):
    if not isinstance(soup,Tag):
        return soup
    return ''.join(map(txtize,soup.childGenerator()))

class ArchivesSearch:
    _site = 'http://search.gmane.org/?query=%s&group=gmane.org.user-groups.python.argentina'

    def __init__(self,query,site=None):
        self.query = query
        if site is not None:
            self._site = site

    def get_full_query(self):
        return self._site % urllib.quote(self.query)

    def process(self):
        url = 'http://localhost/~javier/asdf.html'
        url = self.get_full_query() ## Comment for offline mode
        page = urllib.urlopen(url)
        soup = BeautifulSoup(page.read())
        f = file('/home/javier/public_html/a.html','w')
        f.write(soup.renderContents())
        f.close()
        summary = soup.find('table','otable')
        if summary is None:
            if 'No documents match your query':
                return 'Noy hay resultados'
            else:
                return None
        summary = summary.find('td','webtd')
        brs = summary.findAll('br')
        if len(brs) != 2 or brs[0].next != brs[1].previous:
            return None
        matches = brs[0].next.strip()
        if matches is None:
            return None
        return '%s: %s' % (matches.encode('utf-8'),url)
