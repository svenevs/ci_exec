########################################################################################
# Copyright 2019 Stephen McDowell                                                      #
#                                                                                      #
# Licensed under the Apache License, Version 2.0 (the "License");                      #
# you may not use this file except in compliance with the License.                     #
# You may obtain a copy of the License at                                              #
#                                                                                      #
#     http://www.apache.org/licenses/LICENSE-2.0                                       #
#                                                                                      #
# Unless required by applicable law or agreed to in writing, software                  #
# distributed under the License is distributed on an "AS IS" BASIS,                    #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.             #
# See the License for the specific language governing permissions and                  #
# limitations under the License.                                                       #
########################################################################################
"""Tests for the :mod:`ci_exec.patch` module."""

import textwrap
from pathlib import Path
from typing import Tuple

from ci_exec.colorize import Colors, Styles, colorize
from ci_exec.core import mkdir_p, rm_rf
from ci_exec.patch import filter_file, unified_diff

import pytest


_please_stop = textwrap.dedent('''
    cmake_minimum_required(VERSION 3.14 FATAL_ERROR)
    project(super_project)
    export(PACKAGE super_project)
    message(STATUS "PLEASE STOP DOING export(PACKAGE)!")
    message(STATUS "At the very least, give us an option() to stop it!")
''')
"""Dummy contents for testing replacements."""


def _make_dummy() -> Tuple[Path, Path]:
    """Create filter_town and CMakeLists.txt, return the paths."""
    filter_town = Path(".").resolve() / "filter_town"
    rm_rf(filter_town)
    mkdir_p(filter_town)
    cmake_lists_txt = filter_town / "CMakeLists.txt"
    with cmake_lists_txt.open("w") as cml:
        cml.write(_please_stop)
    return (filter_town, cmake_lists_txt)


def test_filter_file(capsys):
    """Validate that |filter_file| patches / errors as expected."""
    # Non-existent files cannot be patched.
    with pytest.raises(SystemExit):
        filter_file("i_dont_exist", "boom", "blam")
    red_x = colorize("[X] ", color=Colors.Red, style=Styles.Bold)
    captured = capsys.readouterr()
    assert captured.out == ""
    err = f"{red_x}Cannot filter 'i_dont_exist', no such file!"
    assert captured.err.strip() == err

    # Backup extension must not be empty string.
    with pytest.raises(SystemExit):
        filter_file("tox.ini", "boom", "blam", backup_extension="")
    captured = capsys.readouterr()
    assert captured.out == ""
    err = f"{red_x}filter_file: 'backup_extension' may not be the empty string."
    assert captured.err.strip() == err

    def read_both(cml: Path, bku: Path) -> Tuple[str, str]:
        """Open and read both files, returning the results."""
        with cml.open() as cml_f:
            cml_contents = cml_f.read()
        with bku.open() as bku_f:
            bku_contents = bku_f.read()
        return (cml_contents, bku_contents)

    for line_based in (True, False):
        # Filtering nothing should error.
        filter_town, cmake_lists_txt = _make_dummy()
        with pytest.raises(SystemExit):
            filter_file(cmake_lists_txt, "", "", line_based=line_based)
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "filter_file: no changes made to '" in captured.err
        assert "CMakeLists.txt'" in captured.err

        # Invalid replacement should trigger failure.
        filter_town, cmake_lists_txt = _make_dummy()
        with pytest.raises(SystemExit):
            filter_file(cmake_lists_txt, "export", lambda x: 11, line_based=line_based)
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err.startswith(f"{red_x}Unable to filter")
        assert "expected str instance, int found" in captured.err

        # No filtering with demand_different=False should not error.
        filter_town, cmake_lists_txt = _make_dummy()
        backup = filter_file(
            cmake_lists_txt, "", "", demand_different=False, line_based=line_based
        )
        cml, bku = read_both(cmake_lists_txt, backup)
        assert cml == bku

        # Test an actual patch.
        filter_town, cmake_lists_txt = _make_dummy()
        backup = filter_file(
            cmake_lists_txt, "super_project", "SUPER_PROJECT", line_based=line_based
        )
        cml, bku = read_both(cmake_lists_txt, backup)
        assert cml != bku
        assert bku == _please_stop
        assert cml == _please_stop.replace("super_project", "SUPER_PROJECT")

    # Cleanup
    rm_rf(filter_town)


def test_unified_diff(capsys):
    """Validate that |unified_diff| diffs / errors as expected."""
    # Invalid from_file should exit.
    with pytest.raises(SystemExit):
        unified_diff("i_am_not_here", "tox.ini")
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "unified_diff: from_path 'i_am_not_here' does not exist!" in captured.err

    # Invalid to_file should exit.
    with pytest.raises(SystemExit):
        unified_diff("tox.ini", "i_am_not_here")
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "unified_diff: to_path 'i_am_not_here' does not exist!" in captured.err

    # Diff between a file and itself should result in the empty string.
    empty = unified_diff("tox.ini", "tox.ini")
    assert empty == ""

    # Do some diffing.
    expected_diff_template = textwrap.dedent('''\
        --- {backup}
        +++ {cmake_lists_txt}
        @@ -1,6 +1,6 @@

         cmake_minimum_required(VERSION 3.14 FATAL_ERROR)
         project(super_project)
        -export(PACKAGE super_project)
        +# export(PACKAGE super_project)
         message(STATUS "PLEASE STOP DOING export(PACKAGE)!")
         message(STATUS "At the very least, give us an option() to stop it!")
    ''').replace("@@\n\n cmake", "@@\n \n cmake")
    # NOTE:       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ this took a while to figure out xD
    # looking at diff of diff in tox output was very confusing hehehe.

    def filter_diff(no_pygments):
        filter_town, cmake_lists_txt = _make_dummy()
        backup = filter_file(
            cmake_lists_txt,
            r"^(\s*export\s*\(PACKAGE.*\).*)$", r"# \1",
            line_based=True
        )
        diff = unified_diff(backup, cmake_lists_txt, no_pygments=no_pygments)
        expected_diff = expected_diff_template.format(
            backup=str(backup), cmake_lists_txt=str(cmake_lists_txt)
        )
        return (diff, expected_diff)

    for no_pygments in (True, False):
        diff, expected_diff = filter_diff(no_pygments)
        if no_pygments:
            assert diff == expected_diff
        else:
            import pygments
            from pygments import lexers, formatters
            lex = lexers.find_lexer_class_by_name("diff")
            fmt = formatters.get_formatter_by_name("console")
            assert diff == pygments.highlight(expected_diff, lex(), fmt)

    # Force in an error just for shiggles (and because we can).
    def superfail(*args, **kwargs):
        raise ValueError("superfail")
    lexers.find_lexer_class_by_name = superfail

    # Attempt to call pygments code now that this raises.  Result: original text.
    diff, expected_diff = filter_diff(False)
    assert diff == expected_diff

    # Lastly, make sure the catch-all exception prints the expected message.
    import difflib
    difflib.unified_diff = superfail
    with pytest.raises(SystemExit):
        unified_diff("tox.ini", "tox.ini")
    captured = capsys.readouterr()
    assert captured.out == ""
    expected = "unified_diff: unable to diff 'tox.ini' with 'tox.ini': superfail"
    assert captured.err.strip().endswith(expected)

    # Cleanup.
    filter_town, cmake_lists_txt = _make_dummy()
    rm_rf(filter_town)
