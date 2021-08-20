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
"""Tests for the :mod:`ci_exec.parsers.utils` module."""

import platform

from ci_exec.parsers.utils import env_or_platform_default
from ci_exec.utils import set_env, unset_env


@unset_env("CC")
def test_env_or_platform_default():
    """
    Validate |env_or_platform_default| returns expected values for each platform.

    .. |env_or_platform_default| replace::

        :func:`~ci_exec.parsers.utils.env_or_platform_default`
    """
    kwargs = dict(
        env="CC",
        windows="cl.exe",
        darwin="clang",
        other="gcc"
    )
    cc = env_or_platform_default(**kwargs)
    system = platform.system()
    if system == "Windows":
        assert cc == "cl.exe"
    elif system == "Darwin":
        assert cc == "clang"
    else:
        assert cc == "gcc"

    with set_env(CC="supercompiler"):
        cc = env_or_platform_default(**kwargs)
        assert cc == "supercompiler"
