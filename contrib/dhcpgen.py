from clusto.scripthelpers import init_script
from clusto.drivers import PenguinServer, IPManager
import clusto
import sys

from traceback import format_exc

ATTR_MAP = {
    'tftp-server': 'next-server',
    'tftp-filename': 'filename',
    'nfsroot': 'option root-path',
}

def main():
    #for server in clusto.get_entities(clusto_drivers=[PenguinServer]):
    for server in clusto.get_by_name('fai').contents():
        out = 'host %s { ' % server.name

        try:
            mac = server.get_port_attr('nic-eth', 1, 'mac')
            if not mac:
                sys.stderr.write('No nic-eth:1 mac for %s\n' % server.name)
                continue
            out += 'hardware ethernet %s; ' % mac
        except:
            sys.stderr.write(format_exc() + '\n')
            continue

        ip = IPManager.get_ips(server)
        if ip:
            ip = ip[0]
            out += 'fixed-address %s; ' % ip

        options = {}
        for attr in server.attrs(key='dhcp', merge_container_attrs=True):
            if attr.subkey in options: continue
            if not attr.subkey in ATTR_MAP:
                sys.stderr.write('Unknown subkey: %s\n' % attr.subkey)
                continue
            options[ATTR_MAP[attr.subkey]] = attr.value

        for key, value in options.items():
            out += '%s %s; ' % (key, value)

        out += '}\n'

        sys.stdout.write(out)
        sys.stdout.flush()

if __name__ == '__main__':
    init_script()
    main()
