#
# This file is part of WinPexpect. WinPexpect is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# WinPexpect is copyright (c) 2008-2010 by the WinPexpect authors. See the
# file "AUTHORS" for a complete overview.

import sys
from setuptools import setup


if sys.version_info[0] == 3:
    from lib2to3.fixes import fix_types
    fix_types._TYPE_MAPPING['StringTypes'] = '(str,)'

setup(
    name = 'winpexpect',
    version = '1.5',
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
    test_suite = 'nose.collector',
    install_requires = ['pywin32 >= 214'],
    zip_safe = False,
    use_2to3 = True
)
