########################################################################################
# Copyright 2019-2021 Stephen McDowell                                                 #
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
"""Various utilities for patching files."""

import difflib
import re
import shutil
from pathlib import Path
from typing import Callable, Match, Optional, Union

from .core import fail


def filter_file(path: Union[Path, str], pattern: str,
                repl: Union[Callable[[Match], str], str], count: int = 0,
                flags: int = 0, backup_extension: str = ".orig",
                line_based: bool = False, demand_different: bool = True,
                encoding: Optional[str] = None) -> Path:
    """
    Filter the contents of a file.

    1. Backup ``path`` to ``{path} + {backup_extension}``.  Typically, this would mean
       copying e.g., ``file.txt`` to ``file.txt.orig``.
    2. Perform filtering using :func:`python:re.sub`.
    3. If ``demand_different=True`` (default), verify that replacements were actually
       made.  If not, |fail|.

    The only required arguments are ``path``, ``pattern``, and ``repl``.  If any errors
    occur, including invalid input, this function will |fail|.

    .. |pass_through| replace:: Pass-through parameter to :func:`python:re.sub`.

    Parameters
    ----------
    path : pathlib.Path or str
        The file that needs to be filtered.

    pattern : str
        The pattern to replace.  |pass_through|

    repl : :any:`Callable[[Match], str] <python:typing.Callable>` or :class:`python:str`
        The replacement to be made.  |pass_through|

    count : int
        The number of replacements to make (default ``0`` means replace all).
        |pass_through|

    flags : int
        Any flags such as :data:`python:re.IGNORECASE` or :data:`python:re.MULTILINE`
        (default ``0`` means no special flags).  |pass_through|

    backup_extension : str
        The name to tack onto the back of ``path`` to make a backup with.  Must be a
        non-empty string.  Default: ``".orig"``.

    line_based : bool
        Whether or not replacements should be made on the entirety of the file, or on a
        per-line basis.  Default: ``False``, do :func:`python:re.sub` on the entire
        contents.  Setting ``line_based=True`` can make for simpler or more restrictive
        regular expressions depending on the replacement needed.

    demand_different : bool
        Whether or not this function should |fail| if no changes were actually made.
        Default: ``True``, |fail| if no filtering was performed.

    encoding : str or None
        The encoding to open files with.  Default: ``None`` implies default.
        Pass-through parameter to :func:`python:open`.

    Return
    ------
    pathlib.Path
        The path to the backup file that was created with the original contents.
    """
    if isinstance(path, str):
        path = Path(path)
    if not path.is_file():
        fail(f"Cannot filter '{str(path)}', no such file!")
    if backup_extension == "":
        fail("filter_file: 'backup_extension' may not be the empty string.")
    try:
        # Backup the original file before trying to filter.
        backup = Path(str(path) + backup_extension)
        shutil.copy(str(path), str(backup))

        # If doing line-based replacement, change access pattern.
        if line_based:
            orig_contents = None
            with backup.open(encoding=encoding) as orig_f:
                with path.open("w", encoding=encoding) as new_f:
                    for line in orig_f:
                        new_f.write(re.sub(
                            pattern, repl, line, count=count, flags=flags
                        ))
        else:
            # Gather the contents to be replaced.
            with backup.open(encoding=encoding) as orig_f:
                orig_contents = orig_f.read()

            # Do the replacement directly.
            with path.open("w", encoding=encoding) as new_f:
                new_f.write(re.sub(
                    pattern, repl, orig_contents, count=count, flags=flags
                ))

        # If requested (by default), make sure something actually changed.
        if demand_different:
            # In the line-based replacement we did not read the whole file at once.
            if not orig_contents:
                with backup.open(encoding=encoding) as orig_f:
                    orig_contents = orig_f.read()

            # Read in the file that may or may not have had changes applied.
            with path.open(encoding=encoding) as new_f:
                new_contents = new_f.read()

            # Enforce that the files are different ;)
            if orig_contents == new_contents:
                fail(f"filter_file: no changes made to '{str(path)}'")

        return backup
    except Exception as e:
        fail(f"Unable to filter '{str(path)}': {e}")


def unified_diff(from_path: Union[Path, str], to_path: Union[Path, str], n: int = 3,
                 lineterm: str = "\n", encoding: Optional[str] = None,
                 no_pygments: bool = False) -> str:
    r"""
    Return the :func:`unified_diff <difflib.unified_diff>` between two files.

    Any errors, such as not being able to read a file, will |fail| the application
    abruptly.

    Parameters
    ----------
    from_path : pathlib.Path or str
        The file to diff from (the "original" file).

    to_path : pathlib.Path or str
        The file to diff to (the "changed" file).

    n : int
        Number of context lines.  Default: ``3``.  Pass-through parameter to
        :func:`difflib.unified_diff`.

    lineterm : str
        Default: ``"\n"``.  Pass-through parameter to :func:`difflib.unified_diff`.

    encoding : str or None
        The encoding to open files with.  Default: ``None`` implies default.
        Pass-through parameter to :func:`python:open`.

    no_pygments : bool
        Whether or not an attempt to colorize the output using
        `Pygments <http://pygments.org/>`_ using the ``console`` formatter.  If Pygments
        is not installed, no errors will ensue.

        Default: ``False``, always try and make pretty output.  Set to ``True`` if you
        need to enforce that the returned string does not have colors.

    Return
    ------
    str
        A string ready to be printed to the console.
    """
    # Make sure we have paths we can work with.
    if isinstance(from_path, str):
        from_path = Path(from_path)
    if isinstance(to_path, str):
        to_path = Path(to_path)
    if not from_path.is_file():
        fail(f"unified_diff: from_path '{str(from_path)}' does not exist!")
    if not to_path.is_file():
        fail(f"unified_diff: to_path '{str(to_path)}' does not exist!")

    try:
        # difflib wants list of strings, read them in
        with from_path.open(encoding=encoding) as from_file:
            from_lines = from_file.readlines()
        with to_path.open(encoding=encoding) as to_file:
            to_lines = to_file.readlines()

        # Compute the unified diff <3
        diff_generator = difflib.unified_diff(
            from_lines, to_lines,
            fromfile=str(from_path), tofile=str(to_path),
            n=n, lineterm=lineterm
        )
        diff_text = "".join(diff_generator)

        # Pygments will turn empty string (no diff) into \n, quit now.
        if diff_text == "":
            return diff_text

        if not no_pygments:
            try:
                import pygments
                from pygments import lexers, formatters
                lex = lexers.find_lexer_class_by_name("diff")
                fmt = formatters.get_formatter_by_name("console")
                diff_text = pygments.highlight(diff_text, lex(), fmt)
            except:  # noqa: E722
                pass

        return diff_text
    except Exception as e:
        fail(f"unified_diff: unable to diff '{str(from_path)}' with "
             f"'{str(to_path)}': {e}")
