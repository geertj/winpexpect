#
# This file is part of winpexpect. Winpexpect is free software that is
# made available under the MIT license. Consult the file "LICENSE" that
# is distributed together with this file for the exact licensing terms.
#
# Winpexpect is copyright (c) 2010 by the winpexpect authors. See the
# file "AUTHORS" for a complete overview.

import os
from winpexpect import winspawn, TIMEOUT, ExceptionPexpect

from nose.tools import assert_raises


class TestWinspawn(object):

    def test_expect(self):
        ps = winspawn('powershell.exe -command -')
        ps.sendline('Get-Location')
        ps.expect('---\s+\r\n')
        cwd = ps.readline().strip()
        assert os.getcwd() == cwd
        ps.terminate()

    def test_expect_stderr(self):
        ps = winspawn('powershell.exe -command -')
        ps.sendline('Write-Error "my-error"')
        ps.expect('my-error')
        ps.terminate()

    def test_timeout(self):
        ps = winspawn('powershell.exe -command -')
        ps.sendline('Sleep 10; Write "done sleeping"')
        assert_raises(TIMEOUT, ps.expect, 'done sleeping', timeout=2)
        ps.terminate()

    def test_terminate(self):
        ps = winspawn('powershell.exe -command -')
        assert ps.isalive()
        ps.terminate()
        assert not ps.isalive()
        assert ps.exitstatus != 0
        ps.terminate()

    def test_wait(self):
        ps = winspawn('powershell.exe -command -')
        ps.sendline('Sleep 2; Exit')
        ps.wait()
        assert not ps.isalive()
        assert ps.exitstatus == 0
        ps.terminate()

    def test_exec_not_found(self):
        assert_raises(ExceptionPexpect, winspawn, ('powershll.exe',))

    def test_multiple_close(self):
        ps = winspawn('powershell.exe -command -')
        ps.close()
        ps.close()

    def test_multiple_terminate(self):
        ps = winspawn('powershell.exe -command -')
        ps.terminate()
        ps.terminate()

    def test_wait_after_close(self):
        ps = winspawn('powershell.exe -command -')
        ps.close()  # closes stdin and should therefore exit powershell
        ps.wait()
        assert not ps.isalive()

    def test_wait_timeout(self):
        ps = winspawn('powershell.exe -command -')
        assert_raises(TIMEOUT, ps.wait, timeout=2)
        ps.terminate()
