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
:mod:`python:argparse` derivatives tailored to specific build systems.

If you would like to contribute a generic parser for a build system, the pull request
shall add the following:

1. Add file ``ci_exec/parsers/{build_system}_parser.py`` with the implementation.
2. Add file ``tests/parsers/{build_system}_parser.py`` with the tests.
3. Add a top-level import to ``ci_exec/parsers/__init__.py`` (keep alphabetical).
4. Update the top-level imports for ``parsers`` in ``ci_exec/__init__.py``.
5. Add ``docs/source/api/parsers/{build_system}.rst`` and update the ``toctree``
   directive in ``docs/source/api/parsers.rst`` (keep alphabetical).

When contributing a custom parser, please do your best to make it as generic as possible
to support as wide an audience as is reasonably possible.  If "arbitrary" decisions need
to be made, please document them clearly and allow them to be overriden.

Lastly, by contributing a build system parser, you agree to being CC'd via a GitHub
``@`` mention for any issues that may arise with the parser.  In other words, please
help me maintain the new parser being added 🙂
"""
from .cmake_parser import CMakeParser

__all__ = [
    "CMakeParser"
]
