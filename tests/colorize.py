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
"""Tests for the :mod:`ci_exec.colorize` module."""

import re
import shutil
import sys
from typing import Any, Dict, Optional

from ci_exec.colorize import Ansi, Colors, Styles, colorize, \
    dump_predefined_color_styles, log_stage

import pytest


def test_all_colors():
    """
    Validate |all_colors| returns all available colors.

    .. |all_colors| replace::

        :func:`Colors.all_colors <ci_exec.colorize.Colors.all_colors>`
    """
    reported_all_colors = Colors.all_colors()
    assert len(set(reported_all_colors)) == len(reported_all_colors)
    all_colors = set([
        item for key, item in Colors.__dict__.items() if key[0].isupper()
    ])
    assert set(reported_all_colors) == all_colors


def test_all_styles():
    """
    Validate |all_styles| returns all available styles.

    .. |all_styles| replace::

        :func:`Styles.all_styles <ci_exec.colorize.Styles.all_styles>`
    """
    reported_all_styles = Styles.all_styles()
    assert len(set(reported_all_styles)) == len(reported_all_styles)
    all_styles = set([
        item for key, item in Styles.__dict__.items() if key[0].isupper()
    ])
    assert set(reported_all_styles) == all_styles


@pytest.mark.parametrize(
    "color,style",
    [(c, s) for c in Colors.all_colors() for s in Styles.all_styles()]
)
def test_colorize(color: str, style: str):
    """Test |colorize| colors as expected for each platform."""
    message = "colors!"
    colored = colorize(message, color=color, style=style)

    if style == Styles.Regular:
        assert colored.startswith("{Escape}{color}m".format(
            Escape=Ansi.Escape, color=color
        ))
    else:
        assert colored.startswith("{Escape}{color};{style}m".format(
            Escape=Ansi.Escape, color=color, style=style
        ))
    assert colored.endswith("{Clear}".format(Clear=Ansi.Clear))
    assert message in colored


def test_dump_predefined_color_styles(capsys):
    """Validate :func:`~ci_exec.colorize.dump_predefined_color_styles` dumps all."""
    dump_predefined_color_styles()
    captured = capsys.readouterr()
    assert captured.err == ""

    # Collect the printed results.
    colors_seen = {}
    spec_regex = re.compile(r"color=([a-zA-Z]+), style=([a-zA-Z]+)")
    for match in spec_regex.finditer(captured.out):
        color, style = match.groups()
        if color in colors_seen:
            colors_seen[color].append(style)
        else:
            colors_seen[color] = [style]

    # Make sure every color in every style was presented.
    all_colors = Colors.all_colors()
    all_styles = set(Styles.all_styles())

    assert len(colors_seen) == len(all_colors)
    for color_name, style_names in colors_seen.items():
        # The style names are printed, get the values
        styles_seen = [getattr(Styles, style) for style in style_names]
        assert len(styles_seen) == len(style_names)
        assert set(styles_seen) == all_styles

        # Check the actual colors showed up.
        color = getattr(Colors, color_name)
        for style_name, style in zip(style_names, styles_seen):
            expected = colorize(
                "color={color_name}, style={style_name}".format(
                    color_name=color_name, style_name=style_name
                ),
                color=color,
                style=style
            )
            assert expected in captured.out


@pytest.mark.parametrize(
    # See: https://github.com/python/mypy/issues/5958
    # Setting via __kwdefaults__ isn't supported yet, so the {var}_ with the underscore
    # is a dirty hack to get around this in conjunction with type: ignore.
    "stage,fill_char_,pad_,l_pad_,r_pad_,color_,style_,width_",
    [
        # This is TOTAL overkill lol
        (stage, fill_char, pad, l_pad, r_pad, color, style, width)
        for stage in (
            "CMake.Configure", "M" * 44, "M" * 512
        )
        for fill_char in (None, "-")                      # default: "="
        for pad in (None, "")                             # default: " "
        for l_pad in (None, "_")                          # default: " "
        for r_pad in (None, "++")                         # default: " "
        for color in (None, Colors.Green, Colors.Cyan)    # default: Colors.Green
        for style in (Styles.Bold, Styles.Regular)        # default: Styles.Bold
        for width in (None, 44)                           # default: None
    ]
)
def test_log_stage(capsys, stage: str, fill_char_: Optional[str], pad_: Optional[str],
                   l_pad_: Optional[str], r_pad_: Optional[str], color_: Optional[str],
                   style_: str, width_: Optional[int]):
    """Test |log_stage| prints the expected messages."""
    # Setup call for log_stage as well as determine what the expected values are by
    # either using the parametrized argument or grabbing the default from log_stage.
    log_stage_kwargs = {}  # type: Dict[str, Any]
    if fill_char_ is not None:
        fill_char = fill_char_
        log_stage_kwargs["fill_char"] = fill_char
    else:
        fill_char = log_stage.__kwdefaults__["fill_char"]  # type: ignore

    if pad_ is not None:
        pad = pad_
        log_stage_kwargs["pad"] = pad
    else:
        pad = log_stage.__kwdefaults__["pad"]  # type: ignore

    if l_pad_ is not None:
        l_pad = l_pad_
        log_stage_kwargs["l_pad"] = l_pad
    else:
        l_pad = log_stage.__kwdefaults__["l_pad"]  # type: ignore

    if r_pad_ is not None:
        r_pad = r_pad_
        log_stage_kwargs["r_pad"] = r_pad
    else:
        r_pad = log_stage.__kwdefaults__["r_pad"]  # type: ignore

    color = color_
    if color_ != Colors.Green:  # use default color
        log_stage_kwargs["color"] = color

    style = style_
    if style_ != Styles.Bold:  # use default style
        log_stage_kwargs["style"] = style

    if width_ is not None:
        width = width_
        log_stage_kwargs["width"] = width
    else:
        width = log_stage.__kwdefaults__["width"]  # type: ignore

    ####################################################################################
    # Same code as implementation ... no good way to abstract.                         #
    # Expected width of output format.                                                 #
    full_width = width or shutil.get_terminal_size().columns                           #
    #                                                                                  #
    # Setup the default padding scenarios.                                             #
    if l_pad is None:                                                                  #
        l_pad = pad                                                                    #
    if r_pad is None:                                                                  #
        r_pad = pad                                                                    #
    #                                                                                  #
    # Compute usable areas to fill.                                                    #
    pad_width = len(l_pad) + len(r_pad)                                                #
    stage_width = len(stage) + pad_width                                               #
    fill_width = full_width - stage_width                                              #
    ####################################################################################

    def verify_all(colored_output: str):
        """Validate all parameters from the specified (maybe) colorized output."""
        # Remove trailing \n to make comparisons easier.
        colored_output = colored_output.strip()

        # Test coloring / style (do first to create un-colored version to test others).
        if color is not None:
            ansi_color, ansi_clear = colorize("!", color=color, style=style).split("!")
            assert colored_output.startswith(ansi_color)
            assert colored_output.endswith(ansi_clear)
            assert color in colored_output
            if style is not None:
                assert style in colored_output
        else:
            ansi_color, ansi_clear = "", ""
            assert Ansi.Escape not in colored_output
            assert Ansi.Clear not in colored_output

        # Create uncolored version to make later tests easier.
        stripped_out = colored_output.replace(ansi_color, "").replace(ansi_clear, "")

        # Need at least (fill_width - 1) / 2 available.
        if fill_width < 3:
            fill = None
        else:
            if fill_width % 2 == 0:
                fill = fill_char * (fill_width // 2)
            else:
                fill = fill_char * ((fill_width - 1) // 2)

        # Verify the expected fill was used.
        if fill is not None:
            assert colored_output.count(fill) == 2
        else:
            assert fill_char not in colored_output

        # Verify the padding specified is used.
        if fill is not None:
            l_fill, r_fill = stripped_out.split(stage)
            assert l_pad == l_fill.split(fill)[-1]
            assert r_pad == r_fill.split(fill)[0]
        else:
            if l_pad != "":
                assert l_pad not in stripped_out
            if r_pad != "":
                assert r_pad not in stripped_out
            assert stripped_out == stage

        # Verify the width is as expected.
        expected_width = len(ansi_color) + len(stage) + len(ansi_clear)
        if fill is not None:
            expected_width += (len(fill) * 2) + len(l_pad) + len(r_pad)
            if fill_width % 2 != 0:
                expected_width += len(fill_char)
        assert len(colored_output) == expected_width
        if fill_width >= 3:
            assert len(stripped_out) == full_width
        else:
            assert stripped_out == stage

    # Test with the default `print` command.
    log_stage(stage, **log_stage_kwargs)
    captured = capsys.readouterr()
    orig_out = "{out}".format(out=captured.out)  # stash for comparing with next test
    assert captured.err == ""
    verify_all(captured.out)

    # Verify that **kwargs passed to print work as expected.  Print to sys.stderr and
    # don't include trailing newline.
    log_stage(stage, **log_stage_kwargs, file=sys.stderr, end="")
    captured = capsys.readouterr()
    assert captured.out == ""
    verify_all(captured.err)
    assert captured.err == orig_out.replace("\n", "")
