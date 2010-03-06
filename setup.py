#
# This file is part of winpexpect. Winpexpect is free software that is
# made available under the MIT license. Consult the file "LICENSE" that
# is distributed together with this file for the exact licensing terms.
#
# Winpexpect is copyright (c) 2010 by the winpexpect authors. See the
# file "AUTHORS" for a complete overview.

from setuptools import setup

setup(
    name = 'winpexpect',
    version = '0.8',
    description = 'A version of pexpect that works under Windows.',
    author = 'Geert Jansen',
    author_email = 'geert@boskant.nl',
    url = 'http://bitbucket.org/geertj/winpexpect/wiki/Home',
    license = 'MIT',
    classifiers = ['Development Status :: 4 - Beta',
        'Intended Audience : = Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Operating System :: Microsoft :: Windows'],
    package_dir = {'': 'lib'},
    py_modules = ['pexpect', 'winpexpect'],
    test_suite = 'nose.collector'
)
