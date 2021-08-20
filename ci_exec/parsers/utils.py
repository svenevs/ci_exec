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
"""
Helper routines for any custom :mod:`ci_exec.parsers`.

In a nested module to avoid any circular import problems.
"""
import os
import platform


def env_or_platform_default(*, env: str, windows: str, darwin: str, other: str) -> str:
    """
    Return either the environment variable or the specified platform default.

    Convenience routine to check :func:`python:os.getenv` for ``env`` variable, and if
    not found check |system| and return the default.  Example::

        env_or_platform_default(env="CC", windows="cl.exe", darwin="clang", other="gcc")

    Only used to avoid writing the same conditional structure repeatedly.

    .. |system| replace:: :func:`python:platform.system`

    Parameters
    ----------
    env : str
        The environment variable to check for first.  If it is set in the environment,
        it will be returned.

    windows : str
        Returned if ``env`` not set, and |system| returns ``"Windows"``.

    darwin : str
        Returned if ``env`` not set and |system| returns ``"Darwin"``.

    other : str
        Returned if ``env`` not set and |system| is neither ``"Windows"`` nor
        ``"Darwin"``.
    """
    system = platform.system()
    if system == "Windows":
        default = windows
    elif system == "Darwin":
        default = darwin
    else:
        default = other

    val = os.getenv(env, None)
    if val is not None:
        return val

    return default
