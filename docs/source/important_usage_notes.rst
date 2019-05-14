Important Usage Notes
========================================================================================

Namespace Pollution
----------------------------------------------------------------------------------------

The ``ci_exec`` package namespace is polluted intentionally.  Always import from the
polluted namespace, never import from the module originally defining something::

    from ci_exec import which       # Yes
    from ci_exec.core import which  # NO!

In practice it shouldn't matter that much, but

1. Any functions moved to different modules will not be considered ABI breaking changes.
   So if ``ci_exec.core.which`` moved to a different ``ci_exec.other_module``, this
   would be done in a patch release (``ci_exec`` uses semantic versioning).
2. Anything that is not exposed at the top-level is more than likely something that
   should not be used.

Beware of Commands Expecting Input
----------------------------------------------------------------------------------------

The :func:`Executable.__call__() <ci_exec.core.Executable.__call__>` method internally
invokes :func:`python:subprocess.run`, which does some fancy manipulations of
``stdout``, ``stderr``, **and** ``stdin``.  In particular, the subprocess by default
will allow communication on ``stdin`` for commands that are expecting input.  In the
context of CI, this is problematic, and users need to be aware that the subprocess will
indeed pause and solicit user input.  Consider a scenario where say |filter_file| was
used to make some significant changes on the CI provider.  If you ran::

    from ci_exec import which

    git = which("git")
    git("diff")

The build may fail from a timeout rather than just displaying the changes, because for a
large enough change to report ``git`` will want to use your ``$PAGER`` to let you
scroll through it.  Most commands that allow input also provide a command-line flag to
disable this behavior and in this scenario, it would be::

    git("--no-pager", "diff")

In situations where you know that input is required, :func:`python:subprocess.run`
enables this via the ``input`` parameter.  Consider the following toy script that is
expecting two pieces of user input at different stages::

    name = input("What is your name? ")
    print("Hi {name}, nice to meet you.".format(name=name))

    age = input("How old are you? ")
    print("Wow!  {age} is such a great age :)".format(age=age))

Then you could call it using ``ci_exec`` like this::

    import sys
    from ci_exec import Executable

    if __name__ == "__main__":
        python = Executable(sys.executable)
        python("./multi_input.py", input=b"Bilbo\n111")

where

1. The ``input`` parameter needs a :class:`python:bytes` object (the ``b`` prefix in
   ``b"..."``).
2. You use ``\n`` to send a newline.  From the docs: For *stdin*, line ending characters
   ``'\n'`` in the input will be converted to the default line separator
   :data:`python:os.linesep`.  So ``"Bilbo\n"`` will end up being the answer to the
   first ``name = input(...)``, and ``"111"`` will be sent to the ``age = input(...)``.

Build Logs out of Order (Azure Pipelines)
----------------------------------------------------------------------------------------

If the results of call logging appear out of order, then your CI provider is affected
by this.  This is a known problem on Azure Pipelines, it seems unlikely to affect many
other providers due to the nature of how the Azure Pipelines build logs are served.
Example "script"::

    cmake("..")
    ninja()

Produces:

.. code-block:: console

    -- The C compiler identification is GNU 8.3.1
    -- The CXX compiler identification is GNU 8.3.1
    -- Check for working C compiler: /usr/bin/gcc
    -- Check for working C compiler: /usr/bin/gcc -- works
    ...
    [12/74] Building C object ...joystick.c.o
    $ /usr/bin/cmake ..
    $ /usr/bin/ninja

The log is out of order, all cmake / ninja output appeared before the call logging
(``$ /usr/bin/cmake ..`` and ``$ /usr/bin/ninja``).  There are two possible solutions:

1. Invoke your build script using `python -u <py_cmd_u_>`_: ``python -u ./.ci/build.py``
2. Set the environment variable `PYTHONUNBUFFERED=true <py_env_u_>`_.

.. _py_cmd_u: https://docs.python.org/using/cmdline.html#cmdoption-u
.. _py_env_u: https://docs.python.org/using/cmdline.html#envvar-PYTHONUNBUFFERED
