#import plugins.plugin

import urllib
from BeautifulSoup import BeautifulSoup, Tag
from dispatcher import dispatcher

def register ():
    pass


class




def txtize(soup):
    if not isinstance(soup,Tag):
        return soup
    return ''.join(map(txtize,soup.childGenerator()))

class _MoinSearch(object):
    _site = 'http://www.python.com.ar'
    _places = {'body':
                     {'path':'/moin?action=fullsearch&context=180&value=%s&fullsearch=Texto',
                      'tag': 'dt'},
               'title':
                     {'path': '/moin?action=fullsearch&context=180&value=%s&titlesearch=T%%C3%%ADtulos',
                      'tag': 'li'}
                    }

    def __init__(self,query,site=None,places=None):


        self.query = query
        if site is not None:
            self._site = site
        if places is not None:
            self._places = places

    def get_full_query(self,where):
        return '%s/%s' % (self._site,self._places[where]['path'] % self.query)

    def process(self, max_resutls=1):
        results = []
        for place in ['title','body']: #I want first title results!
            results = self.get_results(place)
            if results:
                break
        results_count = len(results)
        if not results:
            return (0,[])
        if results_count > max_resutls:
            return (results_count,[self.get_full_query(place)])
        return (results_count,results)

    def get_results(self,where):
        url = self.get_full_query(where)
        page = urllib.urlopen(url)
        soup = BeautifulSoup(page.read())
        if page.geturl() != url:
            # If there was only one result, moin redirected me to it
            title = txtize(soup.find('head').find('title'))
            return ['%s: %s' % (title,page.geturl())]
        div = soup.find('div','searchresults')
        results = []
        for item in div.findAll(self._places[where]['tag']):
            anchor = item.find('a')
            href = self._site + anchor.get('href')
            name = txtize(anchor)
            results.append('%s: %s' % (name,href))
        return results
