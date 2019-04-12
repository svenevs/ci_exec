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
"""Tests for the :mod:`ci_exec.utils` module."""

import os
import platform
from pathlib import Path
from typing import Optional, Union

from ci_exec.core import mkdir_p, rm_rf
from ci_exec.utils import cd, merge_kwargs

import pytest


def test_cd(capsys):
    """Validate :class:`~ci_exec.utils.cd` behaves as expected."""
    def wrap_cd(*, src: Union[Path, str], dest: Union[Path, str], create: bool,
                err_endswith: Optional[str] = None, err_has: Optional[list] = None):
        """
        Test both versions of cd (decorator and context manager).

        Parameters
        ----------
        src : Path or str
            The directory to start in.  Assumed to be a valid place to cd to.

        dest : Path or str
            The directory to test changing to.

        create : bool
            Pass-through argument to ``cd``: whether or not to create ``dest``.

        err_endswith : str or None
            If this string is provided, then it is assumed that ``cd`` to ``dest`` will
            cause an error and we should validate that the captured ``stderr`` ends with
            the value supplied here.

        err_has : list or None
            If provided, this list contains strings to check ``x in`` captured
            ``stderr`` for each ``x in err_has``.
        """
        # NOTE: see cd.__init__ for why we are avoiding resolve()
        src_path = Path(os.path.abspath(str(Path(src).expanduser())))
        dest_path = Path(os.path.abspath(str(Path(dest).expanduser())))
        # Double-whammy testing.
        with cd(src):
            # Make sure we ended up in src
            assert str(Path.cwd()) == str(src_path)

            # Version 1: context manager approach.
            def context_cd():
                with cd(dest, create=create):
                    assert str(Path.cwd()) == str(dest_path)

            # Version 2: decorator approach.
            @cd(dest, create=create)
            def decorated_cd():
                assert str(Path.cwd()) == str(dest_path)

            # Convenience wrapper for checking both succeed or error.
            def assert_cd(func):
                if any([err_endswith, err_has]):
                    with pytest.raises(SystemExit):
                        func()
                    captured = capsys.readouterr()
                    assert captured.out == ""
                    if err_endswith:
                        assert captured.err.strip().endswith(err_endswith)
                    if err_has:
                        for err in err_has:
                            assert err in captured.err
                else:
                    func()

            # Start clean with each test.  Allow existing file tests to fail.
            if create and dest_path.is_dir():
                rm_rf(dest)
            assert_cd(context_cd)
            assert str(Path.cwd()) == str(src_path)  # Make sure we end up back in src.

            # Start clean with each test.  Allow existing file tests to fail.
            if create and dest_path.is_dir():
                rm_rf(dest)
            assert_cd(decorated_cd)
            assert str(Path.cwd()) == str(src_path)  # Make sure we end up back in src.

    starting_cwd = str(Path.cwd())

    # Make sure we can navigate to the same place.  Because why not?
    with cd(starting_cwd):
        assert str(Path.cwd()) == starting_cwd
        with cd(starting_cwd):
            assert str(Path.cwd()) == starting_cwd
            with cd(starting_cwd):
                assert str(Path.cwd()) == starting_cwd
            assert str(Path.cwd()) == starting_cwd
        assert str(Path.cwd()) == starting_cwd
    assert str(Path.cwd()) == starting_cwd

    # Make sure we can get to directories that currently exist.
    wrap_cd(src=".", dest="..", create=False)
    assert str(Path.cwd()) == starting_cwd
    wrap_cd(src=".", dest="~", create=False)
    assert str(Path.cwd()) == starting_cwd

    # With create=True on something that is a file, error ripples from mkdir_p.
    supertest = Path(".").resolve() / "supertest"
    with supertest.open("w") as f:
        f.write("supertest!\n")

    err_has = ["Unable to mkdir_p"]
    if platform.system() == "Windows":
        err_has.append("file already exists")
    else:
        err_has.append("File exists:")
    wrap_cd(src=".", dest=supertest, create=True, err_has=err_has)
    rm_rf(supertest)
    assert str(Path.cwd()) == starting_cwd

    # When create=False with directory that does not exist we expect a failure.
    not_a_directory = "not_a_directory"
    rm_rf(not_a_directory)
    wrap_cd(src=".", dest=not_a_directory, create=False,
            err_endswith="not_a_directory' is not a directory, but create=False.")
    assert not Path(not_a_directory).is_dir()
    assert str(Path.cwd()) == starting_cwd

    # Make sure that we can create it as expected.
    mkdir_p(not_a_directory)  # only here for coverage in wrap_cd (first rm_rf(dest))
    wrap_cd(src=".", dest=not_a_directory, create=True)
    assert Path(not_a_directory).is_dir()
    rm_rf(not_a_directory)
    assert str(Path.cwd()) == starting_cwd

    # v2: multiple directories that don't exist with create=False expects failure.
    not_a_directory = Path("not") / "a" / "directory"
    rm_rf("not")
    wrap_cd(src=".", dest=not_a_directory, create=False,
            err_endswith="directory' is not a directory, but create=False.")
    assert not Path("not").is_dir()
    assert not (Path("not") / "a").is_dir()
    assert not not_a_directory.is_dir()
    assert str(Path.cwd()) == starting_cwd

    # Make sure we can create multiple directories at once.
    rm_rf("not")
    wrap_cd(src=".", dest=not_a_directory, create=True)
    assert Path("not").is_dir()
    assert (Path("not") / "a").is_dir()
    assert not_a_directory.is_dir()
    rm_rf("not")
    assert str(Path.cwd()) == starting_cwd

    # Test first failure case in cd.__enter__ where cwd() cannot be found.  Maybe there
    # is an easier way to test this?
    def uh_uh_uh(*args, **kwargs):
        raise RuntimeError("You didn't say the magic word!")

    first = Path(".").resolve() / "first"
    second = first / "second"
    third = second / "third"

    path_cwd = Path.cwd
    Path.cwd = uh_uh_uh
    with pytest.raises(SystemExit):
        with cd(third, create=True):
            pass  # pragma: nocover
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.strip().endswith(
        "cd: could not get current working directory: You didn't say the magic word!"
    )
    Path.cwd = path_cwd
    assert str(Path.cwd()) == starting_cwd

    # Test second failure case in cd.__enter__ where os.chdir does not succeed.
    rm_rf(first)
    os_chdir = os.chdir
    os.chdir = uh_uh_uh
    with pytest.raises(SystemExit):
        with cd(third, create=True):
            pass  # pragma: nocover
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.strip().endswith(
        "cd: could not change directories to '" + str(third) +
        "': You didn't say the magic word!"
    )
    os.chdir = os_chdir
    rm_rf(first)
    assert str(Path.cwd()) == starting_cwd

    # Test failure case in cd.__exit__ where we cannot return.
    with pytest.raises(SystemExit):
        with cd(third, create=True):
            with cd(second):
                rm_rf(first)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "cd: could not return to " + str(third) in captured.err
    assert str(Path.cwd()) == starting_cwd


def test_merge_kwargs():
    """Validate :func:`~ci_exec.utils.merge_kwargs` merges as expected."""
    def abc(a: int = 1, b: int = 2, c: int = 3):
        """Original function to customize."""
        return a + b + c

    def permute_assert(func, *, a, b, c):
        """Assert default values of a, b, and c are currect for func."""
        assert func(a=0, b=0, c=0) == 0

        assert func(b=0, c=0) == a
        assert func(a=0, c=0) == b
        assert func(a=0, b=0) == c

        assert func(c=0) == a + b
        assert func(b=0) == a + c
        assert func(a=0) == b + c

        assert func() == a + b + c

    # Validate the default values.
    permute_assert(abc, a=1, b=2, c=3)

    # Was this really necessary?  No.  Hehehe.  Python is so flexible though xD
    def manufacture(**outer_kwargs):
        """Create a custom override."""
        def custom(**kwargs):
            return abc(**merge_kwargs(outer_kwargs, kwargs))
        return custom

    custom_a = manufacture(a=4)
    custom_b = manufacture(b=5)
    custom_c = manufacture(c=6)
    permute_assert(custom_a, a=4, b=2, c=3)
    permute_assert(custom_b, a=1, b=5, c=3)
    permute_assert(custom_c, a=1, b=2, c=6)

    custom_ab = manufacture(a=7, b=8)
    custom_ac = manufacture(a=9, c=10)
    custom_bc = manufacture(b=11, c=12)
    permute_assert(custom_ab, a=7, b=8, c=3)
    permute_assert(custom_ac, a=9, b=2, c=10)
    permute_assert(custom_bc, a=1, b=11, c=12)

    custom_abc = manufacture(a=13, b=14, c=15)
    permute_assert(custom_abc, a=13, b=14, c=15)
