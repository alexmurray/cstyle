#!/usr/bin/env python2
"""
This module defines the attributes of the PyPI package for cstyle
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='cstyle',
    version='0.1.0',
    description='CStyle C/C++ Style Checker',
    long_description=long_description,
    url='https://github.com/alexmurray/cstyle',
    author='Alex Murray',
    author_email='murray.alex@gmail.com',
    license='GPLv3+',
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: C',
        'Programming Language :: C++',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Quality Assurance',
    ],
    keywords='development',
    py_modules=['cstyle'],
    install_requires=['clang'],
    test_suite='test-cstyle.CStyleTestSuite',
    entry_points={
        'console_scripts': [
            'cstyle=cstyle:Main',
        ],
    },
)
