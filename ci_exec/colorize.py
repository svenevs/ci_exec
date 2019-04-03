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
"""Various utilities for colorizing terminal output."""

import shutil
from typing import Optional


class Ansi:
    """Wrapper class for defining the escape character and clear sequence."""

    Escape = "\033["
    """The opening escape sequence to use before inserting color / style."""

    Clear = "\033[0m"
    """Convenience definition used to clear ANSI formatting."""


class Styles:
    """
    A non-exhaustive list of ANSI style formats.

    The styles included here are reliable across many terminals, more exotic styles such
    as 'Blinking' are not included as they are not always supported.
    """

    Regular = "0m"
    """The regular ANSI format."""

    Bold = "1m"
    """The bold ANSI format."""

    Dim = "2m"
    """The dim ANSI format."""

    Underline = "4m"
    """The underline ANSI format."""

    Inverted = "7m"
    """The inverted ANSI format."""

    @classmethod
    def all_styles(cls) -> tuple:
        """Return a tuple of all style strings available (used in tests)."""
        return (
            Styles.Regular, Styles.Bold, Styles.Dim, Styles.Underline, Styles.Inverted
        )


class Colors:
    """The core ANSI color codes."""

    Black = "30"
    """The black ANSI color."""

    Red = "31"
    """The red ANSI color."""

    Green = "32"
    """The green ANSI color."""

    Yellow = "33"
    """The yellow ANSI color."""

    Blue = "34"
    """The blue ANSI color."""

    Magenta = "35"
    """The magenta ANSI color."""

    Cyan = "36"
    """The cyan ANSI color."""

    White = "37"
    """The white ANSI color."""

    @classmethod
    def all_colors(cls) -> tuple:
        """Return a tuple of all string colors available (used in tests)."""
        return (
            Colors.Black, Colors.Red, Colors.Green, Colors.Yellow, Colors.Blue,
            Colors.Magenta, Colors.Cyan, Colors.White
        )


def colorize(message: str, *, color: str, style: str=Styles.Regular) -> str:  # noqa: E252, E501
    """
    Return ``message`` colorized with specified style.

    Parameters
    ----------
    message : str
        The message to insert an :data:`Ansi.Escape` sequence with the specified color
        *before*, and :data:`Ansi.Clear` sequence after.

    color : str
        A string describing the ANSI color code to use, e.g., :data:`Colors.Red`.

        .. warning::

            The color is not validated.  Things like ``32m`` with the ``m`` afterward
            are unacceptable, and will produce gibberish.  This parameter is only the
            color code.

    style : str
        The ANSI style to use.  Default: :data:`Styles.Regular`.

    Returns
    -------
    str
        The original message with the specified color escape sequence.
    """
    return "{Escape}{color};{style}{message}{Clear}".format(
        Escape=Ansi.Escape,
        color=color,
        style=style,
        message=message,
        Clear=Ansi.Clear
    )


def log_stage(stage: str, *, fill_char: str="=", color: Optional[str]=Colors.Green,  # noqa: E252, E501
              style: str=Styles.Bold, width: Optional[int]=None, **kwargs):          # noqa: E252, E501
    """
    Print a terminal width block with ``stage`` message in the middle.

    Similar to the output of ``tox``, a bar of ``=== {stage} ===`` will be printed,
    adjusted to the width of the terminal.  For example::

        >>> log_stage("CMake.Configure")
        ======================== CMake.Configure ========================

    By default, this will be printed using ANSI bold green to make it stick out.  If the
    terminal size cannot be obtained, a width of ``44`` is assumed.  Specify ``width``
    if fixed width is desired.

    .. note::

        If the length of the ``stage`` parameter is too long (cannot pad with at least
        one ``fill_char`` and one space on both sides), the message with any coloring is
        printed as is.  Prefer shorter stage messages when possible.

    Parameters
    ----------
    stage : str
        The description of the build stage to print to the console.  This is the only
        required argument.

    fill_char : str
        A **length 1** string to use as the fill character.  Default: ``"="``.

        .. warning::

            No checks on the input are performed, but any non-length-1 string will
            produce unattractive results.

    color : str or None
        The ANSI color code to use with :func:`colorize`.  If no coloring is desired,
        call this function with ``color=None`` to disable.

    style : str
        The ANSI style specification to use with :func:`colorize`.  If no coloring is
        desired, leave this parameter as is and specify ``color=None``.

    width : int
        If specified, the terminal size will be ignored and a message formatted to this
        **positive** valued parameter will be used instead.  If the value is less than
        the length of the ``stage`` message, this parameter is ignored.

        .. note::

            The specified width here does not necessarily equal the length of the string
            printed.  The ANSI escape sequences added / trailing newline character will
            make the printed string longer than ``width``, but the perceived width
            printed to the terminal will be correct.

            That is, if logging to a file, you may also desire to set ``color=None`` to
            remove the ANSI escape sequences / achieve the actual desired width.

    **kwargs : dict
        If provided, ``**kwargs`` is forwarded to the :func:`python:print`.  E.g., to
        specify ``file=some_log_file_object`` rather than printing to
        :data:`python:sys.stdout`.
    """
    # Get desired width of output to format to.
    full_width = width or shutil.get_terminal_size(fallback=(44, 24)).columns

    # Compute usable areas to fill.
    space_width = len(stage) + 2  # Add space before / after message
    fill_width = full_width - space_width
    # If it's too long to add at least (fill_width - 1) / 2 fill_char's, just print the
    # message as is (as stated in docs, no fancy workarounds are created).
    if fill_width < 3:
        message = stage
    else:
        prefix_suffix = " "
        suffix_prefix = " "
        if fill_width % 2 == 0:
            fill = fill_char * (fill_width // 2)
        else:
            fill = fill_char * ((fill_width - 1) // 2)
            # Add an extra fill_char on suffix to fill screen.
            suffix_prefix = "{suffix_prefix}{fill_char}".format(
                suffix_prefix=suffix_prefix, fill_char=fill_char
            )

        # Create the full width message, colorize, and print.
        prefix = "{fill}{prefix_suffix}".format(fill=fill, prefix_suffix=prefix_suffix)
        suffix = "{suffix_prefix}{fill}".format(fill=fill, suffix_prefix=suffix_prefix)
        message = "{prefix}{stage}{suffix}".format(
            prefix=prefix, stage=stage, suffix=suffix
        )
    if color:
        message = colorize(message, color=color, style=style)
    print(message, **kwargs)
