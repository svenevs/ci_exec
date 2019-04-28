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
from typing import Callable, Dict, List, TYPE_CHECKING, Union

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


# mypy has trouble inferring @provider as @staticmethod right now.  The solution will
# not likely exist for a while, there are some deeper problems with typing and
# staticmethod / classmethod that need to be fixed first.
if TYPE_CHECKING:
    provider = staticmethod  # pragma: no cover
else:
    def provider(func: Callable) -> staticmethod:
        """
        Mark a function as a CI provider.

        **Not intended for use outside of the** :class:`Provider` **class**.

        Parameters
        ----------
        func
            The function to decorate.

        Returns
        -------
        :func:`python:staticmethod`
            A static method that has an attribute ``register_provider=True``.
        """
        # NOTE: order matters, staticmethod(func) seems to clear custom attributes so
        # make sure that setting register_provider stays last!
        static_func = staticmethod(func)
        setattr(static_func, "register_provider", True)
        return static_func


class ProviderMeta(type):
    """
    Metaclass for :class:`Provider`.

    This metaclass populates :attr:`Provider._all_provider_functions` by coordinating
    with the :func:`provider` decorator.

    **Not intended to be used as a metaclass for any other classes**.
    """

    def __new__(cls, name, bases, attrs):  # noqa: D102
        the_cls = super().__new__(cls, name, bases, attrs)
        _all_provider_functions = []
        for key, val in attrs.items():
            if getattr(val, "register_provider", False):
                # NOTE: cannot append `val` directly, you will end up with
                # 'staticmethod' is not callable.
                _all_provider_functions.append(getattr(the_cls, key))
        the_cls._all_provider_functions = _all_provider_functions
        return the_cls


class Provider(object, metaclass=ProviderMeta):
    """
    Check if code is executing on a continuous integration (CI) service.

    Every now and then it is useful to know

    1. If you are running on any CI service, or
    2. If you are running on a specific CI service.

    The static methods in this class provide a way of checking for pre-defined (by the
    CI service provider) environment variables::

        from ci_exec import Provider, which

        def build():
            # ... run cmake etc ...
            ninja = which("ninja")
            if Provider.is_travis():
                # Ninja uses too much memory during link phase.  See:
                # "My build script is killed without any error"
                # https://docs.travis-ci.com/user/common-build-problems/
                ninja("-j", "2", "install")
            else:
                ninja("install")

    **Available Providers**:

    .. availableproviders::

    **Adding a New Provider**:

    Pull requests are welcome.  Alternatively, simply raise an issue with a link to the
    provider's main homepage as well as a link to the documentation certifying the
    environment variables we can rely on.

    1. Add a new ``is_{new_provider}`` method to this class, decorated with
       ``@provider``.  Keep these alphabetically sorted (except for ``is_ci``, which
       should always be first).
    2. Document any environment variable(s) involved in a table, including hyperlinks to
       the provider's main homepage as well as documentation describing the environment
       variables in question.
    3. Add to the ``_specific_providers`` list of environment variables in the
       ``tests/utils.py`` file (near :func:`~tests.utils.provider_sum`).
    4. Add a "pseudo-test" in ``tests/utils.py`` in the appropriate location (near
       bottom of the file).

    Attributes
    ----------
    _all_provider_functions : list
        **Not intended for external usage**.  The list of all known (implemented)
        CI provider functions in this class.  For example, it will contain
        :func:`Provider.is_appveyor`, ..., :func:`Provider.is_travis`, etc.  This is a
        **class** attribute, the ``Provider`` class is not intended to be instantiated.
    """

    # NOTE: only added here to make mypy happy.
    _all_provider_functions = []  # type: List[Callable]

    @staticmethod
    def is_ci() -> bool:
        """
        Whether or not the code is executing on a CI service.

        Environment variables considered:

        +----------------------------+-----------------------------+
        | Environment Variable       | Environment Value           |
        +============================+=============================+
        | ``CI``                     | ``true`` (case insensitive) |
        +----------------------------+-----------------------------+
        | ``CONTINUOUS_INTEGRATION`` | ``true`` (case insensitive) |
        +----------------------------+-----------------------------+

        If neither of these are ``true``, this function will query every provider
        directly.  For example, it will end up checking if
        ``any([Provider.is_appveyor(), ..., Provider.is_travis(), ...])``.
        """
        return os.getenv("CI", "false").lower() == "true" or \
            os.getenv("CONTINUOUS_INTEGRATION", "false") == "true" or \
            any([provider() for provider in Provider._all_provider_functions])

    @provider
    def is_appveyor() -> bool:  # type: ignore
        """
        Whether or not the code is executing on `AppVeyor`_.

        `Environment variables considered <appveyor_env_>`_:

        +----------------------+-----------------------------+
        | Environment Variable | Environment Value           |
        +======================+=============================+
        | ``APPVEYOR``         | ``true`` (case insensitive) |
        +----------------------+-----------------------------+

        .. _AppVeyor: https://www.appveyor.com/
        .. _appveyor_env: https://www.appveyor.com/docs/environment-variables/
        """
        return os.getenv("APPVEYOR", "false").lower() == "true"

    @provider
    def is_azure_pipelines() -> bool:
        """
        Whether or not the code is executing on `Azure Pipelines <azp_>`_.

        `Environment variables considered <azp_env_>`_:

        +---------------------------+-----------------------------------+
        | Environment Variable      | Environment Value                 |
        +===========================+===================================+
        | ``AZURE_HTTP_USER_AGENT`` | Existence checked, value ignored. |
        +---------------------------+-----------------------------------+
        | ``AGENT_NAME``            | Existence checked, value ignored. |
        +---------------------------+-----------------------------------+
        | ``BUILD_REASON``          | Existence checked, value ignored. |
        +---------------------------+-----------------------------------+

        .. note:: All three must be set for this function to return ``True``.

        .. _azp: https://azure.microsoft.com/en-us/services/devops/pipelines/
        .. _azp_env: https://docs.microsoft.com/en-us/azure/devops/pipelines/build/variables
        """  # noqa: E501
        # NOTE: in future this might get to change.
        # https://github.com/MicrosoftDocs/vsts-docs/issues/4051
        return os.getenv("AZURE_HTTP_USER_AGENT", None) is not None and \
            os.getenv("AGENT_NAME", None) is not None and \
            os.getenv("BUILD_REASON", None) is not None

    @provider
    def is_circle_ci() -> bool:
        """
        Whether or not the code is executing on `CircleCI`_.

        `Environment variables considered <circle_ci_env_>`_:

        +----------------------+-----------------------------+
        | Environment Variable | Environment Value           |
        +======================+=============================+
        | ``CIRCLECI``         | ``true`` (case insensitive) |
        +----------------------+-----------------------------+

        .. _CircleCI: https://circleci.com/
        .. _circle_ci_env: https://circleci.com/docs/2.0/env-vars/#built-in-environment-variables
        """  # noqa: E501
        return os.getenv("CIRCLECI", "false").lower() == "true"

    @provider
    def is_jenkins() -> bool:
        """
        Whether or not the code is executing on `Jenkins`_.

        `Environment variables considered <jenkins_env_>`_:

        +----------------------+-----------------------------------+
        | Environment Variable | Environment Value                 |
        +======================+===================================+
        | ``JENKINS_URL``      | Existence checked, value ignored. |
        +----------------------+-----------------------------------+
        | ``BUILD_NUMBER``     | Existence checked, value ignored. |
        +----------------------+-----------------------------------+

        .. note::  Both must be set for this function to return ``True``.

        .. _Jenkins: https://jenkins.io/
        .. _jenkins_env: https://wiki.jenkins.io/display/JENKINS/Building+a+software+project#Buildingasoftwareproject-belowJenkinsSetEnvironmentVariables
        """  # noqa: E501
        return os.getenv("JENKINS_URL", None) is not None and \
            os.getenv("BUILD_NUMBER", None) is not None

    @provider
    def is_travis() -> bool:
        """
        Whether or not the code is executing on `Travis`_.

        `Environment variables considered <travis_env_>`_:

        +----------------------+-----------------------------+
        | Environment Variable | Environment Value           |
        +======================+=============================+
        | ``TRAVIS``           | ``true`` (case insensitive) |
        +----------------------+-----------------------------+

        .. _Travis: https://travis-ci.com/
        .. _travis_env: https://docs.travis-ci.com/user/environment-variables/#default-environment-variables
        """  # noqa: E501
        return os.getenv("TRAVIS", "false").lower() == "true"
