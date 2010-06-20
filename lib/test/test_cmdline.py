#
# This file is part of WinPexpect. WinPexpect is free software that is made
# available under the MIT license. Consult the file "LICENSE" that is
# distributed together with this file for the exact licensing terms.
#
# WinPexpect is copyright (c) 2008-2010 by the WinPexpect authors. See the
# file "AUTHORS" for a complete overview.

import os
from winpexpect import split_command_line, join_command_line

from nose.tools import assert_raises


class TestCommandLine(object):

    split_ok = [
        ('a b c', ['a', 'b', 'c']),
        ('"a b c" d e', ['a b c', 'd', 'e']),
        (r'"ab\"c" "\\" d', ['ab"c', '\\', 'd']),
        (r'a\\\b d"e f"g h', [r'a\\\b', 'de fg', 'h']),
        (r'a\\\"b c d', [r'a\"b', 'c', 'd']),
        (r'a\\\\"b c" d e', [r'a\\b c', 'd', 'e']),
        ('""', ['']),
        ('"" ""', ['', '']),
        (' ', []),
        ('  ', []),
        (' a', ['a']),
        ('a ', ['a']),
        (' a ', ['a']),
        ('"  a"', ['  a'])
    ]

    split_error = [
        '"a',
        'a"b',
        '"'
    ]

    def test_split(self):
        for s,ref in self.split_ok:
            assert split_command_line(s) == ref

    def test_split_error(self):
        for s in self.split_error:
            assert_raises(ValueError, split_command_line, s)

    join_ok = [
        (['a'], 'a'),
        (['a', 'b'], 'a b'),
        (['a b'], '"a b"'),
        (['a|b'], '"a|b"'),
        (['a"b'], r'a\"b'),
        ([r'a\b'], r'a\b'),
        ([r'a\"b'], r'a\\\"b'),
        ([r'"a\"b"'], r'\"a\\\"b\"'),
        ([r'"a\" b"'], r'"\"a\\\" b\""')
    ]

    def test_join(self):
        for l,ref in self.join_ok:
            assert join_command_line(l) == ref
