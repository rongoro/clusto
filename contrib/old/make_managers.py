from clusto.scripthelpers import get_clusto_config
from clusto.drivers import IPManager
import clusto

def main():
    IPManager('sjc1-subnet-01', baseip='10.2.128.0', netmask='255.255.252.0', gateway='10.2.128.1')
    IPManager('sjc1-subnet-02', baseip='10.2.192.0', netmask='255.255.252.0')
    IPManager('sjc1-subnet-03', baseip='192.168.243.0', netmask='255.255.255.0')
    IPManager('sjc1-subnet-04', baseip='192.168.248.0', netmask='255.255.255.0')

if __name__ == '__main__':
    config = get_clusto_config()
    clusto.connect(config.get('clusto', 'dsn'))
    clusto.init_clusto()
    main()
