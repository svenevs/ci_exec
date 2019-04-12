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
"""Tests for the :mod:`ci_exec.core` module."""

import itertools
import platform
import re
import shutil
import sys
from pathlib import Path
from subprocess import PIPE

from ci_exec.colorize import Ansi, Colors, Styles, colorize
from ci_exec.core import Executable, fail, mkdir_p, rm_rf, which

import pytest


@pytest.mark.parametrize(
    "why,exit_code,no_prefix",
    [
        (why, exit_code, no_prefix)
        for why in ("super fail", "failure of death")
        for exit_code in (1, 2, 128)
        for no_prefix in (False, True)
    ]
)
def test_fail(capsys, why: str, exit_code: int, no_prefix: bool):
    """Validate :func:`~ci_exec.core.fail` exits as expected."""
    with pytest.raises(SystemExit) as se_excinfo:
        # Make sure calling this raises SystemExit with appropriate code.
        fail(why, exit_code=exit_code, no_prefix=no_prefix)

    # Make sure we exited with the expected code.
    assert se_excinfo.value.code == exit_code

    # Check printout of sys.stderr and make sure expected message was printed.
    if no_prefix:
        prefix = ""
    else:
        prefix = colorize("[X] ", color=Colors.Red, style=Styles.Bold)
    expected_error_message = "{prefix}{why}\n".format(prefix=prefix, why=why)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == expected_error_message


def test_executable_construction_failures():
    """Validate that non-absolute and non-(executable)file constructions will raise."""
    # There is no `git` executable in this directory (user should have used `which`).
    with pytest.raises(ValueError) as relative_excinfo:
        Executable("git")
    assert str(relative_excinfo.value) == "The path 'git' is not a file."

    # It must be a file that exists.
    here = Path(".").resolve()
    with pytest.raises(ValueError) as non_file_excinfo:
        Executable(str(here / "this_file_is_not_here"))
    non_file_msg = str(non_file_excinfo.value)
    assert non_file_msg.startswith("The path '")
    not_here = str(Path(".").resolve() / "this_file_is_not_here")
    assert non_file_msg.endswith("{not_here}' is not a file.".format(not_here=not_here))

    # It must be executable.
    tox_ini = str(here / "tox.ini")
    with pytest.raises(ValueError) as non_executable_excinfo:
        Executable(tox_ini)
    if platform.system() == "Windows":
        not_exe = "Extension of '{tox_ini}' is not in PATHEXT.".format(tox_ini=tox_ini)
    else:
        not_exe = "The path '{tox_ini}' is not executable.".format(tox_ini=tox_ini)
    assert str(non_executable_excinfo.value) == not_exe


def test_executable_relative():
    """Validate :class:`~ci_exec.core.Executable` accepts relative paths."""
    if platform.system() != "Windows":
        scripty_path = "./scripty.sh"
        with open(scripty_path, "w") as scripty:
            scripty.write("#!/bin/sh\necho 'hi, my name is scripty :)'\n")
        chmod = which("chmod")
        chmod("+x", scripty_path)
        scripty = Executable(scripty_path, log_calls=False)
        proc = scripty(stdout=PIPE, stderr=PIPE)
        assert proc.returncode == 0
        assert proc.stderr == b""
        assert proc.stdout.decode("utf-8") == "hi, my name is scripty :)\n"
        rm_rf(scripty_path)


def test_executable_logging(capsys):
    """Validate :class:`~ci_exec.core.Executable` runs and logs as expected."""
    # NOTE: capsys is not able to capture subprocess.run() output directly, so what we
    # do instead is run with PIPEs and print it to simulate how it would run normally.
    pipe = {"stdout": PIPE, "stderr": PIPE}

    def run_and_print(exe: Executable, *args, **kwargs) -> str:
        """Run the executable and print to stdout / stderr, return expected logging."""
        proc = exe(*args, **kwargs)
        assert proc.returncode == 0
        print(proc.stderr.decode("utf-8"), file=sys.stderr, end="")
        print(proc.stdout.decode("utf-8"), end="")
        if exe.log_calls:
            popen_args = (exe.exe_path, *args)
            message = "{log_prefix}{cmd_line}".format(
                log_prefix=exe.log_prefix,
                cmd_line=" ".join(popen_args)
            )
            if exe.log_color:
                message = colorize(message, color=exe.log_color, style=exe.log_style)
            return message
        else:
            return ""

    def startswith(out: str, prefix: str, color: str, style: str) -> bool:
        """External check for cross-validating run_and_print."""
        colored_prefix = colorize(prefix, color=color, style=style)
        colored = colored_prefix.split(Ansi.Clear)[0]
        return out.startswith(colored)

    git = which("git")
    log_template = "{logged}\norigin\n"

    # Test default logging (bold cyan).
    logged = run_and_print(git, "remote", **pipe)
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == log_template.format(logged=logged)
    assert startswith(captured.out, "$ ", Colors.Cyan, Styles.Bold)

    # Test custom log color.
    git.log_color = Colors.Magenta
    logged = run_and_print(git, "remote", **pipe)
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == log_template.format(logged=logged)
    assert startswith(captured.out, "$ ", Colors.Magenta, Styles.Bold)

    # Test custom log style.
    git.log_style = Styles.BoldInverted
    logged = run_and_print(git, "remote", **pipe)
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == log_template.format(logged=logged)
    assert startswith(captured.out, "$ ", Colors.Magenta, Styles.BoldInverted)

    # Test custom log prefix.
    git.log_prefix = ">>> "
    logged = run_and_print(git, "remote", **pipe)
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == log_template.format(logged=logged)
    assert startswith(captured.out, ">>> ", Colors.Magenta, Styles.BoldInverted)

    # Test log without colors.
    git.log_color = None
    logged = run_and_print(git, "remote", **pipe)
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out.startswith(">>> ")

    # Test log turned off only outputs command.
    git.log_calls = False
    run_and_print(git, "remote", **pipe)
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == "origin\n"


def test_executable_failures(capsys):
    """Validate failing executables error as expected."""
    git = which("git", log_calls=False)

    # By default, failed invocations terminate.  Make sure this happens.
    # NOTE: as with test_executable_logging, capsys doesn't capture subprocess.run.
    # Check for `git` failure message in non-terminating tests below where we capture
    # using PIPE.
    pipe = {"stdout": PIPE, "stderr": PIPE}
    with pytest.raises(SystemExit) as se_excinfo:
        git("log", "--petty=%B", **pipe)

    captured = capsys.readouterr()
    assert re.match(r".*non-zero exit status (\d+)\.?", captured.err).group(1) == "128"
    assert se_excinfo.value.code == 128

    # Using check=False tells subprocess.run not to raise an Exception.

    proc = git("log", "--petty=%B", check=False, **pipe)
    assert proc.returncode == 128
    assert proc.stdout == b""
    assert b"fatal" in proc.stderr
    assert b"unrecognized argument" in proc.stderr
    assert b"--petty=%B" in proc.stderr

    # Clear capsys before this test.
    captured = capsys.readouterr()

    # Test that invalid kwargs to subprocess.run fail.
    with pytest.raises(SystemExit) as se_excinfo:
        git("status", not_valid_subprocess_kwarg=True)
    assert se_excinfo.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Executable.__call__: invalid kwarg(s) for subprocess.run" in captured.err
    assert "unexpected keyword argument 'not_valid_subprocess_kwarg'" in captured.err


def test_mkdir_p(capsys):
    """Validate that :func:`~ci_exec.core.mkdir_p` creates directories as expected."""
    # Relative paths should be ok.
    hello = Path("hello")
    rm_rf(hello)  # in case previous tests failed, start clean

    mkdir_p(hello)
    assert hello.is_dir()

    # Already exists, but this is ok (real test is that it doesn't fail).
    hello = hello.resolve()
    mkdir_p(hello)
    assert hello.is_dir()

    # Strings are allowed.
    mkdir_p("hello")
    assert hello.is_dir()

    # Long chains should be allowed.
    hello_there = hello / "there"
    hello_there_beautiful = hello_there / "beautiful"
    hello_there_beautiful_world = hello_there_beautiful / "world"

    def repeat():
        mkdir_p(hello_there_beautiful_world)
        assert hello.is_dir()
        assert hello_there.is_dir()
        assert hello_there_beautiful.is_dir()
        assert hello_there_beautiful_world.is_dir()

    repeat()  # because
    repeat()  # why
    repeat()  # not? xD

    # Cleanup hello/there/beautiful/world and create file hello/there to test errors.
    rm_rf(hello_there)
    assert hello.is_dir()
    with hello_there.open("w") as f:
        f.write("beautiful world\n")
    assert hello_there.is_file()

    with pytest.raises(SystemExit):
        mkdir_p(hello_there)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Unable to mkdir_p" in captured.err
    if platform.system() == "Windows":
        assert "file already exists" in captured.err
    else:
        assert "File exists:" in captured.err

    # TODO: how to safely engineer permission access errors on all platforms?
    #       Concern: don't eff people over if they ran tests as `root`

    # Cleanup
    rm_rf(hello)
    assert not hello.is_dir()


def test_rm_rf(capsys):
    """Validate :func:`~ci_exec.core.rm_rf` deletes files / directories as expected."""
    def stage(spec: dict):
        """
        Create the stage to (selectively) delete.

        Parameters
        ----------
        spec : dict
            All keys must be strings.  Values may either be strings (indicating a file
            is to be written), or a dictionary (nested directory) with string keys and
            values being strings or dict as well.

        Return
        ------
        tuple(List[Path], List[Path])
            The created ``(files, directories)`` in that order.
        """
        all_files = []
        all_directories = []

        def make_children(parent, next_spec):
            for key, item in next_spec.items():
                this_kid = parent / key
                if isinstance(item, str):
                    with this_kid.open("w") as f:
                        f.write(item)
                    all_files.append(this_kid)
                else:  # assumed to be dict!
                    mkdir_p(this_kid)
                    all_directories.append(this_kid)
                    make_children(this_kid, item)

        make_children(Path(".").resolve(), spec)
        return (all_files, all_directories)

    spec = {
        "hi": {
            "there.txt": "a file with some text\n",
            "there": {
                "beautiful": {
                    "file.ya": "how interesting, another file ya?\n",
                    "world": {
                        "FILEZ": "don't need extensions :p\n"
                    }
                }
            },
            "another": {
                "directory": {
                    "goes": {
                        "all": {
                            "the": {
                                "way": {
                                    "down": {
                                        "here": "!!!\n"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    # Create the stage.
    files, directories = stage(spec)

    # May as well check (?)
    for f in files:
        assert f.is_file()
    for d in directories:
        assert d.is_dir()

    # Deleting hi means they are all gone.
    rm_rf("hi")
    for fd in itertools.chain(files, directories):
        assert not fd.exists()

    # Recreate stage and selectively delete some things.
    files, directories = stage(spec)
    hi_there_txt = Path("hi") / "there.txt"
    assert hi_there_txt.is_file()
    rm_rf(hi_there_txt)
    assert not hi_there_txt.exists()

    # Creating a symbolic link is the only way I know of to raise an exception here.
    # rmtree does not allow removal of symlinks.
    # NOTE: see https://docs.python.org/3/library/pathlib.html#pathlib.Path.symlink_to
    # Can only test directory links on windows.
    hi_there = (Path("hi") / "there").resolve()  # make sure target is absolute
    assert hi_there.is_dir()
    hi_you = Path("hi") / "you"
    hi_you.symlink_to(hi_there, target_is_directory=True)

    with pytest.raises(SystemExit):
        rm_rf(hi_you)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Cannot call rmtree on a symbolic link" in captured.err

    # Cleanup: remove hi completely
    rm_rf("hi")


def test_which(capsys):
    """Validate that :func:`~ci_exec.core.which` finds or does not find executables."""
    # Make sure ci_exec.core.which and shutil.which agree (how could then not? xD).
    git = which("git")
    git_path = shutil.which("git")
    assert git.exe_path == git_path

    # This command should not exist.  Right?
    no_cmd = "ja" * 22
    with pytest.raises(SystemExit) as se_excinfo:
        which(no_cmd)
    assert se_excinfo.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    prefix = colorize("[X] ", color=Colors.Red, style=Styles.Bold)
    expected_error_message = "{prefix}Could not find '{no_cmd}' in $PATH.\n".format(
        prefix=prefix, no_cmd=no_cmd
    )
    assert captured.err == expected_error_message

    # Test manual $PATH override / make sure same python is found.
    actual_python = Path(sys.executable)
    python_name = actual_python.name
    python_dir = str(actual_python.parent)
    python = which(python_name, path=python_dir, log_calls=False)
    assert python.exe_path == str(actual_python)

    # Throwing in the __str__ test here because it doesn't deserve its own test method.
    assert str(python) == "Executable('{py}')".format(py=str(actual_python))

    proc = python("-c", "import sys; print(sys.version_info)", stdout=PIPE, stderr=PIPE)
    assert proc.returncode == 0
    assert proc.stderr == b""
    assert proc.stdout.decode("utf-8").strip() == "{v}".format(v=sys.version_info)

    # :)
    with pytest.raises(TypeError) as te_excinfo:
        which("git", log_callz=False)
    assert "unexpected keyword argument 'log_callz'" in str(te_excinfo.value)
