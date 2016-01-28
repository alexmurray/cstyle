#!/usr/bin/env python2
import ConfigParser
import cstyle
import os.path
import unittest

class CStyleTestCase(unittest.TestCase):
    """Base test case for testing CStyle."""
    def __init__(self, Name, BaseName, ExpectedErrors):
        self._BaseName = BaseName
        self._ExpectedErrors = ExpectedErrors if ExpectedErrors is not None else []
        super(CStyleTestCase, self).__init__(Name)

    def runTest(self):
        Base = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            'test', self._BaseName)
        Errors = cstyle.CStyle(Base + '.conf',
                               [Base + '.c']).CheckStyle()
        self.assertEqual(Errors, self._ExpectedErrors)

class CStyleTestSuite(unittest.TestSuite):
    def __init__(self):
        super(CStyleTestSuite, self).__init__()
        Tests = {'0001_pointer_prefix': [],
                 '0002_pointer_prefix_repeat': [],
                 '0003_no_goto': [],
                 '0004_prefer_goto': []}
        for (BaseName, ExpectedErrors) in Tests.iteritems():
            TestCase = CStyleTestCase('runTest', BaseName, ExpectedErrors)
            self.addTest(TestCase)

if __name__ == '__main__':
    unittest.TextTestRunner().run(CStyleTestSuite())
