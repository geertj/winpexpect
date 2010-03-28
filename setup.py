#
# This file is part of WinPexpect. WinPexpect is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# WinPexpect is copyright (c) 2008-2010 by the WinPexpect authors. See the
# file "AUTHORS" for a complete overview.

from setuptools import setup

setup(
    name = 'winpexpect',
    version = '1.1',
    description = 'A version of pexpect that works under Windows.',
    author = 'Geert Jansen',
    author_email = 'geert@boskant.nl',
    url = 'http://bitbucket.org/geertj/winpexpect',
    license = 'MIT',
    classifiers = ['Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Operating System :: Microsoft :: Windows'],
    package_dir = {'': 'lib'},
    py_modules = ['pexpect', 'winpexpect'],
    test_suite = 'nose.collector'
)
