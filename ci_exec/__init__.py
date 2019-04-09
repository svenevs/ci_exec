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

"""This is a package that does things."""

# Import the core utilities in the ci_exec "namespace" for simpler imports.
from .colorize import Ansi, Colors, Styles, colorize, log_stage
from .core import Executable, fail, mkdir_p, rm_rf, which

__version__ = "0.1.0.dev"
__all__ = [
    "Ansi", "Colors", "Styles", "colorize", "log_stage",
    "Executable", "fail", "mkdir_p", "rm_rf", "which"
]
