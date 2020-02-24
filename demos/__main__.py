"""
Wrapper module for executing each respective location from the repository root.

Each individual demo is executable on its own.  However, users may also run a demo from
repository root doing ``python demos/ <demo_name>``.

By default the programs are not run in "animated" mode.  The ``--animated`` flag is what
is used to record the videos hosted on each individual demo page, which utilizes
``clear``, ``PAUSE`` and a delay in calls to :func:`type_message`.  See
:func:`mock_shell` for more information.
"""

import argparse
import os
import platform
import shlex
import subprocess
import sys
import textwrap
import time
from collections import namedtuple
from pathlib import Path
from typing import Any, Callable, List

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
from ci_exec import Executable, cd, merge_kwargs, rm_rf, which  # noqa: E402


# See tox.ini.  This is to enable coverage of the actual demo files.
CI_EXEC_DEMOS_COVERAGE = os.getenv("CI_EXEC_DEMOS_COVERAGE", False) == "YES"
"""
Whether or not this is a coverage run of the demo files.

.. warning::

    This should not be set unless invoking from ``tox``.  See notes in
    ``[testenv:docs]`` section of ``tox.ini`` at repository root.
"""


def windows_cmd_builtin(builtin: str):
    """
    Return a function that runs the specified ``builtin``.

    .. note::

        There is a reason this is not in the main library.  To deal with shell builtins
        requires a significant amount of extra work for little to no benefit.  The demos
        just need ``"cls"`` to clear and ``"type"`` to ``cat``.

    The return is a function that can support:

    ``*args``
        Any command line arguments to provide to the builtin.

    ``**kwargs``
        Any keyword arguments to provide to :func:`python:subprocess.run`.  This
        function will add ``check=True`` and ``shell=True`` unless these keys are
        already explicitly specified.

    Parameters
    ----------
    builtin : str
        Any of the `CMD builtins <https://ss64.com/nt/syntax-internal.html>`_, such as
        ``"type"`` or ``"cls"``.  No checking is performed!
    """
    def builtin_cmd(*args, **kwargs):
        kwargs = merge_kwargs({"check": True, "shell": True}, kwargs)
        return subprocess.run([builtin, *args], **kwargs)

    return builtin_cmd


def clear():
    """Clear the console screen.  Uses ``cls`` on Windows, and ``clear`` otherwise."""
    kwargs = {}
    if platform.system() == "Windows":
        actual_clear = windows_cmd_builtin("cls")
    else:
        actual_clear = which("clear", log_calls=False)
        # TERM not always set on CI machines, but we want coverage.  THIS IS "DANGEROUS"
        # since we're convincing `clear` it can do things it probably shouldn't ;)
        if CI_EXEC_DEMOS_COVERAGE:
            term = os.getenv("TERM", False)
            if not term:
                kwargs["env"] = {"TERM": "xterm"}

    actual_clear(**kwargs)


def pause(amount: float = 3.0):
    """
    Pause by ``amount`` using :func:`python:time.sleep`.

    This function exists so that it can be used for ``PAUSE`` statements in
    :func:`mock_shell`.

    Parameters
    ----------
    amount : float
        The amount of time to :func:`python:time.sleep` for.  Default: ``3.0`` seconds.
    """
    time.sleep(amount)


def type_message(message: str, *, delay: float):
    r"""
    Flush ``message`` to |stdout|, sleep by ``delay`` after character.

    .. |stdout| replace:: :data:`python:sys.stdout`

    Parameters
    ----------
    message : str
        What to type.  A trailing newline ``"\n"`` **will** be written at the end.

    delay : float
        The positive amount to :func:`time.sleep` after each **character** in
        ``message`` is written.  Suggested value for simulating typing to the console:
        ``0.05``.  Use ``0.0`` to avoid delays.
    """
    for char in message:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")
    sys.stdout.flush()


def mock_shell(program: str, *, cwd: str, delay: float, animated: bool):
    r"""
    Run a "shell" program from the specified working directory.

    - Lines starting with ``#`` are "comment" lines, they will be printed to the screen
      using :func:`type_message`.
    - Lines starting with ``"$ "`` are a command to execute.

        - Commands executed will be printed to the screen using :func:`type_message`.

    There is also a notion of "animated" mode.  When ``animated=True``, the following
    special behavior is enabled:

    - ``$ clear``: calls :func:`clear`.  In non-animated mode, ``clear`` is skipped.
    - ``PAUSE`` or ``PAUSE=X.Y``: call :func:`pause`, ``X.Y`` should be parseable as a
      ``float`` e.g., ``PAUSE=7.0`` would pause for 7 seconds.  In non-animated mode
      this is skipped.
    - Calls to :func:`type_message` will have a ``delay=0.05``.  In non-animated mode
      the ``delay=0.0``.

    These scripts are not intended to be robust.  Features are implemented as needed...
    this is not intended to be a real shell programming language!  See
    ``demos/__main__.py`` for example ``program``'s that can execute.

    Parameters
    ----------
    program : str
        The "shell" program to execute.

    cwd : str
        The directory to execute ``program`` from.

    delay : float
        Pass-through parameter for :func:`type_message`.

    animated : bool
        Whether or not this is an "animated" shell, meaning commands such as
        ``clear`` or ``PAUSE`` should be executed.
    """
    commands = []  # type: List[Any]
    # filter: skip any lines that are only whitespace (l.strip() -> empty -> Falsey).
    for line in filter(lambda l: l.strip(), program.splitlines()):
        # A line of 'PAUSE' calls pause(), also allowed: PAUSE=amount
        if line.startswith("PAUSE"):
            if not animated:
                continue
            parts = line.split("=")
            args = []  # type: List[Any]
            # No checking: if this breaks we want to crash.
            if len(parts) == 2:
                args = [float(parts[1])]
            commands.append([pause, args, {}])
            continue

        # Console lexer style: lines starting with $ are a command to execute.
        # Need to parse a little bit to see if we need to remove `clear` command, but we
        # want to make sure to append `type_message` call to `commands` before finishing
        # processing cmd_line (type command before executing xD).
        if line.startswith("$"):
            cmd_line = shlex.split(line)[1:]  # Remove leading $
            exe_name = cmd_line.pop(0)
            if not animated and exe_name == "clear":
                continue
            is_command = True
        else:
            is_command = False

        # Type out the command first.
        commands.append([type_message, [line], {"delay": delay}])

        # Now that the type_message has been added to commands we can continue
        # processing the rest of the command line.
        if is_command:
            # Special-case rm to just use ci_exec.rm_rf.
            if exe_name == "rm":
                exe = rm_rf  # type: Callable
                # Remove any flags, keep any filenames / folders.
                # NOTE: does *NOT* support globs e.g. *.pyc!
                cmd_args = [arg for arg in cmd_line if not arg.startswith("-")]
                cmd_kwargs = {}  # type: dict
            # Special-case clear to use `clear` defined above.
            elif exe_name == "clear":
                exe = clear
                cmd_args = []
                cmd_kwargs = {}
            # Otherwise, try and create a usable executable.
            else:
                # Map cat to windows builtin type.
                if platform.system() == "Windows" and exe_name == "cat":
                    exe = windows_cmd_builtin("type")
                    cmd_args = cmd_line
                    cmd_kwargs = {}
                # Special case "python" executable to be sys.executable
                elif exe_name in {"python", "python3"}:
                    # Use `coverage run` rather than python to get coverage of demo.
                    if "-c" not in cmd_line and CI_EXEC_DEMOS_COVERAGE:
                        # Create: `coverage` [run, -p, ... other args ...]
                        exe_name = "coverage"
                        cmd_line.insert(0, "-p")  # parallel
                        cmd_line.insert(0, "run")
                    else:
                        exe_name = sys.executable

                # If exe_name is a file path use it.  Otherwise use `which`.
                exe_path = Path(exe_name)
                if exe_path.is_file():
                    exe = Executable(str(exe_path), log_calls=False)
                else:
                    exe = which(exe_name, log_calls=False)

                # Only support redirect of stdout to one file at this time.
                if ">" in cmd_line:
                    redirect_index = cmd_line.index(">")
                    redirect_file = cmd_line[redirect_index + 1]
                    cmd_args = cmd_line[0:redirect_index]
                    cmd_kwargs = {}
                    real_exe = exe  # type: Callable

                    def exe(*args, **kwargs):
                        with open(redirect_file, "w") as f:
                            real_exe(*args, stdout=f)
                else:
                    cmd_args = cmd_line
                    cmd_kwargs = {}

            commands.append([exe, cmd_args, cmd_kwargs])

    with cd(cwd):
        for cmd, args, kwargs in commands:
            cmd(*args, **kwargs)


def run_demo(program: str, cwd: str, animated: bool):
    """
    Run the specified demo program.

    When ``animated=True``, :func:`clear` the screen and sleep for 2 seconds to allow
    recording to begin.  The ``delay`` parameter passed-through to :func:`type_message`
    will be set to ``0.05``.  In non-animated mode the screen will not be cleared,
    and the delay will be ``0.0``.

    Parameters
    ----------
    program : str
        The "shell" program to execute with :func:`mock_shell`.

    cwd : str
        Pass-through parameter to :func:`mock_shell`.

    animated : bool
        Pass-through parameter to :func:`mock_shell`.
    """
    if animated:
        clear()
        time.sleep(2.0)  # allow time to start recording
        delay = 0.05
    else:
        delay = 0.0  # do not delay typing
    mock_shell(program, cwd=cwd, delay=delay, animated=animated)


########################################################################################
def main():
    """Create the argument parser and run the specified demo."""
    Demo = namedtuple("Demo", ["cwd", "program"])

    # NOTE: repo_root is the expected cwd for all demo programs when running through
    # `tox`, not doing so may result in coverage files showing up in unexpected places.
    # Things like `setup.cfg` etc are used to determine what `coverage` is looking for.
    this_file_dir = os.path.abspath(os.path.dirname(__file__))
    repo_root = os.path.dirname(this_file_dir)

    class RawFormatter(argparse.HelpFormatter):
        def _split_lines(self, text, width):
            text = text.strip()
            if text.startswith("RAW(") and text.endswith(")RAW"):
                _, tail = text.split("RAW(")
                head, _ = tail.split(")RAW")
                return head.splitlines()
            return super()._split_lines(text, width)

    parser = argparse.ArgumentParser(
        description="Run a demo program.", formatter_class=RawFormatter
    )
    available_demos = {
        "custom_log_stage": Demo(
            cwd=repo_root,
            program=textwrap.dedent('''
                # Redirection to a file: 80 characters

                PAUSE=0.5

                $ python ./demos/custom_log_stage.py > work
                $ python -c "print('*' * 80)"
                $ cat work
                $ rm -f work

                PAUSE

                $ clear
                # Otherwise: use terminal width

                PAUSE=0.5

                $ python ./demos/custom_log_stage.py
            ''').strip()
        )
    }

    parser.add_argument(
        "demo", type=str, metavar="DEMO", choices=available_demos.keys(),
        help=textwrap.dedent('''
            RAW(The demo to run.  Choices:

            {choices}
            )RAW
        ''').format(choices="".join([
            "- {key}".format(key=key)for key in available_demos.keys()
        ]))
    )
    parser.add_argument(
        "--animated", action="store_true",
        help=(
            "Type commands slowly / keep `clear` and `PAUSE` statements (suitable for "
            "recording).  Default: False, do not type out / pause."
        )
    )

    args = parser.parse_args()

    demo = available_demos[args.demo]
    run_demo(demo.program, demo.cwd, args.animated)


if __name__ == "__main__":
    main()
