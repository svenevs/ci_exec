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
"""Tests for the :mod:`ci_exec.provider` module."""

from ci_exec.provider import Provider
from ci_exec.utils import set_env, unset_env

_generic_providers = ["CI", "CONTINUOUS_INTEGRATION"]
_specific_providers = [
    # is_appveyor  #####################################################################
    "APPVEYOR",
    # is_azure_pipelines  ##############################################################
    "AZURE_HTTP_USER_AGENT", "AGENT_NAME", "BUILD_REASON",
    # is_circle_ci  ####################################################################
    "CIRCLECI",
    # is_github_actions ################################################################
    "GITHUB_RUN_ID",
    # is_jenkins  ######################################################################
    "JENKINS_URL", "BUILD_NUMBER",
    # is_travis  #######################################################################
    "TRAVIS"
]
_all_providers = [*_generic_providers, *_specific_providers]


def provider_sum():
    """Return number of |Provider|'s that return ``True``."""
    return sum([provider() for provider in Provider._all_provider_functions])


@unset_env(*_all_providers)
def test_provider_is_ci():
    """
    Validate |is_ci| reports as expected.

    .. |is_ci| replace:: :func:`Provider.is_ci() <ci_exec.provider.Provider.is_ci>`
    """
    assert not Provider.is_ci()

    # Test individual generic providers report success.
    for generic in _generic_providers:
        generic_map = {generic: "true"}
        with set_env(**generic_map):
            assert Provider.is_ci()

    # Test both being set report success.
    full_generic_map = {generic: "true" for generic in _generic_providers}
    with set_env(**full_generic_map):
        assert Provider.is_ci()

    # Test that setting specific provider(s) also reports success.  This should also be
    # tested in each specific provider test below.
    full_provider_map = {}
    for provider in ["APPVEYOR", "CIRCLECI", "TRAVIS"]:
        provider_map = {provider: "true"}
        with set_env(**provider_map):
            assert Provider.is_ci()

        full_provider_map[provider] = "true"

    with set_env(**full_provider_map):
        assert Provider.is_ci()


@unset_env(*_all_providers)
def test_provider_is_appveyor():
    """
    Validate |is_appveyor| reports as expected.

    .. |is_appveyor| replace::

        :func:`Provider.is_appveyor() <ci_exec.provider.Provider.is_appveyor>`
    """
    assert not Provider.is_ci()
    assert not Provider.is_appveyor()
    with set_env(APPVEYOR="true"):
        assert Provider.is_ci()
        assert Provider.is_appveyor()
        assert provider_sum() == 1


@unset_env(*_all_providers)
def test_provider_is_azure_pipelines():
    """
    Validate |is_azure_pipelines| reports as expected.

    .. |is_azure_pipelines| replace::

        :func:`Provider.is_azure_pipelines() <ci_exec.provider.Provider.is_azure_pipelines>`
    """  # noqa: E501
    assert not Provider.is_ci()
    assert not Provider.is_azure_pipelines()
    with set_env(AZURE_HTTP_USER_AGENT="dontcare"):
        assert not Provider.is_ci()
        assert not Provider.is_azure_pipelines()
        with set_env(AGENT_NAME="dontcare"):
            assert not Provider.is_ci()
            assert not Provider.is_azure_pipelines()
            with set_env(BUILD_REASON="dontcare"):
                assert Provider.is_ci()
                assert Provider.is_azure_pipelines()
                assert provider_sum() == 1


@unset_env(*_all_providers)
def test_provider_is_circle_ci():
    """
    Validate |is_circle_ci| reports as expected.

    .. |is_circle_ci| replace::

        :func:`Provider.is_circle_ci() <ci_exec.provider.Provider.is_circle_ci>`
    """
    assert not Provider.is_ci()
    assert not Provider.is_circle_ci()
    with set_env(CIRCLECI="true"):
        assert Provider.is_ci()
        assert Provider.is_circle_ci()
        assert provider_sum() == 1


@unset_env(*_all_providers)
def test_provider_is_github_actions():
    """
    Validate |is_github_actions| reports as expected.

    .. |is_github_actions| replace::

        :func:`Provider.is_github_actions <ci_exec.provider.Provider.is_github_actions>`
    """
    assert not Provider.is_ci()
    assert not Provider.is_github_actions()
    with set_env(GITHUB_RUN_ID="123456789"):
        assert Provider.is_ci()
        assert Provider.is_github_actions()
        assert provider_sum() == 1


@unset_env(*_all_providers)
def test_provider_is_jenkins():
    """
    Validate |is_jenkins| reports as expected.

    .. |is_jenkins| replace::

        :func:`Provider.is_jenkins() <ci_exec.provider.Provider.is_jenkins>`
    """
    assert not Provider.is_ci()
    assert not Provider.is_jenkins()
    with set_env(JENKINS_URL="dontcare"):
        assert not Provider.is_ci()
        assert not Provider.is_jenkins()
        with set_env(BUILD_NUMBER="dontcare"):
            assert Provider.is_ci()
            assert Provider.is_jenkins()
            assert provider_sum() == 1


@unset_env(*_all_providers)
def test_provider_is_travis():
    """
    Validate |is_travis| reports as expected.

    .. |is_travis| replace::

        :func:`Provider.is_travis() <ci_exec.provider.Provider.is_travis>`
    """
    assert not Provider.is_ci()
    assert not Provider.is_travis()
    with set_env(TRAVIS="true"):
        assert Provider.is_ci()
        assert Provider.is_travis()
        assert provider_sum() == 1
