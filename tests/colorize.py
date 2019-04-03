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

import shutil
import sys
from typing import Any, Dict, Optional

from ci_exec.colorize import Ansi, Colors, Styles, colorize, log_stage

import pytest


@pytest.mark.parametrize(
    "color,style",
    [(c, s) for c in Colors.all_colors() for s in Styles.all_styles()]
)
def test_colorize(color: str, style: str):
    """Test :func:`~ci_exec.colorize.colorize` colors as expected for each platform."""
    message = "colors!"
    colored = colorize(message, color=color, style=style)

    assert colored.startswith("{Escape}{color};{style}".format(
        Escape=Ansi.Escape, color=color, style=style
    ))
    assert colored.endswith("{Clear}".format(Clear=Ansi.Clear))
    assert message in colored


@pytest.mark.parametrize(
    "stage,fill_char,color,style,width",
    [
        # This is TOTAL overkill lol
        (stage, fill_char, color, style, width)
        # In the ideal world right? Hehe.
        for stage in (
            "CMake.Configure", "CMake.Build", "CMake.Test", "CMake.Install",
            # These are for testing the "phase message too long" scenarios.
            "M" * 42, "M" * 44, "M" * 256
        )
        for fill_char in (None, "-", "_")
        for color in (None, Colors.Green, Colors.Cyan, Colors.Magenta)
        for style in (Styles.Regular, Styles.Bold, Styles.Inverted)
        for width in (None, 44, 88)
    ]
)
def test_log_stage(capsys, stage: str, fill_char: str, color: Optional[str], style: str,
                   width: Optional[int]):
    """Test :func:`~ci_exec.colorize.log_stage` prints the expected messages."""
    log_stage_kwargs = {}  # type: Dict[str, Any]
    if fill_char is not None:
        log_stage_kwargs["fill_char"] = fill_char
    if color != Colors.Green:  # Default is Green
        log_stage_kwargs["color"] = color
    if style != Styles.Bold:  # Default is Bold
        log_stage_kwargs["style"] = style
    if width is not None:
        log_stage_kwargs["width"] = width

    # Get the expected width of the output message (ignoring colors).
    full_width = width or shutil.get_terminal_size(fallback=(44, 24)).columns
    if color is not None:
        ansi_color, ansi_clear = colorize("!", color=color, style=style).split("!")
    else:
        ansi_color, ansi_clear = "", ""

    # Test with the default `print` command.
    log_stage(stage, **log_stage_kwargs)
    captured = capsys.readouterr()
    orig_out = "{out}".format(out=captured.out)  # Save for test against stderr below.
    fill_width = full_width - (len(stage) + 2)  # Spaces added before / after {stage}

    if fill_width < 3:
        expected_length = len(stage)
    else:
        expected_length = full_width
    expected_length += len(ansi_color) + len(ansi_clear) + 1  # +1: \n
    assert len(captured.out) == expected_length
    assert captured.out.startswith(ansi_color)
    assert captured.out.endswith("{ansi_clear}\n".format(ansi_clear=ansi_clear))
    assert len(captured.err) == 0

    # Also verify the computed fill is correct.
    the_fill_char = fill_char or "="  # Default fill_char: "="
    if fill_width < 3:
        # The tests for this are long strings of MMMMMM, no spaces, no fill_char
        assert the_fill_char not in captured.out
        assert " " not in captured.out
    else:
        prefix, suffix = captured.out.split(" {stage} ".format(stage=stage))
        prefix = prefix.replace(ansi_color, "")
        suffix = suffix.replace(ansi_clear, "").rstrip()
        if fill_width % 2 == 0:
            fill = the_fill_char * (fill_width // 2)
            assert prefix == fill
            assert suffix == fill
        else:
            fill = the_fill_char * ((fill_width - 1) // 2)
            assert prefix == fill
            assert suffix == (the_fill_char + fill)

    # Verify that **kwargs passed to print work as expected.  Print to sys.stderr and
    # don't include trailing newline.
    log_stage(stage, **log_stage_kwargs, file=sys.stderr, end="")
    captured = capsys.readouterr()
    assert len(captured.out) == 0
    assert orig_out.replace("\n", "") == captured.err
