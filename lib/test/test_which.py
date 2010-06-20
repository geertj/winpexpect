#
# This file is part of WinPexpect. WinPexpect is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# WinPexpect is copyright (c) 2008-2010 by the WinPexpect authors. See the
# file "AUTHORS" for a complete overview.

import os
import os.path
import tempfile
import shutil

from winpexpect import which


class TestWhich(object):

    root = 'c:\\'
    systemdir = r'c:\windows\system32'

    def setUp(self):
        self.saved_path = os.environ['Path']
        self.saved_pathext = os.environ['Pathext']
        self.saved_cwd = os.getcwd()
        self.tempdirs = []

    def tearDown(self):
        os.environ['Path'] = self.saved_path
        os.environ['Pathext'] = self.saved_pathext
        os.chdir(self.saved_cwd)
        for dname in self.tempdirs:
            try:
                shutil.rmtree(dname)
            except OSError:
                pass

    def tempdir(self):
        dname = tempfile.mkdtemp()
        self.tempdirs.append(dname)
        return dname

    def test_simple(self):
        assert which('cmd.exe') is not None
        assert which('chcp.com') is not None
    
    def test_extensions(self):
        assert which('cmd').lower().endswith('.exe')
        assert which('cmd.exe').lower() == which('cmd').lower()
        assert which('chcp').lower().endswith('.com')
        assert which('chcp.com').lower() == which('chcp').lower()

    def test_absolute_path(self):
        assert which(os.path.join(self.systemdir, 'cmd.exe')) is not None

    def test_current_directory(self):
        os.environ['Path'] = ''
        os.chdir(self.root)
        assert which('cmd.exe') is None
        os.chdir(self.systemdir)
        assert which('cmd.exe') is not None

    def test_no_path(self):
        os.environ['Path'] = ''
        os.chdir(self.root)
        assert which('cmd.exe') is None
        assert which(os.path.join(self.systemdir, 'cmd.exe')) is not None

    def test_current_directory_has_precendence(self):
        dname = self.tempdir()
        shutil.copyfile(os.path.join(self.systemdir, 'cmd.exe'),
                        os.path.join(dname, 'cmd.exe'))
        os.chdir(self.root)
        cmd1 = which('cmd.exe')
        os.chdir(dname)
        cmd2 = which('cmd.exe')
        assert cmd1.lower() != cmd2.lower()
