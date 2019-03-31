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
"""The core functionality of the ``ci_exec`` package."""

import sys

from .colorize import Colors, Styles, colorize


def fail(why: str, *, exit_code: int=1, no_prefix: bool=False):  # noqa: E252
    """
    Write a failure message to :data:`python:sys.stderr` and exit.

    **Parameters**

    ``why`` (:class:`python:str`)
        The message explaining why the program is being failed out.

    ``exit_code`` (:class:`python:int`)
        The exit code to use.  Default: ``1``.

    ``no_prefix`` (:class:`python:bool`)
        Whether to prefix a bold red ``[X] `` before ``why``.  Default: ``False``, the
        bold red ``[X] `` prefix is included unless set to ``True``.
    """
    if no_prefix:
        prefix = ""
    else:
        prefix = colorize("[X] ", color=Colors.Red, style=Styles.Bold)
    sys.stderr.write("{prefix}{why}\n".format(prefix=prefix, why=why))
    sys.exit(exit_code)


class Executable:  # noqa: D101
    pass


def which():  # noqa: D103
    pass


def mkdir():  # noqa: D103
    pass


def rmtree():  # noqa: D103
    pass
