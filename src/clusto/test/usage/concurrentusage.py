from clusto.test import testbase

from clusto.drivers import BasicServer, BasicRack, IPManager
from clusto.drivers import BasicNetworkSwitch, BasicPowerStrip, PowerTowerXM
from clusto.exceptions import ConnectionException
import clusto

import os
import threading
import ConfigParser

thread_count = 0

def barrier_creator(count):

    semaphore = threading.Semaphore()
    event = threading.Event()

    def synchronise():
        """ All calls to this method will block until the last (count) call is made """
        global thread_count

        semaphore.acquire()
        thread_count += 1
        if thread_count == count:
            event.set()
        semaphore.release()

        event.wait(3)

    return synchronise

    
class ClustoWorkThread(threading.Thread):

    def __init__(self, db, echo, barrier):
        super(ClustoWorkThread, self).__init__()  
        conf = ConfigParser.ConfigParser()
        conf.add_section('clusto')
        conf.set('clusto', 'dsn', db)
        self.conf = conf
        self.echo = echo
        self.barrier = barrier
        
    def run(self):

        clusto.connect(self.conf,echo=self.echo)
        clusto.init_clusto()

        try:

            clusto.begin_transaction()

            e = clusto.Entity('foo'+self.getName())

            self.barrier()

            clusto.commit()
        except Exception, x:
            clusto.rollback_transaction()
            raise x
            
class ConcurrentTest(testbase.unittest.TestCase):

    def setUp(self):
        conf = ConfigParser.ConfigParser()
        conf.add_section('clusto')
        conf.set('clusto', 'dsn', testbase.DB)

        clusto.SESSION.clusto_version = clusto.working_version()
        clusto.connect(conf,echo=testbase.ECHO)
        clusto.METADATA.drop_all(clusto.SESSION.bind)
        clusto.clear()
        clusto.SESSION.close()


    def tearDown(self):
        if clusto.SESSION.is_active:
            raise Exception("SESSION IS STILL ACTIVE in %s" % str(self.__class__))

        clusto.clear()
        clusto.disconnect()
        clusto.METADATA.drop_all(clusto.SESSION.bind)

        
    def testConcurrentThreads(self):

        DB = testbase.DB
        if DB.startswith('sqlite'):
            return
            
        conf = ConfigParser.ConfigParser()
        conf.add_section('clusto')
        conf.set('clusto', 'dsn', testbase.DB)
        clusto.connect(conf, echo=testbase.ECHO)
        clusto.init_clusto()
        firstver = clusto.get_latest_version_number()
        
        threadcount = 5
        threads = []
        barrier = barrier_creator(threadcount)
        for i in range(threadcount):
            threads.append(ClustoWorkThread(DB, testbase.ECHO,
                                            barrier))

        for i in threads:
            i.start()

        for i in threads:
            i.join()

        self.assertEqual(clusto.get_latest_version_number(),
                         threadcount+firstver)        


        
