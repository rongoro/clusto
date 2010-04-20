import clusto
from clusto.scripthelpers import init_script
import sys

#RU,type,switchport1,switchport2,consoleport,poweroutlet(s)

LAYOUT_DIR = '/home/synack/src/clusto/contrib/layout/'

def verify_rack(rack, layoutfile=None):
    rack = clusto.get_by_name(rack)

    if not layoutfile:
        layoutfile = rack.attr_values(key='racklayout')
        if not layoutfile:
            print 'No racklayout attribute for', rack.name
            return False
        layoutfile = layoutfile[0]

    good = True

    for line in file(LAYOUT_DIR + layoutfile):
        if line.startswith('#'): continue
        sys.stdout.write('RU%02i: ' % int(line.split(',', 1)[0]))
        result = verify_ru(rack, line)
        if result != True:
            good = False
            sys.stdout.write(result + '\n')
        else:
            sys.stdout.write('OK\n')

    if not good:
        print 'Rack failed verification'
    return good

def verify_port(device, porttype, portnum, target):
    ports = device.port_info

    if porttype in ports and portnum in ports[porttype]:
        if target:
            port = ports[porttype][portnum]
            connection = port['connection']
            if connection:
                connection = connection.name
            if port['otherportnum'] != target:
                return '%s %s:%i is connected to %s:%s, should be port %s' % (device.name, porttype, portnum, connection, port['otherportnum'], target)
        else:
            if port['otherportnum']:
                return '%s %s:%i is connected to %s:%s on %s, when it shouldn\'t be' % (device.name, porttype, portnum, porttype, port['otherportnum'], connection)
    return True

def verify_ru(rack, rulayout):
        ru, devicetype, sport1, sport2, cport, outlet = rulayout.split(',', 5)
        ru = int(ru)
        if sport1:
            sport1 = int(sport1)
        if sport2:
            sport2 = int(sport2)
        if cport:
            cport = int(cport)

        device = rack.get_device_in(ru)

        if devicetype == 'filled':
            return True

        if not devicetype:
            if device:
                return "%s exists where it shouldn't in RU %i" % (device.name, ru)
            else:
                return True
        else:
            if not device:
                return '%s is missing in RU %i' % (devicetype, ru)

        if device.type != devicetype:
            return '%s Wrong device type %s in RU %i. Should be %s' % (device.name, device.type, ru, devicetype)

        ports = device.port_info

        if devicetype in ('server', 'consoleserver', 'powerstrip'):
            result = verify_port(device, 'nic-eth', 1, sport1)
            if result != True:
                return result

            result = verify_port(device, 'nic-eth', 2, sport2)
            if result != True:
                return result

        if devicetype != 'consoleserver':
            result = verify_port(device, 'console-serial', 1, cport)
            if result != True:
                return result

        if outlet and devicetype != 'powerstrip':
            for i, poutlet in enumerate(outlet.split(';')):
                result = verify_port(device, 'pwr-nema-5', i, outlet)
                if result != True: return result
        return True

if __name__ == '__main__':
    init_script()

    if len(sys.argv) < 2:
        print 'Usage: %s <rack name> [layout file]' % sys.argv[0]
        sys.exit(0)

    rack = sys.argv[1]

    if len(sys.argv) > 2:
        layoutfile = sys.argv[2]
    else:
        layoutfile = None

    verify_rack(rack, layoutfile)
