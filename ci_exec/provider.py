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
"""Mechanisms to detect a given CI provider."""

import os
from typing import Callable, List, TYPE_CHECKING

# mypy has trouble inferring @provider as @staticmethod right now.  The solution will
# not likely exist for a while, there are some deeper problems with typing and
# staticmethod / classmethod that need to be fixed first.
if TYPE_CHECKING:
    provider = staticmethod  # pragma: no cover
else:
    def provider(func: Callable) -> staticmethod:
        """
        Mark a function as a CI provider.

        **Not intended for use outside of the** |Provider| **class**.

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
    Metaclass for |Provider|.

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
       ``tests/provider.py`` file (near :func:`~tests.provider.provider_sum`).
    4. Add a "pseudo-test" in ``tests/provider.py`` in the appropriate location.

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
    def is_github_actions() -> bool:
        """
        Whether or not the code is executing on `GitHub Actions`_.

        `Environment variables considered <github_actions_env_>`_:

        +----------------------+-----------------------------+
        | Environment Variable | Environment Value           |
        +======================+=============================+
        | ``GITHUB_ACTIONS``   | ``true`` (case insensitive) |
        +----------------------+-----------------------------+

        .. _GitHub Actions: https://github.com/features/actions
        .. _github_actions_env: https://help.github.com/en/actions/configuring-and-managing-workflows/using-environment-variables#default-environment-variables
        """  # noqa: E501
        return os.getenv("GITHUB_ACTIONS", "false").lower() == "true"

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
