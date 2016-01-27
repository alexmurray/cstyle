#!/usr/bin/env python2
import ConfigParser
import cstyle
import os.path
import unittest

class TestCStyle(unittest.TestCase):
    def __init__(self, Name, ExpectedErrors=None):
        self._Name = Name
        self._ExpectedErrors = ExpectedErrors if ExpectedErrors is not None else []
        super(TestCStyle, self).__init__()

    def runTest(self):
        Base = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            'test', self._Name)
        Errors = cstyle.CStyle(Base + '.conf',
                               [Base + '.c']).CheckStyle()
        self.assertEqual(Errors, self._ExpectedErrors)

if __name__ == '__main__':
    Tests = {'0001_pointer_prefix': [],
             '0002_pointer_prefix_repeat': [],
             '0003_no_goto': [],
             '0004_prefer_goto': []}

    TestSuite = unittest.TestSuite()
    for (Name, Errors) in Tests.iteritems():
        TestCase = TestCStyle(Name, Errors)
        TestSuite.addTest(TestCase)
    unittest.TextTestRunner().run(TestSuite)
