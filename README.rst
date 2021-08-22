ci_exec
========================================================================================
|docs| |azure| |travis| |coverage| |pypi| |py_versions| |license|

.. begin_badges

.. |docs| image:: https://readthedocs.org/projects/ci-exec/badge/?version=latest
   :alt: Documentation Status
   :target: http://ci-exec.readthedocs.io/

.. |azure| image:: https://img.shields.io/azure-devops/build/svenevs/bb82882f-1c4c-4bf2-a2da-1d2146a7fb2a/5/master.svg?logo=azure-devops
   :alt: Azure Pipelines Build Status
   :target: https://dev.azure.com/svenevs/ci_exec/_build/latest?definitionId=5&branchName=master

.. |travis| image:: https://img.shields.io/travis/com/svenevs/ci_exec/master.svg?logo=Travis
   :alt: Travis CI Build Status
   :target: https://travis-ci.com/svenevs/ci_exec

.. |coverage| image:: https://codecov.io/gh/svenevs/ci_exec/branch/master/graph/badge.svg
   :alt: Code Coverage Report
   :target: https://codecov.io/gh/svenevs/ci_exec

.. |pypi| image:: https://img.shields.io/pypi/v/ci-exec.svg
   :alt: PyPI Version
   :target: https://pypi.org/project/ci-exec/

.. |py_versions| image:: https://img.shields.io/pypi/pyversions/ci-exec.svg
   :alt: PyPI - Python Version
   :target: https://pypi.org/project/ci-exec

.. |license| image:: https://img.shields.io/github/license/svenevs/ci_exec.svg
   :alt: License Apache 2.0
   :target: https://github.com/svenevs/ci_exec/blob/master/LICENSE

.. end_badges

A wrapper package designed for running continuous integration (CI) build steps using
Python 3.6+.

Managing cross platform build scripts for CI can become tedious at times when you need
to e.g., maintain two nearly identical scripts ``install_deps.sh`` and
``install_deps.bat`` due to incompatible syntaxes.  ``ci_exec`` enables a single file
to manage this using Python.

The ``ci_exec`` package provides a set of wrappers / utility functions designed
specifically for running build steps on CI providers.  It is

**Logging by Default**
    Commands executed, including their full command-line arguments, are logged.  This
    includes any output on ``stdout`` / ``stderr`` from the commands.  The logging
    resembles what ``set -x`` would give you in a shell script.  For commands that will
    take a long time, as long as output is being produced, this will additionally
    prevent timeouts on the build.

**Failing by Default**
    Any command that does not succeed will fail the entire build.  An attempt to exit
    with the same exit code as the command that failed will be performed.  Meaning the
    CI provider will correctly report a failed build.

**Convenient**
    ``ci_exec`` affords users the ability to write shell-like scripts that will work
    on any platform that Python can run on.  A simple example:

    .. code-block:: py

        from ci_exec import cd, which

        cmake = which("cmake")
        ninja = which("ninja")
        with cd("build", create=True):
            cmake("..", "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release")
            ninja("-j", "2", "test")

Installation
========================================================================================

``ci_exec`` is `available on PyPI <https://pypi.org/project/ci-exec/>`_.  It can be
installed using your python package manager of choice:

.. code-block:: console

    $ pip install ci-exec

.. note::

    The PyPI package has a ``-``: ``ci-exec``, not ``ci_exec``.

There is also a ``setup.py`` here, so you can also install it from source:

.. code-block:: console

    $ pip install git+https://github.com/svenevs/ci_exec.git@master

License
========================================================================================

This software is licensed under the Apache 2.0 license.
