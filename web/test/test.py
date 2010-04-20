from rest import request
from pprint import pprint
from traceback import format_exc

try: import json
except ImportError: import simplejson as json

BASE_URL = 'http://localhost:9999'

def test_default_delegate():
    status, headers, data = request('GET', BASE_URL + '/')
    assert status == 200
    assert type(json.loads(data)) == list
    return True

def test_types_delegate():
    status, headers, data = request('GET', BASE_URL + '/server')
    assert status == 200
    data = json.loads(data)
    assert type(data) == list
    if len(data) > 0:
        assert type(data[0]) == str
    return True

def test_action_delegate():
    testname = '/pool/api_test_pool'

    test_create(testname)
    test_create('/pool/api_test_child')

    test_action_addattr(testname)
    test_action_delattr(testname)
    test_action_insert(testname)
    test_action_remove(testname)
    test_action_show(testname)

    test_delete('/pool/api_test_child')
    test_delete(testname)

def test_create(testname):
    status, headers, data = request('POST', BASE_URL + testname)
    assert status == 201
    data = json.loads(data)
    assert 'object' in data
    assert data['object'] == testname
    return True

def test_action_addattr(testname):
    status, headers, data = request('GET', BASE_URL + testname + '/addattr?key=testkey&value=testvalue')
    assert status == 200
    data = json.loads(data)
    assert type(data) == dict
    assert data['attrs'] == [{'key': 'testkey', 'value': 'testvalue', 'subkey': None, 'number': None, 'datatype': 'string'}]
    return True

def test_action_delattr(testname):
    status, headers, data = request('GET', BASE_URL + testname + '/delattr?key=testkey')
    assert status == 200
    data = json.loads(data)
    assert len(data['attrs']) == 0
    return True

def test_action_insert(testname):
    status, headers, data = request('GET', BASE_URL + testname + '/insert?object=/pool/api_test_child')
    assert status == 200
    data = json.loads(data)
    assert data['contents'] == ['/pool/api_test_child']
    return True

def test_action_remove(testname):
    status, headers, data = request('GET', BASE_URL + testname + '/remove?object=/pool/api_test_child')
    assert status == 200
    data = json.loads(data)
    assert data['contents'] == []
    return True

def test_action_show(testname):
    status, headers, data = request('GET', BASE_URL + testname + '/show')
    assert status == 200
    data = json.loads(data)
    for field in ('object', 'attrs', 'contents', 'parents', 'actions'):
        assert field in data.keys()
    return True

def test_delete(testname):
    status, headers, data = request('DELETE', BASE_URL + testname)
    assert status in (200, 202, 204)
    return True

if __name__ == '__main__':
    test_default_delegate()
    test_types_delegate()
    test_action_delegate()
