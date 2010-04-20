import os.path
import logging.handlers
import logging
import sys
import os

try:
    import simplejson as json
except ImportError:
    import json

LEVELS = {
    'DEBUG':    logging.DEBUG,
    'INFO':     logging.INFO,
    'WARNING':  logging.WARNING,
    'ERROR':    logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}

files = [
    '/etc/clusto/services.conf',
    '%s/.clusto/services.conf' % os.environ.get('HOME', '/tmp'),
    'services.conf',
]

config = None
for filename in files:
    if os.path.exists(filename):
        try:
            config = json.load(file(filename, 'r'))
            break
        except:
            sys.stderr.write('Unable to parse config file %s: %s\n' % (filename, sys.exc_info()[1]))

if not config:
    sys.stderr.write('Unable to find services.conf!\n')

def conf(key):
    obj = config
    for k in key.split('.'):
        obj = obj[k]
    return obj

def get_logger(name, level='INFO'):
    log = logging.getLogger(name)

    fmt = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s', '%Y-%m-%d %H:%M:%S')
    stdout = logging.StreamHandler()
    stdout.setFormatter(fmt)

    fmt = logging.Formatter('%(name)s %(message)s')
    syslog = logging.handlers.SysLogHandler()
    syslog.setFormatter(fmt)

    log.addHandler(stdout)
    log.addHandler(syslog)
    log.setLevel(LEVELS[level])
    return log
