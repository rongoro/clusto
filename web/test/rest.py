import httplib
import logging
from urllib import urlencode
from urlparse import urlsplit

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

def tinyurl(url):
    status, response = request('GET', 'http://tinyurl.com/api-create.php?url=%s' % url)
    return response
