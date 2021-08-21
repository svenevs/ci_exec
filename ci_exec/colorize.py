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
"""Various utilities for colorizing terminal output."""

import shutil
from typing import Optional


class Ansi:
    """Wrapper class for defining the escape character and clear sequence."""

    Escape = "\033["
    """The opening escape sequence to use before inserting color / style."""

    Clear = "\033[0m"
    """Convenience definition used to clear ANSI formatting."""


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


class Styles:
    """
    A non-exhaustive list of ANSI style formats.

    The styles included here are reliable across many terminals, more exotic styles such
    as 'Blinking' are not included as they often are not supported.
    """

    Regular = ""
    """The regular ANSI format."""

    Bold = "1"
    """The bold ANSI format."""

    Dim = "2"
    """The dim ANSI format."""

    Underline = "4"
    """The underline ANSI format."""

    Inverted = "7"
    """The inverted ANSI format."""

    BoldUnderline = "1;4"
    """Bold and underlined ANSI format."""

    BoldInverted = "1;7"
    """Bold and inverted ANSI format."""

    BoldUnderlineInverted = "1;4;7"
    """Bold, underlined, and inverted ANSI format."""

    DimUnderline = "2;4"
    """Dim and underlined ANSI format."""

    DimInverted = "2;7"
    """Dim and inverted ANSI format."""

    DimUnderlineInverted = "2;4;7"
    """Dim, underlined, and inverted ANSI format."""

    @classmethod
    def all_styles(cls) -> tuple:
        """Return a tuple of all style strings available (used in tests)."""
        return (
            Styles.Regular, Styles.Bold, Styles.Dim, Styles.Underline, Styles.Inverted,
            Styles.BoldUnderline, Styles.BoldInverted, Styles.BoldUnderlineInverted,
            Styles.DimUnderline, Styles.DimInverted, Styles.DimUnderlineInverted
        )


def colorize(message: str, *, color: str, style: str = Styles.Regular) -> str:
    """
    Return ``message`` colorized with specified style.

    .. warning::

        For both the ``color`` and ``style`` parameters, these are not supposed to have
        the ``m`` after.  For example, a ``color="32m"`` is invalid, it should just be
        ``"32"``.  Similarly, a ``style="1m"`` is invalid, it should just be ``"1"``.

    Parameters
    ----------
    message : str
        The message to insert an :data:`Ansi.Escape` sequence with the specified color
        *before*, and :data:`Ansi.Clear` sequence after.

    color : str
        A string describing the ANSI color code to use, e.g., :data:`Colors.Red`.

    style : str
        The ANSI style to use.  Default: :data:`Styles.Regular`.  Note that any number
        of ANSI style specifiers may be used, but it is assumed that the user has
        already formed the semicolon delineated list.  For multiple ANSI specifiers,
        see for example :data:`Styles.BoldUnderline`.  Semicolons should be on the
        interior separating each style.

    Returns
    -------
    str
        The original message with the specified color escape sequence.
    """
    prefix = f"{Ansi.Escape}{color}"
    # Regular: `m` goes right after color without `;`
    if style != "":
        if not style.startswith(";"):
            prefix += ";" + style
    prefix += "m"

    return f"{prefix}{message}{Ansi.Clear}"


def dump_predefined_color_styles():
    """Dump all predefined |Colors| in every |Styles| to the console."""
    for c_key in Colors.__dict__.keys():
        if not c_key[0].isupper():
            continue
        color = getattr(Colors, c_key)
        for s_key in Styles.__dict__.keys():
            if not s_key[0].isupper():
                continue
            style = getattr(Styles, s_key)

            print(colorize(f"color={c_key}, style={s_key}", color=color, style=style))


def log_stage(stage: str, *, fill_char: str = "=", pad: str = " ",
              l_pad: Optional[str] = None, r_pad: Optional[str] = None,
              color: Optional[str] = Colors.Green, style: str = Styles.Bold,
              width: Optional[int] = None, **kwargs):
    """
    Print a terminal width block with ``stage`` message in the middle.

    Similar to the output of ``tox``, a bar of ``=== {stage} ===`` will be printed,
    adjusted to the width of the terminal.  For example::

        >>> log_stage("CMake.Configure")
        ======================== CMake.Configure ========================

    By default, this will be printed using ANSI bold green to make it stick out.  If the
    terminal size cannot be obtained, a width of ``80`` is assumed.  Specify ``width``
    if fixed width is desired.

    .. note::

        If the length of the ``stage`` parameter is too long (cannot pad with at least
        one ``fill_char`` and the specified padding both sides), the message with any
        coloring is printed as is.  Prefer shorter stage messages when possible.

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

    pad : str
        A padding to insert both before and after ``stage``.  Default: ``" "``.  This
        value can be any length, but may **not** be ``None``.  If no padding is desired,
        use the empty string ``""``.  Some examples::

            >>> log_stage("CMake.Configure")
            ============================= CMake.Configure ==============================
            >>> log_stage("CMake.Configure", fill_char="_", pad="")
            ______________________________CMake.Configure_______________________________

        See also: ``l_pad`` and ``r_pad`` if asymmetrical patterns are desired.

    l_pad : str or None
        A padding to insert before the ``stage`` (on the left).  Default: ``None``
        (implies use value from ``pad`` parameter).  See examples in ``r_pad`` below.

    r_pad : str or None
        A padding to insert after the ``stage`` (on the right).  Default: ``None``
        (implies use value from ``pad`` parameter).  Some examples::

            >>> log_stage("CMake.Configure", fill_char="-", l_pad="+ ", r_pad=" +")
            ----------------------------+ CMake.Configure +-----------------------------
            # Without specifying r_pad, pad is used (default: " ")
            >>> log_stage("CMake.Configure", fill_char="-", l_pad="+ ")
            -----------------------------+ CMake.Configure -----------------------------

    color : str or None
        The ANSI color code to use with |colorize|.  If no coloring is desired, call
        this function with ``color=None`` to disable.

    style : str
        The ANSI style specification to use with |colorize|.  If no coloring is desired,
        leave this parameter as is and specify ``color=None``.

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

    **kwargs
        If provided, ``**kwargs`` is forwarded to the :func:`python:print`.  E.g., to
        specify ``file=some_log_file_object`` or ``file=sys.stderr`` rather than
        printing to :data:`python:sys.stdout`.
    """
    # Get desired width of output to format to.
    full_width = width or shutil.get_terminal_size().columns

    if l_pad is None:
        l_pad = pad
    if r_pad is None:
        r_pad = pad

    # Compute usable areas to fill.
    pad_width = len(l_pad) + len(r_pad)
    stage_width = len(stage) + pad_width
    fill_width = full_width - stage_width
    # If it's too long to add at least (fill_width - 1) / 2 fill_char's, just print the
    # message as is (as stated in docs, no fancy workarounds are created).
    if fill_width < 3:
        message = stage
    else:
        prefix_suffix = l_pad
        suffix_prefix = r_pad
        if fill_width % 2 == 0:
            fill = fill_char * (fill_width // 2)
        else:
            fill = fill_char * ((fill_width - 1) // 2)
            # Add an extra fill_char on suffix to fill screen.
            suffix_prefix = f"{suffix_prefix}{fill_char}"

        # Create the full width message, colorize, and print.
        prefix = f"{fill}{prefix_suffix}"
        suffix = f"{suffix_prefix}{fill}"
        message = f"{prefix}{stage}{suffix}"
    if color:
        message = colorize(message, color=color, style=style)
    print(message, **kwargs)
