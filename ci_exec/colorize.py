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

import platform


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
        """Return a tuple of all style strings available (used in testing)."""
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
        """Return a tuple of all string colors available (used in testing)."""
        return (
            Colors.Black, Colors.Red, Colors.Green, Colors.Yellow, Colors.Blue,
            Colors.Magenta, Colors.Cyan, Colors.White
        )


def colorize(message: str, *, color: str, style: str=Styles.Regular, force: bool=False) -> str:  # noqa: E252, E501
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

    force : bool
        If :func:`python:platform.system` returns ``"Windows"``, the original message is
        not escaped with color codes.  This is to accomodate that some Windows CI
        providers will remove any lines of text that have color escape sequences.

        The default value is ``False``, set to ``True`` if color sequences are always
        desired.

    Returns
    -------
    str
        The original message with the specified color escape sequence, unless the
        platform is ``"Windows"`` (see ``force`` parameter).
    """
    if platform.system() == "Windows" and not force:
        return message

    return "{Escape}{color};{style}{message}{Clear}".format(
        Escape=Ansi.Escape,
        color=color,
        style=style,
        message=message,
        Clear=Ansi.Clear
    )


def log_build_stage(stage: str, *, force_color: bool=False):  # noqa: E252
    """
    Print ``stage`` with ``"==> "`` prefixed in ANSI bold green.

    Simply calls :func:`python:print` with a :func:`colorize`'d prefix.  It's utility is
    for making finding stages in the build log output easier to find (just search for
    the bright green ``"==> "``).

    Parameters
    ----------
    stage : str
        The description of the build stage to print to the console.

    force_color : bool
        Whether or not color should be forced.  Default: ``False`` (some Windows CI
        providers seem to remove all lines with color sequences).
    """
    prefix = colorize("==> ", color=Colors.Green, style=Styles.Bold, force=force_color)
    print("{prefix}{stage}".format(prefix=prefix, stage=stage))
