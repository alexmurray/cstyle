#!/usr/bin/env python
"""
Unit tests for cstyle.
"""
import cstyle
import os.path
import unittest

class CStyleTestCase(unittest.TestCase):
    """Base test case for testing CStyle."""
    def __init__(self, name, base_name, expected_errors):
        self._base_name = base_name
        self._expected_errors = (expected_errors if expected_errors is not None
                                 else [])
        super(CStyleTestCase, self).__init__(name)

    def runTest(self):
        """Override runTest method with our own implementation."""
        base = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            'test', self._base_name)
        errors = cstyle.CStyle(base + '.conf',
                               [base + '.c']).check()
        self.assertEqual(errors, self._expected_errors)

class CStyleTestSuite(unittest.TestSuite):
    """Test suite for cstyle."""
    def __init__(self):
        super(CStyleTestSuite, self).__init__()
        tests = {'0001_pointer_prefix': [],
                 '0002_pointer_prefix_repeat': [],
                 '0003_no_goto': [],
                 '0004_prefer_goto': []}
        for (base_name, expected_errors) in tests.iteritems():
            test = CStyleTestCase('runTest', base_name, expected_errors)
            self.addTest(test)

if __name__ == '__main__':
    unittest.TextTestRunner().run(CStyleTestSuite())
