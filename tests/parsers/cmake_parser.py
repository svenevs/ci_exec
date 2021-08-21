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
"""Tests for the :mod:`ci_exec.parsers.cmake_parser` module."""

from itertools import chain
from typing import Tuple

from ci_exec.parsers.cmake_parser import CMakeParser
from ci_exec.parsers.utils import env_or_platform_default
from ci_exec.utils import unset_env

import pytest


def default_cc_cxx() -> Tuple[str, str]:
    """Return the default ``(cc, cxx)`` for the current platform."""
    cc = env_or_platform_default(
        env="CC", windows="cl.exe", darwin="clang", other="gcc"
    )
    cxx = env_or_platform_default(
        env="CXX", windows="cl.exe", darwin="clang++", other="g++"
    )

    return (cc, cxx)


def test_cmake_parser_is_x_config_generator():
    """
    Validate |is_single_config_generator| and |is_multi_config_generator|.

    .. |is_single_config_generator| replace::

        :func:`~ci_exec.parsers.cmake_parser.CMakeParser.is_single_config_generator`

    .. |is_multi_config_generator| replace::

        :func:`~ci_exec.parsers.cmake_parser.CMakeParser.is_multi_config_generator`
    """
    for g in chain(CMakeParser.makefile_generators, CMakeParser.ninja_generator):
        assert CMakeParser.is_single_config_generator(g)
        assert not CMakeParser.is_multi_config_generator(g)

    for g in chain(CMakeParser.visual_studio_generators, CMakeParser.other_generators):
        assert not CMakeParser.is_single_config_generator(g)
        assert CMakeParser.is_multi_config_generator(g)


@unset_env("CC", "CXX")
def test_cmake_parser_defaults():
    """Validate the |CMakeParser| defaults are as expected."""
    parser = CMakeParser()
    args = parser.parse_args([])

    assert args.generator == "Ninja"
    assert args.architecture is None
    assert args.toolset is None
    assert not args.shared
    assert not args.static

    cc, cxx = default_cc_cxx()
    assert args.cc == cc
    assert args.cxx == cxx

    assert args.build_type == "Release"

    expected_configure_args = {
        "-G", "Ninja",
        f"-DCMAKE_C_COMPILER={cc}",
        f"-DCMAKE_CXX_COMPILER={cxx}",
        "-DCMAKE_BUILD_TYPE=Release"
    }
    assert set(args.cmake_configure_args) == expected_configure_args
    assert len(args.cmake_build_args) == 0


def test_cmake_parser_add_argument_failues():
    """
    Validate |cm_add_argument| fails with expected names.

    .. |cm_add_argument| replace::

        :func:`~ci_exec.parsers.cmake_parser.CMakeParser.add_argument`
    """
    parser = CMakeParser()

    with pytest.raises(ValueError) as ve_excinfo:
        parser.add_argument("cmake_configure_args")
    assert str(ve_excinfo.value) == "'cmake_configure_args' name is reserved."

    with pytest.raises(ValueError) as ve_excinfo:
        parser.add_argument("cmake_build_args")
    assert str(ve_excinfo.value) == "'cmake_build_args' name is reserved."

    with pytest.raises(ValueError) as ve_excinfo:
        parser.add_argument("extra_args")
    assert str(ve_excinfo.value) == \
        "'extra_args' is reserved.  Set `add_extra_args = False` first."

    parser.add_extra_args = False
    parser.add_argument("extra_args")  # OK


@unset_env("CC", "CXX")
def test_cmake_parser_get_argument():
    """
    Validate |get_argument| finds both flag and dest names.

    .. |get_argument| replace::

        :func:`~ci_exec.parsers.cmake_parser.CMakeParser.get_argument`
    """
    parser = CMakeParser()
    parser.add_argument("-f", "--flag", dest="flag", action="store_true")
    parser.add_argument("positional", type=str, nargs=1)

    # Run through default options added.
    assert parser.get_argument("-G").default == "Ninja"
    assert parser.get_argument("generator").default == "Ninja"

    assert parser.get_argument("-A").default is None
    assert parser.get_argument("architecture").default is None

    assert parser.get_argument("-T").default is None
    assert parser.get_argument("toolset").default is None

    assert not parser.get_argument("--shared").default
    assert not parser.get_argument("shared").default

    assert not parser.get_argument("--static").default
    assert not parser.get_argument("static").default

    cc, cxx = default_cc_cxx()
    assert parser.get_argument("--cc").default == cc
    assert parser.get_argument("cc").default == cc

    assert parser.get_argument("--cxx").default == cxx
    assert parser.get_argument("cxx").default == cxx

    assert parser.get_argument("--build-type").default == "Release"
    assert parser.get_argument("build_type").default == "Release"

    # Run through options user added.
    assert not parser.get_argument("-f").default
    assert not parser.get_argument("--flag").default
    assert not parser.get_argument("flag").default

    assert parser.get_argument("positional").nargs == 1

    # None should be returned when argument not found.
    assert parser.get_argument("--not-here") is None


@unset_env("CC", "CXX")
def test_cmake_parser_remove():
    """
    Validate |remove| can remove registered arguments (except for generator).

    .. |remove| replace::

        :func:`~ci_exec.parsers.cmake_parser.CMakeParser.remove`
    """
    parser = CMakeParser()

    # Cannot remove generator.
    for args in ["-G"], ["generator"], ["-G", "generator"]:
        with pytest.raises(ValueError) as ve_excinfo:
            parser.remove(*args)
        assert str(ve_excinfo.value) == "'generator' argument may not be removed."

    # extra_args is added in parse_args, must be prevented (nothing to remove).
    with pytest.raises(ValueError) as ve_excinfo:
        parser.remove("extra_args")
    assert str(ve_excinfo.value) == (
        "'extra_args' cannot be removed, it must be prevented.  Set "
        "`add_extra_args = False`."
    )

    # Unregistered arguments cannot be removed.
    with pytest.raises(ValueError) as ve_excinfo:
        parser.remove("foo")
    assert str(ve_excinfo.value) == "Cannot remove unregistered arg(s): ['foo']"

    with pytest.raises(ValueError) as ve_excinfo:
        parser.remove("foo", "shared", "bar")  # removes shared (!)
    assert str(ve_excinfo.value) == "Cannot remove unregistered arg(s): ['foo', 'bar']"

    # Test removing items and make sure parse_args doesn't include them.
    flag_to_dest = {
        "-G": "generator",
        "-A": "architecture",
        "-T": "toolset",
        "--shared": "shared",
        "--static": "static",
        "--cc": "cc",
        "--cxx": "cxx",
        "--build-type": "build_type"
    }

    # Test removing one at a time by flags.
    flags = [f for f in flag_to_dest]
    parser = CMakeParser(add_extra_args=False)
    while len(flags) > 1:
        f = flags.pop(0)
        if f == "-G":
            flags.append(f)
            continue

        # Parse args, make sure the attribute was set.
        args = parser.parse_args([])
        assert hasattr(args, flag_to_dest[f])
        assert all(hasattr(args, flag_to_dest[fl]) for fl in flags)
        assert set(parser.flag_map.keys()) == set(flags + [f])
        assert len(parser.flag_map) == len(parser.dest_map)

        # Remove arg, make sure it is gone now but others still remain.
        parser.remove(f)
        args = parser.parse_args([])
        assert not hasattr(args, flag_to_dest[f])
        assert all(hasattr(args, flag_to_dest[fl]) for fl in flags)
        assert set(parser.flag_map.keys()) == set(flags)
        assert len(parser.flag_map) == len(parser.dest_map)

    assert flags == ["-G"]  # testing the test...

    # Test removing one at a time by dests.
    dests = [val for _, val in flag_to_dest.items()]
    parser = CMakeParser(add_extra_args=False)
    while len(dests) > 1:
        d = dests.pop(0)
        if d == "generator":
            dests.append(d)
            continue

        # Parse args, make sure the attribute was set.
        args = parser.parse_args([])
        assert hasattr(args, d)
        assert all(hasattr(args, de) for de in dests)
        assert set(parser.dest_map.keys()) == set(dests + [d])
        assert len(parser.dest_map) == len(parser.flag_map)

        # Remove arg, make sure it is gone now but others still remain.
        parser.remove(d)
        args = parser.parse_args([])
        assert not hasattr(args, d)
        assert all(hasattr(args, de) for de in dests)
        assert set(parser.dest_map.keys()) == set(dests)
        assert len(parser.dest_map) == len(parser.flag_map)

    assert dests == ["generator"]  # testing the test...

    # Remove all flags but generator at once.
    parser = CMakeParser(add_extra_args=False)
    args = parser.parse_args([])
    assert all(hasattr(args, dest) for _, dest in flag_to_dest.items())

    parser.remove(*[flag for flag in flag_to_dest if flag != "-G"])
    args = parser.parse_args([])
    for _, dest in flag_to_dest.items():
        if dest == "generator":
            assert hasattr(args, dest)
        else:
            assert not hasattr(args, dest)

    # Remove all dests but generator at once.
    parser = CMakeParser(add_extra_args=False)
    args = parser.parse_args([])
    assert all(hasattr(args, dest) for _, dest in flag_to_dest.items())

    parser.remove(*[dest for _, dest in flag_to_dest.items() if dest != "generator"])
    args = parser.parse_args([])
    for _, dest in flag_to_dest.items():
        if dest == "generator":
            assert hasattr(args, dest)
        else:
            assert not hasattr(args, dest)


@unset_env("CC", "CXX")
def test_cmake_parser_set_argument():
    """
    Validate |set_argument| can set supported attributes.

    .. |set_argument| replace::

        :func:`~ci_exec.parsers.cmake_parser.CMakeParser.set_argument`
    """
    parser = CMakeParser()

    # Test that unsupported attributes are failed out.
    for kwargs in {"action": "store_false"}, {"nargs": 2, "type": list}:
        with pytest.raises(ValueError) as ve_excinfo:
            parser.set_argument("shared", **kwargs)
        why = str(ve_excinfo.value)
        assert why.startswith(f"Setting attribute{'' if len(kwargs) == 1 else 's'}")
        # NOTE: str.format(set) used, can't assume order so just check `in`.
        for key in kwargs:
            assert key in why
        assert why.endswith("not supported.")

    # Changing generator choies not supported.
    for arg in "-G", "generator":
        with pytest.raises(ValueError) as ve_excinfo:
            parser.set_argument(arg, help="GeNeRaToR", choices={"meh"})
        assert str(ve_excinfo.value) == \
            "Changing 'generator' attribute 'choices' is not supported."

    # Cannot set value of argument that does not exist...
    with pytest.raises(ValueError) as ve_excinfo:
        parser.set_argument("blargh", help="BLARGH")
    assert str(ve_excinfo.value) == "Cannot set attrs of 'blargh', argument not found."

    # Change just one attribute of one argument.
    generator = parser.get_argument("generator")
    assert generator.default == "Ninja"
    parser.set_argument("generator", default="Unix Makefiles")
    assert generator.default == "Unix Makefiles"

    # Change multiple attributes of a different argument.
    build_type = parser.get_argument("build_type")
    assert build_type.default == "Release"
    assert set(build_type.choices) == \
        {"Release", "MinSizeRel", "RelWithDebInfo", "Debug"}
    parser.set_argument("--build-type", choices={"Release", "Debug"}, default="Debug")
    assert build_type.default == "Debug"
    assert set(build_type.choices) == {"Release", "Debug"}


@unset_env("CC", "CXX")
def test_cmake_parser_extra_args():
    """
    Validate |add_extra_args| works as described.

    .. |add_extra_args| replace::

        :attr:`~ci_exec.parsers.cmake_parser.CMakeParser.add_extra_args`
    """
    parser = CMakeParser()

    cc, cxx = default_cc_cxx()
    base_configure_args = [
        "-G", "Ninja",
        f"-DCMAKE_C_COMPILER={cc}",
        f"-DCMAKE_CXX_COMPILER={cxx}",
        "-DCMAKE_BUILD_TYPE=Release"
    ]

    # No extra args given.
    args = parser.parse_args([])
    assert args.cmake_configure_args == base_configure_args
    assert args.cmake_build_args == []

    # Extra args with nothing else set.
    args = parser.parse_args(["--", "-DMYLIB_OPTION=ON", "-Werr=dev"])
    assert args.cmake_configure_args == base_configure_args + [
        "-DMYLIB_OPTION=ON", "-Werr=dev"
    ]
    assert args.cmake_build_args == []

    # Extra args with explicit args given.
    args = parser.parse_args([
        "-G", "Ninja",
        "--cc", cc,
        "--cxx", cxx,
        "--build-type", "Release",
        "--", "-DMYLIB_OPTION=OFF", "-DCMAKE_CXX_FLAGS=-Werror"
    ])
    assert args.cmake_configure_args == base_configure_args + [
        "-DMYLIB_OPTION=OFF", "-DCMAKE_CXX_FLAGS=-Werror"
    ]
    assert args.cmake_build_args == []


@unset_env("CC", "CXX")
def test_cmake_parser_shared_or_static(capsys):
    """Validate ``--shared`` and ``--static`` |CMakeParser| options."""
    def validate_shared_and_or_static(parser: CMakeParser):
        """Verify -DBUILD_SHARED_LIBS is correct with --shared vs --static."""
        # Specifying --shared: -DBUILD_SHARED_LIBS=ON
        args = parser.parse_args(["--shared"])
        assert args.shared
        assert not args.static
        assert "-DBUILD_SHARED_LIBS=ON" in args.cmake_configure_args

        # Specifying --shared: -DBUILD_SHARED_LIBS=OFF
        args = parser.parse_args(["--static"])
        assert args.static
        assert not args.shared
        assert "-DBUILD_SHARED_LIBS=OFF" in args.cmake_configure_args

        # Specifying both: error
        with pytest.raises(SystemExit) as se_excinfo:
            args = parser.parse_args(["--shared", "--static"])
        assert se_excinfo.value.code == 2
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "argument --static: not allowed with argument --shared" in captured.err

        with pytest.raises(SystemExit) as se_excinfo:
            args = parser.parse_args(["--static", "--shared"])
        assert se_excinfo.value.code == 2
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "argument --shared: not allowed with argument --static" in captured.err

    # Default: if neither --shared nor --static specified, NO -DBUILD_SHARED_LIBS.
    optional_parser = CMakeParser()
    args = optional_parser.parse_args([])
    assert not args.shared
    assert not args.static
    assert not any(
        conf.startswith("-DBUILD_SHARED_LIBS") for conf in args.cmake_configure_args
    )

    validate_shared_and_or_static(optional_parser)

    # At least one of `--shared` or `--static` must be provided.
    required_parser = CMakeParser(shared_or_static_required=True)
    with pytest.raises(SystemExit) as se_excinfo:
        args = required_parser.parse_args([])
    assert se_excinfo.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "one of the arguments --shared --static is required" in captured.err

    validate_shared_and_or_static(required_parser)


@unset_env("CC", "CXX")
def test_cmake_parser_parse_args_cmake_configure_args():
    """
    Validate |parse_args| works as expected.

    .. |parse_args| replace::

        :attr:`~ci_exec.parsers.cmake_parser.CMakeParser.parse_args`
    """
    # NOTE: the important test cases are in the sinvle_vs_multi test below.  This is
    # really just testing to make sure that certain arguments only end up in the
    # configure arguments when they are supposed to.
    parser = CMakeParser(add_extra_args=False)

    args = parser.parse_args([])
    assert "-A" not in args.cmake_configure_args
    assert "-T" not in args.cmake_configure_args
    assert not any(
        a.startswith("-DBUILD_SHARED_LIBS=") for a in args.cmake_configure_args
    )

    args = parser.parse_args(["-A", "x64"])
    expected = {"-A", "x64"}
    assert set(args.cmake_configure_args) & expected == expected

    args = parser.parse_args(["-T", "i-dislike-visual-studio"])
    expected = {"-T", "i-dislike-visual-studio"}
    assert set(args.cmake_configure_args) & expected == expected

    args = parser.parse_args(["--shared"])
    expected = {"-DBUILD_SHARED_LIBS=ON"}
    assert set(args.cmake_configure_args) & expected == expected

    args = parser.parse_args(["--static"])
    expected = {"-DBUILD_SHARED_LIBS=OFF"}
    assert set(args.cmake_configure_args) & expected == expected


@unset_env("CC", "CXX")
def test_cmake_parser_single_vs_multi_configure_build_args():
    """Validate that single vs multi config generators affect configure / build args."""
    parser = CMakeParser(add_extra_args=False)

    # Single-config generator: build type is configure argument.
    args = parser.parse_args(["-G", "Ninja", "--build-type", "Debug"])
    assert "-DCMAKE_BUILD_TYPE=Debug" in args.cmake_configure_args
    assert args.cmake_build_args == []

    # Multi-config generator: it is a build argument.
    args = parser.parse_args([
        "-G", "Visual Studio 16 2019", "-A", "x64", "--build-type", "Debug"
    ])
    assert "-DCMAKE_BUILD_TYPE=Debug" not in args.cmake_configure_args
    assert args.cmake_build_args == ["--config", "Debug"]
