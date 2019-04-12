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
"""
Assorted utility functions.

This module aims to house any utility functions that may facilitate easier consumption
of the ``ci_exec`` package.
"""

import os
from contextlib import ContextDecorator
from pathlib import Path
from typing import Union

from .core import fail, mkdir_p


class cd(ContextDecorator):  # noqa: N801
    """
    Context manager / decorator that can be used to change directories.

    This context manager will change directories to ``dest``, and after its scope
    expires (outside of the ``with`` statement, or after the decorated function) it will
    change directories back to the original current working directory.

    As a context manager::

        from ci_exec import cd, which

        if __name__ == "__main__":
            # Get the build tools setup.
            cmake = which("cmake")
            ninja = which("ninja")

            # Suppose current directory here is "/source"
            with cd("build", create=True):
                # Current directory is now "/source/build"
                cmake("..", "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release")
                ninja()

            # Any code out-dented (not under the `with`): current directory is "/source"

    As a decorator::

        from ci_exec import cd, which

        @cd("build", create=True)
        def build():
            # Inside the function: current directory is "/source/build"
            cmake = which("cmake")
            ninja = which("ninja")
            cmake("..", "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release")
            ninja()

        if __name__ == "__main__":
            # Suppose current directory here is "/source"
            build()  # Function executes in "/source/build"
            # After the function current directory is "/source"

    Parameters
    ----------
    dest : pathlib.Path or str
        The destination to change directories to.

    create : bool
        Whether or not the ``dest`` is allowed to be created.  Default: ``False``, the
        ``dest`` must exist already (will :func:`~ci_exec.core.fail` if it does not).
        If ``True``, :func:`~ci_exec.core.mkdir_p` will be called with ``dest``.
    """

    def __init__(self, dest: Union[str, Path], *, create: bool = False):
        if isinstance(dest, str):
            dest = Path(dest)
        dest = dest.expanduser()
        if not dest.is_absolute():
            # NOTE: python <3.6 resolve() throws, we need an absolute path to something
            # that may not exist which is what this does.
            dest = Path(os.path.abspath(str(dest)))

        self.create = create
        self.dest = dest
        self.return_dest = None

    def __enter__(self):  # noqa: D105
        # If it does not exist, create it or fail.
        if not self.dest.is_dir():
            if self.create:
                mkdir_p(self.dest)  # May fail, if cannot create we want failure.
            else:
                fail("cd: '{dest}' is not a directory, but create=False.".format(
                    dest=str(self.dest)
                ))
        # Now that we are running, stash the current working directory at the time
        # this context is being created.
        try:
            self.return_dest = Path.cwd()
        except Exception as e:
            fail("cd: could not get current working directory: {e}".format(e=e))
        # At long last, actually change to the directory.
        try:
            os.chdir(str(self.dest))
        except Exception as e:
            fail("cd: could not change directories to '{dest}': {e}".format(
                dest=str(self.dest), e=e
            ))

        return self

    def __exit__(self, exc_type, exc_value, traceback):  # noqa: D105
        try:
            os.chdir(str(self.return_dest))
        except Exception as e:
            fail("cd: could not return to {return_dest}: {e}".format(
                return_dest=self.return_dest, e=e
            ))


def merge_kwargs(defaults: dict, kwargs: dict):
    """
    Merge ``defaults`` into ``kwargs`` and return ``kwargs``.

    Intended usage is for setting defaults to ``**kwargs`` when the caller did not
    provide a given argument, but making sure not to overwrite the caller's explicit
    argument when specified.

    For example::

        >>> merge_kwargs({"a": 1, "b": 2}, {})
        {'a': 1, 'b': 2}
        >>> merge_kwargs({"a": 1, "b": 2}, {"a": 3})
        {'a': 3, 'b': 2}

    Entries in the ``defaults`` parameter only get included of **not** present in the
    ``kwargs`` argument.  This is to facilitate something like this::

        from ci_exec import merge_kwargs

        # The function we want to customize the defaults for.
        def func(alpha=1, beta=2):
            return alpha + beta

        # Example: default to alpha=2, leave beta alone.
        def custom(**kwargs):
            return func(**merge_kwargs({"alpha": 2}, kwargs))

        # custom()                == 4
        # custom(alpha=0)         == 2
        # custom(beta=0)          == 2
        # custom(alpha=0, beta=0) == 0

    Parameters
    ----------
    defaults : dict
        The dictionary of defaults to add to ``kwargs`` if not present.

    kwargs : dict
        The dictionary to merge ``defaults`` into.

    Return
    ------
    dict
        The ``kwargs`` dictionary, possibly with values from ``defaults`` injected.
    """
    for key, val in defaults.items():
        if key not in kwargs:
            kwargs[key] = val

    return kwargs
