#!/usr/bin/env python
"""
Unit tests for cstyle.
"""
import cstyle
import os.path
import unittest
import sys

class CStyleTestCase(unittest.TestCase):
    """Base test case for testing CStyle."""
    def __init__(self, name, basename, expected_errors):
        self._basename = basename
        self._expected_errors = (expected_errors if expected_errors is not None
                                 else [])
        super(CStyleTestCase, self).__init__(name)

    def runTest(self):
        """Test case"""
        # output our name as all tests are called runTest so too hard to
        # distinguish
        sys.stderr.write(self._basename + ' ... ')
        base = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            'test', self._basename)
        errors = cstyle.CStyle(base + '.conf',
                               [base + '.c']).check()
        self.assertEqual(errors, self._expected_errors)

class CStyleGenerateConfigTestCase(unittest.TestCase):
    """Test generation of configuration file."""
    def runTest(self):
        """Test configuration file generation."""
        cstyle.CStyle(None, []).generate_config()

class CStyleMainTestCase(unittest.TestCase):
    """Test main of cstyle."""
    def runTest(self):
        """Test cstyle.main."""
        sys.argv = [ "cstyle", "test/0001_pointer_prefix.c"]
        cstyle.main()

class CStyleMainNoArgumentsTestCase(unittest.TestCase):
    """Test main of cstyle with no arguments."""
    def runTest(self):
        """Test cstyle.main with no arguments."""
        sys.argv = [ "cstyle" ]
        cstyle.main()

class CStyleMainGenerateConfigTestCase(unittest.TestCase):
    """Test main of cstyle with --generate-config argument."""
    def runTest(self):
        """Test cstyle.main with --generate-config."""
        sys.argv = [ "cstyle", "--generate-config" ]
        cstyle.main()

class CStyleTestSuite(unittest.TestSuite):
    """Test suite for cstyle."""
    def __init__(self):
        super(CStyleTestSuite, self).__init__()
        base = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'test')
        tests = {'0001_pointer_prefix':
                 [
                     {'column': 27,
                      'file': os.path.join(base, '0001_pointer_prefix.c'),
                      'line': 1,
                      'reason': '"Argv" is invalid - expected pointer prefix "p"'}
                 ],
                 '0002_pointer_prefix_repeat':
                 [
                     {'column': 27,
                      'file': os.path.join(base, '0002_pointer_prefix_repeat.c'),
                      'line': 1,
                      'reason': '"pArgv" is invalid - expected pointer prefix "pp"'}
                 ],
                 '0003_no_goto':
                 [
                     {'column': 3,
                      'file': os.path.join(base, '0003_no_goto.c'),
                      'line': 3,
                      'reason': 'goto considered harmful'},
                     {'column': 3,
                      'file': os.path.join(base, '0003_no_goto.c'),
                      'line': 6,
                      'reason': 'goto considered harmful'}
                 ],
                 '0004_prefer_goto':
                 [
                     {'column': 5,
                      'file': os.path.join(base, '0004_prefer_goto.c'),
                      'line': 8,
                      'reason': 'Only 1 return statement per function (prefer_goto)'}
                 ],
                 '0005_arrays_are_pointers':
                 [
                     {'column': 26,
                      'file': os.path.join(base, '0005_arrays_are_pointers.c'),
                      'line': 1,
                      'reason': '"Argv" is invalid - expected pointer prefix "pp"'}
                 ],
                 '0006_arrays_arent_pointers':
                 [
                     {'column': 26,
                      'file': os.path.join(base, '0006_arrays_arent_pointers.c'),
                      'line': 1,
                      'reason': '"Argv" is invalid - expected pointer prefix "p"'}
                 ]
        }
        for (basename, expected_errors) in tests.iteritems():
            test = CStyleTestCase('runTest', basename, expected_errors)
            self.addTest(test)
        self.addTest(CStyleGenerateConfigTestCase())
        self.addTest(CStyleMainTestCase())
        self.addTest(CStyleMainNoArgumentsTestCase())
        self.addTest(CStyleMainGenerateConfigTestCase())

if __name__ == '__main__':
    unittest.TextTestRunner().run(CStyleTestSuite())
