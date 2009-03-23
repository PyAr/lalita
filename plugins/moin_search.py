#import plugins.plugin

from twisted.web import client
from BeautifulSoup import BeautifulSoup, Tag
from core.dispatcher import dispatcher
from core.events import COMMAND
from twisted.internet import reactor

def txtize(soup):
    if not isinstance(soup,Tag):
        return soup
    return ''.join(map(txtize,soup.childGenerator()))

class MoinSearch(object):
    _site = 'http://www.python.com.ar'
    _places = {'body':
                     {'path':'/moin?action=fullsearch&context=180&value=%s&fullsearch=Texto',
                      'tag': 'dt'},
               'title':
                     {'path': '/moin?action=fullsearch&context=180&value=%s&titlesearch=T%%C3%%ADtulos',
                      'tag': 'li'}
                    }
    _max_results = 1

    def __init__(self,config,params):
        print config
        print params
        dispatcher.register(COMMAND,self.search,['wiki'])

    def get_full_query(self,where,query):
        return '%s/%s' % (self._site,self._places[where]['path'] % query)

    def search(self, command, user, channel, *args):
        """First searchs for title, later if nothing found
        searchs for text"""
        query = ' '.join(map(str,args))
        d = client.getPage(self.get_full_query('title',query))
        d.addCallback(self.parse_page,'title')
        d.addCallback(self.search_body,query)
        return d

    def search_body(self,titleresults,query):
        if titleresults:
            return titleresults
        d = client.getPage(self.get_full_query('body',query))
        d.addCallback(self.parse_page,'body')
        return d

    def parse_page(self,page,where):
        print 'estoy parseando'
        soup = BeautifulSoup(page)
        div = soup.find('div','searchresults')
        results = []
        for item in div.findAll(self._places[where]['tag']):
            anchor = item.find('a')
            href = self._site + anchor.get('href')
            name = txtize(anchor)
            results.append('%s: %s' % (name,href))
        return self.process_resutls(results,where)

    def process_resutls(self,results,where):
        return results

#def main():
    #disp = dispatcher.Dispatcher()
    #ms = MoinSearch(disp)
    #disp.push(COMMAND,'wiki', 'rafen', '#pyar', 'karma')
    #reactor.run()

if __name__ == '__main__':
    main()

