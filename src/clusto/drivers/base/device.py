
from clusto.drivers.base import Driver
import sys

class Device(Driver):

    _properties = {'model':None,
                   'serialnum':None,
                   'manufacturer':None}

    _clustotype = "device"
    _driver_name = "device"


    @classmethod
    def get_by_serial_number(self, serialnum):
        pass

    def _get_hostname(self):
        """return a hostname set for this device or its entity name"""

        hostname = self.attrs("hostname")

        if hostname:
            return hostname[0].value
        else:
            return self.entity.name
        
    def _set_hostname(self, name):

        self.set_attr("hostname", value=name)

    hostname = property(_get_hostname, _set_hostname)

    @property
    def fqdns(self):
        """return the fully qualified domain names for this device"""

        return self.attr_values("fqdn")


    def add_fqdn(self, fqdn):
        """add a fully qualified domain name"""
        
        if not self.has_attr("fqdn", number=True, value=fqdn):
            self.add_attr("fqdn", number=True, value=fqdn)

    def remove_fqdn(self, fqdn):
        """remove a fully qualified domain name"""
        
        self.del_attrs("fqdn", number=True, value=fqdn)

    def _power_captcha(self):
        while True:
            sys.stdout.write('Are you sure you want to reboot %s (yes/no)? ' % self.name)
            line = sys.stdin.readline().rstrip('\r\n')
            if line == 'yes':
                return True
            if line == 'no':
                return False
            sys.stdout.write('"yes" or "no", please\n')

    def power_on(self, captcha=True):
        if captcha and not self._power_captcha():
            return

        ports_set = 0
        for porttype, ports in self.port_info.items():
            if not porttype.startswith('pwr-'): continue
            for portnum, port in ports.items():
                if not port['connection']: continue
                port['connection'].set_power_on(porttype, port['otherportnum'])
                ports_set += 1
        return ports_set

    def power_off(self, captcha=True):
        if captcha and not self._power_captcha():
            return

        ports_set = 0
        for porttype, ports in self.port_info.items():
            if not porttype.startswith('pwr-'): continue
            for portnum, port in ports.items():
                if not port['connection']: continue
                port['connection'].set_power_off(porttype, port['otherportnum'])
                ports_set += 1
        return ports_set

    def power_reboot(self, captcha=True):
        if captcha and not self._power_captcha():
            return

        ports_rebooted = 0
        for porttype, ports in self.port_info.items():
            if not porttype.startswith('pwr-'): continue
            for portnum, port in ports.items():
                if not port['connection']: continue
                port['connection'].reboot(porttype, port['otherportnum'])
                ports_rebooted += 1
        return ports_rebooted

    def console(self, ssh_user='root'):
        console = self.port_info['console-serial'][1]
        if not console['connection']:
            sys.stderr.write('No console connected to %s console-serial:1\n' % self.name)
            sys.stderr.flush()
            return

        if not hasattr(console['connection'], 'console'):
            sys.stderr.write('No console method on %s\n' % console.name)
            sys.stderr.flush()
            return

        console['connection'].connect('console-serial', console['otherportnum'], ssh_user)
