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
The ``ci_exec`` package top-level namespace.

Quick Reference:

.. coresummary::
"""

# Import the core utilities in the ci_exec "namespace" for simpler imports.
from .colorize import Ansi, Colors, Styles, colorize, log_stage
from .core import Executable, fail, mkdir_p, rm_rf, which
from .parsers import CMakeParser
from .patch import filter_file, unified_diff
from .provider import Provider
from .utils import cd, merge_kwargs, set_env, unset_env

__version__ = "0.1.2"
__all__ = [
    # Core imports from ci_exec.colorize module.
    "Ansi", "Colors", "Styles", "colorize", "log_stage",
    # Core imports from ci_exec.core module.
    "Executable", "fail", "mkdir_p", "rm_rf", "which",
    # Core imports from ci_exec.parsers package.
    "CMakeParser",
    # Core imports from ci_exec.patch module.
    "filter_file", "unified_diff",
    # Core imports from ci_exec.provider module.
    "Provider",
    # Core imports from ci_exec.utils module.
    "cd", "merge_kwargs", "set_env", "unset_env"
]
