try:
    import simplejson as json
except ImportError:
    import json

from urllib import urlencode, quote
from urlparse import urlsplit, urljoin
import httplib
import logging

from pprint import pprint

def request(method, url, body='', headers={}):
    logging.debug('%s %s' % (method, url))
    if type(body) != type(''):
        body = urlencode(body)
    url = urlsplit(url, 'http')

    conn = httplib.HTTPConnection(url.hostname, url.port)
    if url.query:
        query = '%s?%s' % (url.path, url.query)
    else:
        query = url.path
    conn.request(method, query, body, headers)
    response = conn.getresponse()
    length = response.getheader('Content-length', None)
    if length:
        data = response.read(int(length))
    else:
        data = response.read()
    conn.close()
    if response.status >= 400:
        logging.debug('Server error %s: %s' % (response.status, data))
    return (response.status, response.getheaders(), data)

class ClustoProxy(object):
    def __init__(self, url):
        self.url = url

    def get_entities(self, **kwargs):
        for k, v in kwargs.items():
            if k == 'attrs':
                kwargs[k] = json.dumps(v)
        status, headers, response = request('POST', self.url + '/query/get_entities?%s' % urlencode(kwargs))
        if status != 200:
            raise Exception(response)
        return [EntityProxy(self.url + x) for x in json.loads(response)]

    def get_by_name(self, name):
        status, headers, response = request('GET', self.url + '/query/get_by_name?name=%s' % quote(name))
        if status != 200:
            raise Exception(response)
        obj = json.loads(response)
        return EntityProxy(self.url + obj['object'])

    def get_from_pools(self, pools, clusto_types=None):
        url = self.url + '/query/get_from_pools?pools=%s' % ','.join(pools)
        if clusto_types:
            url += '&types=' + ','.join(clusto_types)
        status, headers, response = request('GET', url)
        if status != 200:
            raise Exception(response)
        return [EntityProxy(self.url + x) for x in json.loads(response)]

    def get_ip_manager(self, ip):
        status, headers, response = request('GET', self.url + '/query/get_ip_manager?ip=%s' % ip)
        if status != 200:
            raise Exception(response)
        return EntityProxy(self.url + json.loads(response))

class EntityProxy(object):
    def __init__(self, url):
        self.url = url
        self.name = self.url.rsplit('/', 1)[1]

    def __getattr__(self, action):
        def method(**kwargs):
            data = {}
            for k, v in kwargs.items():
                if isinstance(v, bool):
                    v = int(v)
                if not type(v) in (int, str, unicode):
                    v = json.dumps(v)
                data[k] = v
            if data:
                status, headers, response = request('GET', '%s/%s?%s' % (self.url, action, urlencode(data)))
            else:
                status, headers, response = request('GET', '%s/%s' % (self.url, action))
            if status != 200:
                raise Exception(response)
            if response:
                return json.loads(response)
            else:
                return None
        return method

    def contents(self):
        return [EntityProxy(urljoin(self.url, x)) for x in self.show()['contents']]

    def parents(self):
        return [EntityProxy(urljoin(self.url, x)) for x in self.show()['parents']]

    def attrs(self, **kwargs):
        return self.__getattr__('attrs')(**kwargs)['attrs']
    
    def set_port_attr(self, porttype, portnum, key, value):
        return self.__getattr__('set_port_attr')(porttype=porttype, portnum=portnum, key=key, value=value)

    def get_port_attr(self, porttype, portnum, key):
        return self.__getattr__('get_port_attr')(porttype=porttype, portnum=portnum, key=key)

    def __str__(self):
        return urlsplit(self.url).path

    def __repr__(self):
        return 'EntityProxy(%s)' % repr(self.url)

def test():
    clusto = ClustoProxy('http://127.0.0.1:9996')
    server = clusto.get_entities(attrs=[{'subkey': 'mac', 'value': '00:a0:d1:e9:3d:dc'}])
    server = server[0]
    print server
    assert server.name == 's0104'
    attr = server.get_port_attr('nic-eth', 1, 'mac')
    server.set_port_attr('nic-eth', 1, 'mac', attr)
    newattr = server.get_port_attr('nic-eth', 1, 'mac')
    print repr((attr, newattr))
    assert newattr == attr
    #print server.parents()
    #obj = clusto.get_by_name('s1100')
    #pprint(obj.ports())
    #pprint(obj.attrs(key='dhcp', merge_container_attrs=True))
    #webservers = clusto.get_from_pools(['webservers-lolcat', 'production'])
    #pprint(webservers)
    #pprint(webservers[0].contents())

if __name__ == '__main__':
    test()
