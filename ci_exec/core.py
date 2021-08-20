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
"""The core functionality of the ``ci_exec`` package."""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import NoReturn, Optional, Union

from .colorize import Colors, Styles, colorize


def fail(why: str, *, exit_code: int = 1, no_prefix: bool = False) -> NoReturn:
    """
    Write a failure message to :data:`python:sys.stderr` and exit.

    Parameters
    ----------
    why : str
        The message explaining why the program is being failed out.

    exit_code : int
        The exit code to use.  Default: ``1``.

    no_prefix : bool
        Whether to prefix a bold red ``"[X] "`` before ``why``.  Default: ``False``, the
        bold red ``"[X] "`` prefix is included unless set to ``True``.
    """
    if no_prefix:
        prefix = ""
    else:
        prefix = colorize("[X] ", color=Colors.Red, style=Styles.Bold)
    sys.stderr.write(f"{prefix}{why}\n")
    sys.exit(exit_code)


class Executable:
    """
    Represent a reusable executable.

    Each executable is:

    1. Failing by default: unless called with ``check=False``, any execution
       that fails (has a non-zero exit code) will result in a call to |fail|,
       terminating the entire application.
    2. Logging by default: every call executed will print what will be run in color
       and then dump the output of the command.  In the event of failure, this makes
       finding the last call issued much simpler.

    Consider the following simple script::

        from ci_exec import Executable
        git = Executable("/usr/bin/git")
        git("remote")
        # Oops! --pretty not --petty ;)
        git("log", "-1", "--petty=%B")
        git("status")  # will not execute (previous failed)

    When we execute ``python simple.py`` and check the exit code with ``echo $?``:

    .. code-block:: console

        > python simple.py
        $ /usr/bin/git remote
        origin
        $ /usr/bin/git log -1 --petty=%B
        fatal: unrecognized argument: --petty=%B
        [X] Command '('/usr/bin/git', 'log', '-1', "--petty=%B")' returned
            non-zero exit status 128.
        > echo $?
        128

    See :func:`__call__` for more information.

    .. tip::

        Hard-coded paths in these examples were for demonstrative purposes.  In practice
        this should not be done, use |which| instead.

    Attributes
    ----------
    exe_path : str
        The path to the executable that will be run when called.

    log_calls : bool
        Whether or not every invocation of :func:`__call__` should print what will
        execute before executing it.  Default: ``True``.

    log_prefix : str
        The prefix to use when printing a given invocation of :func:`__call__`.
        Default: ``"$ "`` to simulate a ``console`` lexer.  Set to the empty string
        ``""`` to have no prefix.

    log_color : str
        The ``color`` code to use when calling |colorize| to display the next invocation
        of :func:`__call__`.  Set to ``None`` to disable colorizing each log of
        :func:`__call__`.  Default: :data:`Colors.Cyan <ci_exec.colorize.Colors.Cyan>`.

    log_style : str
        The ``style`` code to use when calling |colorize| to display the next invocation
        of :func:`__call__`.  If no colors are desired, set ``log_color`` to ``None``.
        Default: :data:`Styles.Bold <ci_exec.colorize.Styles.Bold>`.

    Raises
    ------
    ValueError
        If ``exe_path`` is not a file, or if it is not executable.
    """

    PATH_EXTENSIONS = set(
        filter(
            # Filter empty strings so we can just check `if Executable.PATH_EXTENSIONS`
            lambda x: x != "",
            # Map all values to lowercase for consistency
            map(lambda x: x.lower(), os.getenv("PATHEXT", "").split(os.pathsep))
        )
    )
    """
    The set of valid file extensions that can be executed on Windows.

    On \\*nix systems this will be the empty set, and takes no meaning.  On Windows, it
    is controlled by the user.  These are stored in lower case, and comparisons should
    be lower case for consistency.  The typical default value on Windows would be::

        PATH_EXTENSIONS = {".com", ".exe", ".bat", ".cmd"}
    """

    def __init__(self, exe_path: str, *, log_calls: bool = True,
                 log_prefix: str = "$ ", log_color: Optional[str] = Colors.Cyan,
                 log_style: str = Styles.Bold):
        p = Path(exe_path)
        if not p.is_file():
            raise ValueError(f"The path '{exe_path}' is not a file.")
        # NOTE: this check does not really apply to Windows.
        if not os.access(exe_path, os.X_OK):
            raise ValueError(f"The path '{exe_path}' is not executable.")
        # On Windows, check that this file can be executed directly using PATHEXT.
        if Executable.PATH_EXTENSIONS:
            if p.suffix.lower() not in Executable.PATH_EXTENSIONS:
                raise ValueError(f"Extension of '{exe_path}' is not in PATHEXT.")

        # Store paths as absolute paths so that users can change working directory
        # without needing to worry about relative paths.
        if not p.is_absolute():
            p = p.resolve()

        self.exe_path = str(p)
        self.log_calls = log_calls
        self.log_prefix = log_prefix
        self.log_color = log_color
        self.log_style = log_style

    def __call__(self, *args, **kwargs) -> subprocess.CompletedProcess:
        """
        Run :attr:`exe_path` with the specified command-line ``*args``.

        The usage of the parameters is best summarized in code::

            popen_args = (self.exe_path, *args)
            # ... some potential logging ...
            return subprocess.run(popen_args, **kwargs)

        For example, sending multiple arguments to the executable is as easy as::

            cmake = Executable("/usr/bin/cmake")
            cmake("..", "-G", "Ninja", "-DBUILD_SHARED_LIBS=ON")

        and any overrides to :func:`subprocess.run` you wish to include should be done
        with ``**kwargs``, which are forwarded directly.

        .. warning::

            **Any** exceptions generated result in a call to |fail|, which will
            terminate the application.

        Parameters
        ----------
        *args
            The positional arguments will be forwarded along with :attr:`exe_path` to
            :func:`python:subprocess.run`.

        **kwargs
            The key-value arguments are all forwarded to :func:`python:subprocess.run`.
            If ``check`` is not provided, this is an implicit ``check=True``.  That is,
            if you do **not** want the application to exit (via |fail|), you **must**
            specify ``check=False``:

            .. code-block:: python

                >>> from ci_exec import Executable
                >>> git = Executable("/usr/bin/git")
                >>> proc = git("not-a-command", check=False)
                $ /usr/bin/git not-a-command
                git: 'not-a-command' is not a git command. See 'git --help'.
                >>> proc.returncode
                1
                >>> git("not-a-command")
                $ /usr/bin/git not-a-command
                git: 'not-a-command' is not a git command. See 'git --help'.
                [X] Command '('/usr/bin/git', 'not-a-command')' returned non-zero exit
                    status 1.

            The final ``git("not-a-command")`` exited the shell (this is what is meant
            by "failing by default").

        Return
        ------
        subprocess.CompletedProcess
            The result of calling :func:`python:subprocess.run` as outlined above.

            .. note::

                Unless you are are calling with ``check=False``, you generally don't
                need to store the return type.
        """
        popen_args = (self.exe_path, *args)
        if self.log_calls:
            message = f"{self.log_prefix}{' '.join(popen_args)}"
            if self.log_color:
                message = colorize(message, color=self.log_color, style=self.log_style)
            print(message)
        try:
            # By default non-zero exit codes should terminate.
            if "check" not in kwargs:
                kwargs["check"] = True
            return subprocess.run(popen_args, **kwargs)
        except Exception as e:
            # Provide a little more context for the user, the actual error message will
            # be something like '__init__() got an unexpected keyword argument', which
            # may confuse people who don't understand that __call__ -> subprocess.run()
            # actually instantiates a subprocess.Popen object.
            if isinstance(e, TypeError):
                err_msg = (
                    f"Executable.__call__: invalid kwarg(s) for subprocess.run: {e}"
                )
            else:
                err_msg = f"{e}"
            # Try and mirror the exit code if possible, subprocess.run will raise an
            # exception when check=True, but this may not necessarily be why this code
            # is executing.
            # NOTE: 3.5 has no ending period, 3.6+ do.
            match = re.match(r".*non-zero exit status (\d+)\.?", err_msg)
            if match:
                try:
                    exit_code = int(match.group(1))
                except:  # noqa: E722 # pragma: no cover
                    exit_code = 1     # pragma: no cover
            else:
                exit_code = 1
            fail(err_msg, exit_code=exit_code)

    def __str__(self):  # noqa: D105
        return f"Executable('{self.exe_path}')"


def mkdir_p(path: Union[Path, str], mode: int = 0o777, parents: bool = True,
            exist_ok: bool = True):
    """
    Permissive wrapper around :meth:`python:pathlib.Path.mkdir`.

    The intention is to behave like ``mkdir -p``, meaning the only real difference is
    that ``parents`` and ``exist_ok`` default to ``True`` for this method (rather than
    ``False`` for ``pathlib``).

    Parameters
    ----------
    path : pathlib.Path or str
        The directory path to make.

    mode : int
        Access mask for directory permissions.  See :meth:`python:pathlib.Path.mkdir`.

    parents : bool
        Whether or not parent directories may be created.  Default: ``True``.

    exist_ok : bool
        Whether or not the command should be considered successful if the specified path
        already exists.  Default: ``True``.

        .. note::

            If the path exists and is a directory with ``exist_ok=True``, the command
            will succeed.  If the path exists and is a **file**, even with
            ``exist_ok=True`` the command will |fail|.
    """
    if isinstance(path, str):
        path = Path(path)
    try:
        path.mkdir(mode=mode, parents=parents, exist_ok=exist_ok)
    except Exception as e:
        fail(f"Unable to mkdir_p '{str(path)}': {e}")


def rm_rf(path: Union[Path, str], ignore_errors: bool = False, onerror=None):
    """
    Permissive wrapper around :func:`python:shutil.rmtree` bypassing :class:`python:FileNotFoundError` and :class:`python:NotADirectoryError`.

    This function simply checks if ``path`` exists first before calling
    :func:`python:shutil.rmtree`.  If the ``path`` does not exist, nothing is done.  If
    the path exists but is a file, :meth:`python:pathlib.Path.unlink` is called instead.

    Essentially, this function tries to behave like ``rm -rf``, but in the event that
    removal is not possible (e.g., due to insufficient permissions), the function will
    still |fail|.

    Parameters
    ----------
    path : pathlib.Path or str
        The directory path to delete (including all children).

    ignore_errors : bool
        Whether or not errors should be ignored.  Default: ``False``, to ensure that
        permission errors are still caught.

    onerror
        See :func:`python:shutil.rmtree` for more information on the callback.
    """  # noqa: E501
    if isinstance(path, str):
        path = Path(path)
    if not path.exists():
        return
    try:
        if path.is_file():
            path.unlink()
            return
        shutil.rmtree(str(path), ignore_errors=ignore_errors, onerror=onerror)
    except Exception as e:
        fail(f"Unable to remove '{str(path)}': {e}")


def which(cmd: str, *, mode: int = (os.F_OK | os.X_OK), path: Optional[str] = None,
          **kwargs) -> Executable:
    """
    Restrictive wrapper around :func:`shutil.which` that will |fail| if not found.

    The primary difference is that when ``cmd`` is not found,
    :func:`python:shutil.which` will return ``None`` whereas this function will
    |fail|.  If you need to conditionally check for a command, do **not** use this
    function, use :func:`python:shutil.which` instead.

    Parameters
    ----------
    cmd : str
        The name of the command to search for.  E.g., ``"cmake"``.

    mode : int
        The flag permission mask.  Default: ``(os.F_OK | os.X_OK)``, see:
        :data:`python:os.F_OK`, :data:`python:os.X_OK`, :func:`python:shutil.which`.

    path : str or None
        Default: ``None``.  See :func:`python:shutil.which`.

    **kwargs
        Included as a convenience bypass, forwards directly to |Executable| constructor.
        Suppose a non-logging |Executable| is desired.  One option::

            git = which("git")
            git.log_calls = False

        Or alternatively::

            git = which("git", log_calls=False)

        This is in recognition that for continuous integration users will likely have
        many different preferences.  Users can provide their own ``which`` to always use
        this default, or say, change the logging color::

            from ci_exec import which as ci_which
            from ci_exec import Colors, Styles

            def which(cmd: str):
                return ci_which(cmd, log_color=Colors.Magenta, log_style=Styles.Regular)

    Return
    ------
    Executable
        An executable created with the full path to the found ``cmd``.
    """
    exe_path = shutil.which(cmd, mode=mode, path=path)
    if exe_path is None:
        fail(f"Could not find '{cmd}' in $PATH.")
    return Executable(exe_path, **kwargs)
