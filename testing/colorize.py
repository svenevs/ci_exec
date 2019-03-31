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

import platform

from ci_exec.colorize import Ansi, Colors, Styles, colorize, log_build_stage

import pytest


def always_colorize(message: str, color: str, style: str) -> str:
    """Identical to :func:`ci_exec.colorize.colorize` without platform checks."""
    return "{Escape}{color};{style}{message}{Clear}".format(
        Escape=Ansi.Escape,
        color=color,
        style=style,
        message=message,
        Clear=Ansi.Clear
    )


@pytest.mark.parametrize(
    "color,style",
    [(c, s) for c in Colors.all_colors() for s in Styles.all_styles()]
)
def test_colorize(color: str, style: str):
    """Test :func:`~ci_exec.colorize.colorize` colors as expected for each platform."""
    message = "colors!"
    maybe_colored = colorize(message, color=color, style=style)
    force_colored = colorize(message, color=color, style=style, force=True)
    colored = always_colorize(message, color, style)

    # On Windows the default is not to force color in.
    if platform.system() == "Windows":
        assert maybe_colored == message
    else:
        assert maybe_colored == colored

    # Regardless of platform...forced is forced.
    assert force_colored == colored


@pytest.mark.parametrize(
    "stage,force_color",
    [
        (stage, force)
        # In the ideal world right? Hehe.
        for stage in ["CMake.Configure", "CMake.Build", "CMake.Test", "CMake.Install"]
        for force in [False, True]
    ]
)
def test_log_build_stage(capsys, stage: str, force_color: bool):
    """Test :func:`~ci_exec.colorize.log_build_stage` prints the expected messages."""
    log_build_stage(stage, force_color=force_color)
    prefix = colorize("==> ", color=Colors.Green, style=Styles.Bold, force=force_color)
    expected = "{prefix}{stage}\n".format(prefix=prefix, stage=stage)
    captured = capsys.readouterr()
    assert captured.out == expected
    assert captured.err == ""
