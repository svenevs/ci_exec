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
Assorted utility functions.

This module aims to house any utility functions that may facilitate easier consumption
of the ``ci_exec`` package.
"""

import os
from contextlib import ContextDecorator
from pathlib import Path
from typing import Dict, List, Union

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
        ``dest`` must exist already (will |fail| if it does not).  If ``True``,
        |mkdir_p| will be called with ``dest``.
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
                fail(f"cd: '{str(self.dest)}' is not a directory, but create=False.")
        # Now that we are running, stash the current working directory at the time
        # this context is being created.
        try:
            self.return_dest = Path.cwd()
        except Exception as e:
            fail(f"cd: could not get current working directory: {e}")
        # At long last, actually change to the directory.
        try:
            os.chdir(str(self.dest))
        except Exception as e:
            fail(f"cd: could not change directories to '{str(self.dest)}': {e}")

        return self

    def __exit__(self, exc_type, exc_value, traceback):  # noqa: D105
        try:
            os.chdir(str(self.return_dest))
        except Exception as e:
            fail(f"cd: could not return to {self.return_dest}: {e}")


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


class set_env(ContextDecorator):  # noqa: N801
    """
    Context manager / decorator that can be used to set environment variables.

    Usage example::

        from ci_exec import set_env

        @set_env(CC="clang", CXX="clang++")
        def build_clang():
            # CC="clang" and CXX="clang++" inside function.

        # ... or ...

        with set_env(CC="clang", CXX="clang++"):
            # CC="clang" and CXX="clang++" in `with` block

    Prior environment variable state will be recorded and later restored when a
    decorated function / ``with`` block's scope ends.

    1. An environment variable was already set.  Its value is saved before overwriting,
       and then later restored::

           # Example: CC=gcc was already set.
           with set_env(CC="clang"):
               # Inside block: CC="clang"
           # Out-dented: CC=gcc again.

    2. An environment variable was **not** already set.  Its value is unset again::

           # Example: CC was _not_ set in environment.
           with set_env(CC="clang"):
               # Inside block: CC="clang"
           # Out-dented: CC _not_ set in environment.

    .. note::

        See :ref:`note in unset_env <unset_env_note>` for more information on removing
        environment variables.

    Parameters
    ----------
    **kwargs
        Keyword argument parameter pack.  Keys are the environment variable to set, and
        values are the desired value of the environment variable.  All keys and all
        values **must** be strings.

    Raises
    ------
    ValueError
        If no arguments are provided (``len(kwargs) == 0``), or if any keys / values are
        **not** a :class:`python:str`.
    """

    def __init__(self, **kwargs: str):
        # Need at least one environment variable to set.
        if len(kwargs) == 0:
            raise ValueError("set_env: at least one argument required.")

        # Make sure all values are strings (required by os.environ).  All keys are
        # implicitly strings -- constructing this class with non-string keys is a
        # TypeError via Python and how **kwargs works <3
        for env_var, env_val in kwargs.items():
            if not isinstance(env_val, str):
                raise ValueError("set_env: all keys and values must be strings.")

        # Save state requested by user, do not inspect environment until __enter__.
        self.set_env = {**kwargs}  # type: Dict[str, str]
        self.restore_env = {}  # type: Dict[str, str]
        self.delete_env = []  # type: List[str]

    def __enter__(self):  # noqa: D105
        for key, val in self.set_env.items():
            # Create backups / record what needs to be deleted afterward.
            curr = os.getenv(key, None)
            if curr:
                self.restore_env[key] = curr
            else:
                self.delete_env.append(key)

            # Set the actual environment variable
            os.environ[key] = val

        return self

    def __exit__(self, exc_type, exc_value, traceback):  # noqa: D105
        # Restore all previously set environment variables.
        for key, val in self.restore_env.items():
            os.environ[key] = val

        # Remove any environment variables that were not previously set.
        for key in self.delete_env:
            # NOTE: need to double check it is there, nested @set_env that set the same
            # variable will delete as the are __exit__ed, meaning an inner scope may
            # have already deleted this.
            if key in os.environ:
                del os.environ[key]


class unset_env(ContextDecorator):  # noqa: N801
    """
    Context manager / decorator that can be used to unset environment variables.

    Usage example::

        from ci_exec import unset_env

        @unset_env("CC", "CXX")
        def build():
            # Neither CC nor CXX are set in the environment during this function call.

        # ... or ...

        with unset_env("CC", "CXX"):
            # Neither CC nor CXX are set in the environment inside this block.

    Prior environment variable state will be recorded and later restored when a
    decorated function / ``with`` block's scope ends.  So if an environment variable was
    already set, its value is saved before deletion, and then later restored::

           # Example: CC=gcc was already set.
           with unset_env("CC"):
               # Inside block: CC not set in environment.
           # Out-dented: CC=gcc again.

    .. _unset_env_note:

    .. note::

        Removing the environment variable is done via ``del os.environ[env_var]``.  This
        *may* or *may not* affect child processes in the manner you expect, depending on
        whether your platform supports :func:`python:os.unsetenv`.  See the end of the
        description of :data:`python:os.environ` for more information.

    Parameters
    ----------
    *args
        Argument parameter pack.  Each argument is an environment variable to unset.
        Each argument **must** be a string.  If a specified argument is not currently
        set in the environment, it will effectively be skipped.

    Raises
    ------
    ValueError
        If no arguments are provided (``len(args) == 0``), or if any arguments are
        **not** a :class:`python:str`.
    """

    def __init__(self, *args: str):
        # Need at least one environment variable to set.
        if len(args) == 0:
            raise ValueError("unset_env: at least one argument required.")

        # Make sure every requested environment variable to unset is a string.
        for a in args:
            if not isinstance(a, str):
                raise ValueError("unset_env: all arguments must be strings.")

        # Save state requested by user, do not inspect environment until __enter__.
        self.unset_env = [*args]  # type: List[str]
        self.restore_env = {}  # type: Dict[str, str]

    def __enter__(self):  # noqa: D105
        for key in self.unset_env:
            curr = os.getenv(key, None)
            if curr:
                # If the variable is set, save its current value and then delete it.
                self.restore_env[key] = curr
                del os.environ[key]

        return self

    def __exit__(self, exc_type, exc_value, traceback):  # noqa: D105
        # Restore all previously set environment variables.
        for key, val in self.restore_env.items():
            os.environ[key] = val
