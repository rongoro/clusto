
import os
import sys
import clusto
import logging
import commands

from ConfigParser import SafeConfigParser
from optparse import OptionParser, make_option


scriptpaths = [os.path.realpath(os.path.join(os.curdir, 'scripts')),
               '/etc/clusto/scripts',
               '/usr/local/bin',
               '/usr/bin',
               ] #+ filter(lambda x: not x.endswith('.egg'), sys.path)

def list_clusto_scripts(path):
    """
    Return a list of clusto scripts in the given path.
    """

    if not os.path.exists(path):
        return []

    if os.path.isdir(path):
        dirlist = os.listdir(path)
    else:
        dirlist = [path]

    available = filter(lambda x: x.startswith("clusto-")
                       and not x.endswith('~')
                       and os.access(os.path.join(path,x), os.X_OK),
                       dirlist)

    
    return map(lambda x: os.path.join(path, x), available)

def runcmd(args):
    
    args[0] = 'clusto-' + args[0]
    cmdname = args[0]
    paths = os.environ['PATH'].split(':')

    cmd = None
    for path in paths:
        cmdtest = os.path.join(path, cmdname)
        if os.path.exists(cmdtest):
            cmd = cmdtest
            break

    if not cmd:
        raise CommandError(cmdname + " is not a clusto-command.")

    
    os.execvpe(cmdname, args, env=os.environ)


def get_command(cmdname):

    for path in scriptpaths:

        scripts = list_clusto_scripts(path)

        for s in scripts:
            if s.split('-')[1].split('.')[0] == cmdname:
                return s


    return None

def get_command_help(cmdname):

    fullpath = get_command(cmdname)

    return commands.getoutput(fullpath + " --help-description")
    
def get_clusto_config(filename=None):
    """Find, parse, and return the configuration data needed by clusto.

    Gets the config path from the CLUSTOCONFIG environment variable otherwise
    it is /etc/clusto/clusto.conf
    """

    filesearchpath = ['/etc/clusto/clusto.conf']

    
    filename = filename or os.environ.get('CLUSTOCONFIG')

    if not filename:
        filename = filesearchpath[0]

    if filename:
        if not os.path.exists(os.path.realpath(filename)):
            raise CmdLineError("Config file %s doesn't exist." % filename)
        
    config = SafeConfigParser()    
    config.read([filename])

    if not config.has_section('clusto'):
        config.add_section('clusto')

    if 'CLUSTODSN' in os.environ:
        config.set('clusto', 'dsn', os.environ['CLUSTODSN'])

    if not config.has_option('clusto', 'dsn'):
        raise CmdLineError("No database given for clusto data.")

    return config


def init_script(name=os.path.basename(sys.argv[0]), configfile=None,
                initializedb=False):
    """Initialize the clusto environment for clusto scripts.

    Connects to the clusto database, returns a python SafeConfigParser and a
    logger.

    Uses get_clusto_config and setup_logging
    """
    config = get_clusto_config(filename=configfile)
    clusto.connect(config.get('clusto', 'dsn'))

    if initializedb:
        clusto.init_clusto()
    
    logger = setup_logging(config=config, name=name)

    return (config, logger)


def setup_logging(config=None, name="clusto.script"):
    """Setup the default log level and return the logger

    The logger will try to log to /var/log and console.
    
    #FIXME shouldn't ignore the config
    """

    loglocation="/var/log"

    logfilename = os.path.join(loglocation,'clusto.log')
    
    if not (os.access(loglocation, os.W_OK) 
            or (os.path.exists(logfilename) and os.access(logfilename, os.W_OK))):
        logfilename = os.path.devnull
        
    logging.basicConfig(level=logging.WARNING,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename=logfilename,
                        )
    

    log = logging.getLogger(name)

    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)

    log.addHandler(console)

    return log


def setup_clusto_env(options):
    """
    Take clusto parameters and put it into the shell environment.
    """


    if options.dsn:
        os.environ['CLUSTODSN'] = options.dsn
    if options.configfile:
        os.environ['CLUSTOCONFIG'] = options.configfile

    if os.environ.has_key('CLUSTOCONFIG'):
        config = get_clusto_config(os.environ['CLUSTOCONFIG'])
    else:
        config = get_clusto_config()

    if not os.environ.has_key('CLUSTODSN'):
        os.environ['CLUSTODSN'] = config.get('clusto','dsn')

    return config

class CmdLineError(Exception):
    pass

class CommandError(Exception):
    pass


class ClustoScript(object):

    usage = "%prog [options]"
    option_list = []
    num_args = None
    num_args_min = 0
    short_description = "sample short descripton"
    
    def __init__(self):
        self.parser = OptionParser(usage=self.usage,
                                   option_list=self.option_list)

        self.parser.add_option("--help-description",
                                action="callback",
                               callback=self._help_description,
                               dest="helpdesc",
                               help="print out the short command description")

        
    

    def _help_description(self, option, opt_str, value, parser, *args, **kwargs):

        print self.short_description
        sys.exit(0)
    


def runscript(scriptclass):

    script = scriptclass()

    (options, argv) = script.parser.parse_args(sys.argv)

    config, logger = init_script()

    try:
        if (script.num_args != None and script.num_args != (len(argv)-1)) or script.num_args_min > (len(argv)-1):
            raise CmdLineError("Wrong number of arguments.")
        
        retval = script.main(argv,
                             options,
                             config=config,
                             log=logger)

    except (CmdLineError, LookupError), msg:
        print msg
        script.parser.print_help()
        return 1

    
    return sys.exit(retval)
