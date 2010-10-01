import sys
import os

sys.path.insert(0, os.curdir)


import unittest

import clusto

import ConfigParser

DB='sqlite:///:memory:'
ECHO=False

class ClustoTestResult(unittest.TestResult):
    def addError(self, test, err):
        """Called when an error has occurred. 'err' is a tuple of values as
        returned by sys.exc_info().
        """
        print >>sys.stderr, "ERROR HERE!"
        clusto.rollback_transaction()
        self.errors.append((test, self._exc_info_to_string(err, test)))
        


class ClustoTestBase(unittest.TestCase):



    def data(self):
        pass
    
    def setUp(self):

        conf = ConfigParser.ConfigParser()
        conf.add_section('clusto')
        conf.set('clusto', 'dsn', DB)
        clusto.SESSION.clusto_version = clusto.working_version()
        clusto.connect(conf,echo=ECHO)
        clusto.clear()
        clusto.SESSION.close()
        clusto.init_clusto()
        self.data()


    def tearDown(self):
        if clusto.SESSION.is_active:
            raise Exception("SESSION IS STILL ACTIVE in %s" % str(self.__class__))

        clusto.clear()
        clusto.disconnect()
        clusto.METADATA.drop_all(clusto.SESSION.bind)



    def defaultTestResult(self):
        if not hasattr(self._testresult):
            self._testresult = ClustoTestResult()

        return self._testresult

