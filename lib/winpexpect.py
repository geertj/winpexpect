#
# This file is part of WinPexpect. WinPexpect is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# WinPexpect is copyright (c) 2008-2010 by the WinPexpect authors. See the
# file "AUTHORS" for a complete overview.

import os
import pywintypes

from Queue import Queue, Empty
from threading import Thread

from pexpect import (spawn, split_command_line, which, ExceptionPexpect,
                     EOF, TIMEOUT)
from subprocess import list2cmdline

from msvcrt import open_osfhandle
from win32api import SetHandleInformation, GetCurrentProcess
from win32con import (HANDLE_FLAG_INHERIT, STARTF_USESTDHANDLES,
                      STARTF_USESHOWWINDOW, CREATE_NEW_CONSOLE, SW_HIDE)
from win32pipe import CreatePipe
from win32process import (STARTUPINFO, CreateProcess, CreateProcessAsUser,
			  GetExitCodeProcess, TerminateProcess)
from win32event import (WaitForSingleObject, INFINITE, WAIT_OBJECT_0,
                        WAIT_TIMEOUT)
from win32security import (LogonUser, OpenProcessToken, LOGON32_LOGON_BATCH,
                           LOGON32_PROVIDER_DEFAULT, TOKEN_ALL_ACCESS)
from pywintypes import error as WindowsError


class ChunkBuffer(object):
    """A buffer that allows a chunk of data to be read in smaller reads."""

    def __init__(self, chunk=''):
        self.add(chunk)

    def add(self, chunk):
        self.chunk = chunk
        self.offset = 0 

    def read(self, size):
        data = self.chunk[self.offset:self.offset+size]
        self.offset += size
        return data

    def __len__(self):
        return max(0, len(self.chunk)-self.offset)


class winspawn(spawn):
    """A version of pexpect.spawn that works on Windows.

    I/O works completely different in this version when compared to the Posix
    version of spawn. The difference is caused by the fact that it's not
    possible on Windows to select() on a file descriptor that corresponds to a
    file or a pipe. Therefore, to do non-blocking I/O, we need to use threads.
    One thread is used to read the child's standard output, and another thread
    reads standard error. Those results are passed down to the main thread via
    a Queue.Queue.

    Windows also does not have ptys. It does have the concept of a "Console"
    though but it's much less sophisticated. This code runs the child in a new
    console by passing the flag CREATE_NEW_CONSOLE to CreateProcess(). The
    advantage of this is the child not interfere with the current console, and
    it is also possible to run the main program without a console (e.g. a
    Windows service).
    """

    def __init__(self, command, args=[], timeout=30, maxread=2000,
                 searchwindowsize=None, logfile=None, cwd=None, env=None,
                 username=None, domain=None, password=None):
        """Constructor."""
        self.username = username
        self.domain = domain
        self.password = password
        self.child_handle = None
        self.child_output = Queue()
        self.chunk_buffer = ChunkBuffer()
        self.stdout_fd = None
        self.stdout_eof = False
        self.stdout_reader = None
        self.stderr_fd = None
        self.stderr_eof = False
        self.stderr_reader = None
        super(winspawn, self).__init__(command, args, timeout=timeout,
                maxread=maxread, searchwindowsize=searchwindowsize,
                logfile=logfile, cwd=cwd, env=env)

    def __del__(self):
        self.terminate()

    def _spawn(self, command, args=None):
        """Start the child process. If args is empty, command will be parsed
        (split on spaces) and args will be set to the parsed args."""
        # The approach is documented here:
        # http://msdn.microsoft.com/en-us/library/ms682499(VS.85).aspx
        if args:
            self.args = args[:]  # copy
            self.args.insert(0, command)
            self.command = command
        else:
            self.args = split_command_line(command)
            self.command = self.args[0]
        executable = which(self.command)
        if executable is None:
            raise ExceptionPexpect, 'Command not found: %s' % self.command
        args = list2cmdline(self.args)

        # Create the pipes
        stdin_read, stdin_write = CreatePipe(None, 0)
        SetHandleInformation(stdin_read, HANDLE_FLAG_INHERIT, 1)
        stdout_read, stdout_write = CreatePipe(None, 0)
        SetHandleInformation(stdout_write, HANDLE_FLAG_INHERIT, 1)
        stderr_read, stderr_write = CreatePipe(None, 0)
        SetHandleInformation(stderr_write, HANDLE_FLAG_INHERIT, 1)

        # The standard io streams are redirected by passing a STARTUPINFO
        # structure to CreateProcess. We also create a new console and hide
        # it. This allows us to run e.g. as a service.
        startupinfo = STARTUPINFO()
        startupinfo.dwFlags |= STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW
        startupinfo.hStdInput = stdin_read
        startupinfo.hStdOutput = stdout_write
        startupinfo.hStdError = stderr_write
        startupinfo.wShowWindow = SW_HIDE

        # Create a new token or run as the current process.
        if self.username and self.password:
            token = LogonUser(self.username, self.domain, self.password,
                              LOGON32_LOGON_BATCH, LOGON32_PROVIDER_DEFAULT)
            hp, ht, pid, tid = CreateProcessAsUser(token, executable, args,
                                    None, None, True, CREATE_NEW_CONSOLE,
                                    self.env, self.cwd, startupinfo)
        else:
            hp, ht, pid, tid = CreateProcess(executable, args, None, None,
				    True, CREATE_NEW_CONSOLE, self.env,
				    self.cwd, startupinfo)

        self.child_handle = hp
        self.pid = pid
        ht.Close()

        # Close parent copy of child handles
        stdin_read.Close()
        stdout_write.Close()
        stderr_write.Close()

        # Create file descriptors and start up reader threads
        self.child_fd = open_osfhandle(stdin_write.Detach(), 0)
        self.stdout_fd = open_osfhandle(stdout_read.Detach(), 0)
        self.stdout_reader = Thread(target=self._child_reader,
                                    args=(self.stdout_fd,))
        self.stdout_reader.start()
        self.stderr_fd = open_osfhandle(stderr_read.Detach(), 0)
        self.stderr_reader = Thread(target=self._child_reader,
                                    args=(self.stderr_fd,))
        self.stderr_reader.start()
        self.terminated = False
        self.closed = False

    def terminate(self):
        """Terminate the child process. This also closes all the file
        descriptors."""
        if self.child_handle is None or not self.isalive():
            return
        TerminateProcess(self.child_handle, 1)
        self.close()
        self.wait()
        self.terminated = True

    def close(self):
        """Close all communications channels with the child."""
        if self.closed:
            return
        os.close(self.child_fd)
        os.close(self.stdout_fd)
        os.close(self.stderr_fd)
        # File descriptors are closed, nothing can be added to the queue
        # anymore. Empty it in case a thread was blocked on put().
        while self.child_output.qsize():
            self.child_output.get()
        # Now the threads are ready to be joined.
        self.stdout_reader.join()
        self.stderr_reader.join()
        self.closed = True

    def wait(self, timeout=None):
        """Wait until the child exits. If timeout is not specified this blocks
        indefinately. Otherwise, timeout specifies the number of seconds to wait."""
        if self.exitstatus is not None:
            return
        if timeout is None:
            timeout = INFINITE
        else:
            timeout = 1000 * timeout
        ret = WaitForSingleObject(self.child_handle, timeout)
        if ret == WAIT_TIMEOUT:
            raise TIMEOUT, 'Timeout exceeded in wait().'
        self.exitstatus = GetExitCodeProcess(self.child_handle)
        return self.exitstatus

    def isalive(self):
        """Return True if the child is alive, False otherwise."""
        if self.exitstatus is not None:
            return False
        ret = WaitForSingleObject(self.child_handle, 0)
        if ret == WAIT_OBJECT_0:
            self.exitstatus = GetExitCodeProcess(self.child_handle)
            return False
        return True

    def kill(self, signo):
        """Send a signal to the child (not available on Windows)."""
        raise ExceptionPexpect, 'Signals are not availalbe on Windows'

    def _child_reader(self, fd):
        """INTERNAL: Reader thread that reads stdout/stderr of the child process."""
        status = 'data'
        while True:
            try:
                data = os.read(fd, self.maxread)
                if data == '':
                    status = 'eof'
            except OSError, e:
                data = e.errno
                status = 'error'
            self.child_output.put((fd, status, data))
            if status != 'data':
                break

    def _set_eof(self, fd):
        """INTERNAL: mark a file descriptor as end-of-file."""
        if fd == self.stdout_fd:
            self.stdout_eof = True
        elif fd == self.stderr_fd:
            self.stderr_eof = True

    def read_nonblocking(self, size=1, timeout=-1):
        """Non blocking read."""
        if len(self.chunk_buffer):
            return self.chunk_buffer.read(size)
        if self.stdout_eof and self.stderr_eof:
            assert self.child_output.qsize() == 0
            return ''
        if timeout == -1:
            timeout = self.timeout
        try:    
            fd, status, data = self.child_output.get(timeout=timeout)
        except Empty:
            raise TIMEOUT, 'Timeout exceeded in read_nonblocking().'
        if status == 'data':
            self.chunk_buffer.add(data)
        elif status == 'eof':
            self._set_eof(fd)
            raise EOF, 'End of file in read_nonblocking().'
        elif status == 'error':
            self._set_eof(fd)
            raise OSError, data
        return self.chunk_buffer.read(size)
