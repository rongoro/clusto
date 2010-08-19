from traceback import format_exc
from urlparse import urlparse
from telnetlib import Telnet
import httplib
import sys

try:
    import simplejson as json
except ImportError:
    import json

from basicserver import BasicVirtualServer
from clusto.exceptions import DriverException
import clusto

class KVMVirtualServer(BasicVirtualServer):
    _driver_name = "kvmvirtualserver"

    def __init__(self, name, **kwargs):
        BasicVirtualServer.__init__(self, name, **kwargs)

    def get_hypervisor(self):
        from clusto.drivers import VMManager
        host = VMManager.resources(self)
        if not host:
            raise DriverException('Cannot start a VM without first allocating a hypervisor')
        return host[0].value
        
    def _request(self, method, endpoint, body=None):
        host = self.get_hypervisor().get_ips()[0]
        conn = httplib.HTTPConnection(host, 3000)

        if body:
            body = json.dumps(body, indent=2, sort_keys=True)

        conn.request(method, endpoint, body)
        response = conn.getresponse()
        return (response.status, response.read())

    def kvm_create(self, options):
        status, response = self._request('POST', '/api/1/%s' % self.name, {
            'memory': options.memory,
            'disk': options.disk,
        })
        if status != 200:
            raise DriverException(response)

        response = json.loads(response)

        config = response['config']

        try:
            clusto.begin_transaction()
            self.set_attr(key='system', subkey='memory', value=config['memory'])
            self.set_attr(key='system', subkey='disk', value=config['disk'])
            self.set_attr(key='system', subkey='cpucount', value=1)
            self.set_attr(key='kvm', subkey='console-port', value=config['console'])
            self.set_attr(key='kvm', subkey='vnc-port', value=5900 + config['vnc'])
            self.set_port_attr('nic-eth', 1, 'mac', config['mac'])
            self.set_port_attr('nic-eth', 1, 'model', config['nic'])
            clusto.SESSION.clusto_description = 'Populate KVM information for %s' % self.name
            clusto.commit()
        except:
            sys.stderr.write(format_exc() + '\n')
            clusto.rollback_transaction()

    def kvm_update(self, options):
        attr = dict([(x.subkey, x.value) for x in self.attrs(key='system')])

        status, response = self._request('PUT', '/api/1/%s' % self.name, {
            'memory': attr['memory'],
            'disk': attr['disk'],
            'mac': self.get_port_attr('nic-eth', 1, 'mac'),
            'nic': self.get_port_attr('nic-eth', 1, 'model'),
        })
        if status != 201:
            raise DriverException(response)
        #response = json.loads(response)

    def kvm_delete(self, options):
        status, response = self._request('DELETE', '/api/1/%s' % self.name)
        if status != 200:
            raise DriverException(response)

    def kvm_status(self, options):
        status, response = self._request('GET', '/api/1/%s' % self.name)
        if status != 200:
            raise DriverException(response)
        response = json.loads(response)
        return response['state']

    def kvm_start(self, options):
        status, response = self._request('POST', '/api/1/%s/start' % self.name)
        if status != 200:
            raise DriverException(response)
        response = json.loads(response)
        if response['state'] != 'RUNNING':
            raise DriverException('VM is not in the RUNNING state after starting')

    def kvm_stop(self, options):
        status, response = self._request('POST', '/api/1/%s/stop' % self.name)
        if status != 200:
            raise DriverException(response)
        response = json.loads(response)
        if response['state'] != 'STOPPED':
            raise DriverException('VM is not in the STOPPED state after stopping')

    def kvm_console(self, options):
        client = Telnet(self.get_hypervisor().get_ips()[0], self.attr_value(key='kvm', subkey='console'))
        client.interact()
