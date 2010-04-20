from rest import request

BASE_URL = 'http://localhost:9999'

status, headers, data = request('DELETE', BASE_URL + '/pool/api_test_pool')
print 'DELETE /pool/api_test_pool (%i)' % status
status, headers, data = request('DELETE', BASE_URL + '/pool/api_test_child')
print 'DELETE /pool/api_test_child (%i)' % status
