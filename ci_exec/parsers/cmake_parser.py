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
"""Module for `CMake <https://cmake.org/>`_ focused argument parser |CMakeParser|."""

import argparse
from typing import Any, Dict, Optional

from .utils import env_or_platform_default


class CMakeParser(argparse.ArgumentParser):
    """
    A `CMake <https://cmake.org/>`_ focused argument parser.

    The goal of this parser is to fold some of the more common flags used by many CMake
    projects and parse them into ``cmake_configure_args`` and ``cmake_build_args``
    automatically.  Expected workflow is::

        from ci_exec import CMakeParser, cd, which

        parser = CMakeParser(description="Mylib CI Builder")
        # ... add any extra arguments specific to project ...
        # parser.add_argument("--foo", ...)

        # Parse arguments.  cmake_{configure,build}_args are parsed for you, and are a
        # list of strings (possibly empty).
        args = parser.parse_args()
        configure_args = args.cmake_configure_args
        build_args = args.cmake_build_args

        # Use the configure / build args created for you by CMakeParser.
        cmake = which("cmake")
        with cd("build", create=True):
            cmake("..", *configure_args)
            cmake("--build", ".", *build_args)

    This is helpful for situations where how users are expected to interact with CMake
    changes depending on the generator chosen.  A reputable example being the build type
    for single-config vs multi-config generators:

    - Single-config: configure with ``-DCMAKE_BUILD_TYPE=<build_type>``
    - Multi-config: build with ``--config <build_type>``

    The command line arguments added here should be appropriate for most projects that
    obey typical CMake practices, but is as customizable as possible.  Command-line
    argument values such as the ``help`` string or ``default`` value can be changed with
    :func:`set_argument`.  Arguments added by this parser that are not desired can be
    removed using :func:`remove`.

    .. note::

        The documentation makes a distinction between *registered* and *unregistered*
        arguments.

        **Registered**
            A flag that this parser adds in the constructor, and will later use to
            populate ``cmake_configure_args`` and ``cmake_build_args``.

        **Unregistered**
            Any arguments that the user adds.  This parser does not keep track of them
            (``parser.add_argument("--foo", ...)`` in example above).

    The registered command-line arguments added are as follows:

    ``-G`` (``args.generator``) -- default: ``Ninja``
        The CMake generator to use.  Pass-through configure argument ``cmake -G``.
        Generator choices are validated, however:

        1. `Extra Generators`__ are not supported.
        2. The now deprecated ``Visual Studio XX YYYY Win64`` format with ``Win64`` is
           parsed as an **error**.  Users should take advantage of ``-A``.

        __ https://cmake.org/cmake/help/latest/manual/cmake-generators.7.html#extra-generators

    ``-A`` (``args.architecture``) -- default: ``None``
        The CMake architecture to build.  Pass-through configure argument ``cmake -A``.
        **Not validated**, invalid arguments (e.g., ``-A`` provided when generator does
        not support it) will result in the cmake configure step failing.

    ``-T`` (``args.toolset``) -- default: ``None``
        The CMake toolset to use.  Pass-through configure argument ``cmake -T``.  **Not
        validated**, invalid arguments (e.g., ``-T`` provided when generator does not
        support it) will result in the cmake configure step failing.

    ``--shared`` (``args.shared``) -- default: ``False``
        Add ``-DBUILD_SHARED_LIBS=ON`` to configure arguments?  Conflicts with
        ``--static`` flag.

        See also: ``shared_or_static_required`` constructor parameter.

    ``--static`` (``args.static``) -- default: ``False``
        Add ``-DBUILD_SHARED_LIBS=OFF`` to configure arguments?  Conflicts with
        ``--shared`` flag.

        See also: ``shared_or_static_required`` constructor parameter.

    ``--cc`` (``args.cc``) -- default: *platform dependent*
        The C compiler to use.  If the generator requested is a single-config generator,
        then the ``-DCMAKE_C_COMPILER={args.cc}`` configure argument.  Multi-config
        generators such as Visual Studio or Xcode will ignore this flag.

        Default: ``$CC`` environment variable **if set**, otherwise:

        +----------+------------+
        | Platform | Default    |
        +==========+============+
        | Windows  | ``cl.exe`` |
        +----------+------------+
        | Darwin   | ``clang``  |
        +----------+------------+
        | Other    | ``gcc``    |
        +----------+------------+

    ``--cxx`` (``args.cxx``) -- default: *platform dependent*
        The C++ compiler to use.  Like ``--cc``, adds
        ``-DCMAKE_CXX_COMPILER={args.cxx}`` configure argument for single-config
        generators.

        Default: ``$CXX`` environment variable **if set**, otherwise:

        +----------+-------------+
        | Platform | Default     |
        +==========+=============+
        | Windows  | ``cl.exe``  |
        +----------+-------------+
        | Darwin   | ``clang++`` |
        +----------+-------------+
        | Other    | ``g++``     |
        +----------+-------------+

    ``--build-type`` (``args.build_type``) -- default: ``Release``
        For single-config generators, this will result in a configure argument of
        ``-DCMAKE_BUILD_TYPE={args.build_type}``.  For multi-config generators, results
        in ``["--config", "{args.build_type}"]`` in the ``cmake_build_args``.

        Choices: ``Release``, ``Debug``, ``RelWithDebInfo``, and ``MinSizeRel``.

    ``[extra_args]`` (``args.extra_args``) -- default: ``[]``
        By default, a positional argument with ``nargs="*"`` (meaning 0 or more) will
        be added.  These are parsed as anything after the ``--`` sequence, and will be
        added directly to ``cmake_configure_args``.  This supports users doing something
        like:

        .. code-block:: console

            $ python .ci/build.py --shared
            # args.extra_args = []

            $ python .ci/build.py --shared -- -Werror=dev -DMYLIB_DEV=ON
            # args.extra_args = ["-Werror=dev", "-DMYLIB_DEV=ON"]

            $ python .ci/build.py --shared -- -DMYLIB_DEV=OFF
            # args.extra_args = ["-DMYLIB_DEV=OFF"]

        .. note::

            This positional argument can be disabled two ways::

                # Option 1: at construction.
                parser = CMakeParser(add_extra_args=False)

                # Option 2: set attribute to False *BEFORE* calling parse_args()
                parser = CMakeParser()
                parser.add_extra_args = False
                args = parser.parse_args()

            Since this is a positional argument consuming ``nargs="*"``, it must be
            added last in order for users to add their own positional arguments.  The
            way this is implemented is by having :func:`parse_args` actually add the
            argument, which means:

            1. It must be disabled before ``parser.parse_args()`` is called to prevent.
            2. Unlike other arguments, it's attributes such as default value of ``[]``
               or help string cannot be changed.

    Parameters
    ----------
    add_extra_args : bool
        Default: ``True``, support ``[extra_args]`` CMake configure arguments at the end
        of the command-line, after the ``--`` sequence (see above).

    shared_or_static_required : bool
        Default: ``False``.  The ``--shared`` and ``--static`` flags are added using
        :meth:`~python:argparse.ArgumentParser.add_mutually_exclusive_group`, this is
        a pass-through parameter::

            shared_or_static = self.add_mutually_exclusive_group(
                required=shared_or_static_required
            )

        - When ``False``, if neither ``--shared`` nor ``--static`` are supplied, then
          ``args.cmake_configure_args`` will **not** contain any
          ``-DBUILD_SHARED_LIBS=[val]`` entries.
        - When ``True``, one of ``--shared`` or ``--static`` must be provided, meaning
          that ``args.cmake_configure_args`` will **always** contain either
          ``-DBUILD_SHARED_LIBS=ON`` or ``-DBUILD_SHARED_LIBS=OFF``.

        Typically CMake projects will
        ``option(BUILD_SHARED_LIBS "Build shared libraries?" OFF)``, meaning that if
        not specified ``--static`` is implied.  This is because the default behavior
        of ``add_library`` with no explicit ``SHARED|STATIC`` is ``STATIC``.  However,
        if a project defaults ``BUILD_SHARED_LIBS`` to ``ON``, requiring ``--shared``
        or ``--static`` be explicitly provided can help ensure that dependencies etc
        will all receive the same ``BUILD_SHARED_LIBS`` arguments.

    **kwargs
        All other parameters are forwarded to :class:`python:argparse.ArgumentParser`.
        Note that every parameter to the |CMakeParser| class must be specified as a
        keyword-only argument.  Positional arguments are disabled.

    Attributes
    ----------
    add_extra_args : bool
        Whether or not CMake configure arguments after ``--`` sequence will be added.

    flag_map : dict
        Mapping of string flag keys (e.g., ``"-G"``, or ``"--build-type"``) to the
        actual :class:`~python:argparse.Action` of all registered arguments.  Direct
        usage discouraged by users, use :func:`get_argument` or :func:`set_argument`
        instead.

    dest_map : dict
        Mapping of string ``dest`` keys (e.g., ``"generator"`` or ``"build_type"``) to
        the actual :class:`~python:argparse.Action` of all registered arguments.  Direct
        usage discouraged by users, use :func:`get_argument` or :func:`set_argument`
        instead.
    """  # noqa: E501

    makefile_generators = {
        "Borland Makefiles",
        "MSYS Makefiles",
        "MinGW Makefiles",
        "NMake Makefiles",
        "NMake Makefiles JOM",
        "Unix Makefiles",
        "Watcom WMake"
    }
    """
    The `Makefile Generators`__.

    __ https://cmake.org/cmake/help/latest/manual/cmake-generators.7.html#makefile-generators
    """  # noqa: E501

    ninja_generator = {"Ninja"}
    """
    The `Ninja Generator`__.

    __ https://cmake.org/cmake/help/latest/generator/Ninja.html
    """

    ninja_multi_generator = {"Ninja Multi-Config"}
    """
    The `Ninja Multi-Config Generator`__.

    __ https://cmake.org/cmake/help/latest/generator/Ninja%20Multi-Config.html
    """

    visual_studio_generators = {
        "Visual Studio 9 2008",
        "Visual Studio 10 2010",
        "Visual Studio 11 2012",
        "Visual Studio 12 2013",
        "Visual Studio 14 2015",
        "Visual Studio 15 2017",
        "Visual Studio 16 2019",
        "Visual Studio 17 2022"
    }
    """
    The `Visual Studio Generators`__.

    __ https://cmake.org/cmake/help/latest/manual/cmake-generators.7.html#visual-studio-generators
    """  # noqa: E501

    other_generators = {"Green Hills MULTI", "Xcode"}
    """
    The `Other Generators`__.

    __ https://cmake.org/cmake/help/latest/manual/cmake-generators.7.html#other-generators
    """  # noqa: E501

    @classmethod
    def is_multi_config_generator(cls, generator: str) -> bool:
        """Whether or not string ``generator`` is a multi-config generator."""
        return generator in (cls.visual_studio_generators | cls.other_generators |
                             cls.ninja_multi_generator)

    @classmethod
    def is_single_config_generator(cls, generator: str) -> bool:
        """Whether or not string ``generator`` is a single-config generator."""
        return generator in (cls.makefile_generators | cls.ninja_generator)

    def __init__(self, *, add_extra_args: bool = True,
                 shared_or_static_required: bool = False, **kwargs):
        if "formatter_class" not in kwargs:
            kwargs["formatter_class"] = argparse.ArgumentDefaultsHelpFormatter
        self.add_extra_args = add_extra_args  # see parse_args
        self.flag_map = {}  # type: Dict[str, argparse.Action]
        self.dest_map = {}  # type: Dict[str, argparse.Action]

        super().__init__(**kwargs)

        # The generator to use.  Slightly restrictive: "Visual Studio X YYYY Win64" will
        # fail, need to do -G "Visual Studio X YYY" -A x64
        self._register_argument(
            "-G", dest="generator", type=str, default="Ninja", metavar="GENERATOR",
            help="Generator to use (CMake -G flag).",
            choices=sorted(
                self.makefile_generators | self.ninja_generator |
                self.ninja_multi_generator | self.visual_studio_generators |
                self.other_generators
            )
        )

        # Architecture configure argument.
        self._register_argument(
            "-A", dest="architecture", type=str, default=None,
            help=(
                "Target architecture (CMake -A flag).  Not validated.  Example: -G "
                "'Visual Studio 16 2019' -A x64"
            )
        )

        # Toolset configure argument.
        self._register_argument(
            "-T", dest="toolset", type=str, default=None,
            help=(
                "Toolset to use (CMake -T flag).  Not validated, must be valid for "
                "specified generator / architecture."
            )
        )

        # BUILD_SHARED_LIBS.  Only populated if explicitly requested.
        shared_or_static = self.add_mutually_exclusive_group(
            required=shared_or_static_required
        )

        shared = shared_or_static.add_argument(
            "--shared", dest="shared", action="store_true",
            help="Build shared libraries?  Adds -DBUILD_SHARED_LIBS=ON configure arg."
        )
        self.flag_map["--shared"] = shared
        self.dest_map["shared"] = shared

        static = shared_or_static.add_argument(
            "--static", dest="static", action="store_true",
            help="Build static libraries?  Adds -DBUILD_SHARED_LIBS=OFF configure arg."
        )
        self.flag_map["--static"] = static
        self.dest_map["static"] = static

        # The default C compiler to use.
        cc = env_or_platform_default(
            env="CC", windows="cl.exe", darwin="clang", other="gcc"
        )
        self._register_argument(
            "--cc", dest="cc", type=str, default=cc,
            help="The CMAKE_C_COMPILER to use for single-config generators."
        )

        # The default C++ compiler to use.
        cxx = env_or_platform_default(
            env="CXX", windows="cl.exe", darwin="clang++", other="g++"
        )
        self._register_argument(
            "--cxx", dest="cxx", type=str, default=cxx,
            help="The CMAKE_CXX_COMPILER to use for single-config generators."
        )

        # CMAKE_BUILD_TYPE or --config <build_type> for multiconfig build.
        self._register_argument(
            "--build-type", dest="build_type", type=str, default="Release",
            choices=["Release", "Debug", "RelWithDebInfo", "MinSizeRel"],
            help=(
                "For single-config generators, specifies the CMAKE_BUILD_TYPE to "
                "configure with.  For multi-config generators, ['--config', "
                "'<build_type>'] is returned for use with `cmake --build`."
            )
        )

    def add_argument(self, *args, **kwargs) -> argparse.Action:
        """
        Add an argument to the parser.

        .. |add_argument| replace:: :meth:`~python:argparse.ArgumentParser.add_argument`

        Parameters
        ----------
        *args
            Positional arguments to pass directly to |add_argument|.

        **kwargs
            Keyword arguments to pass directly to |add_argument|.


        Return
        ------
        argparse.Action
            The return value of |add_argument| (return value often not needed).

        Raises
        ------
        ValueError
            If ``cmake_configure_args`` or ``cmake_build_args`` are in the positional
            ``*args``.  These are reserved attribute names that get populated after
            parsing the arguments.

        ValueError
            If :attr:`add_extra_args` is ``True``, then ``extra_args`` is also reserved
            and a value error will be raised if it is found in the positional ``*args``.
        """
        if "cmake_configure_args" in args:
            raise ValueError("'cmake_configure_args' name is reserved.")
        if "cmake_build_args" in args:
            raise ValueError("'cmake_build_args' name is reserved.")
        if self.add_extra_args and "extra_args" in args:
            raise ValueError(
                "'extra_args' is reserved.  Set `add_extra_args = False` first."
            )
        return super().add_argument(*args, **kwargs)

    def get_argument(self, arg: str) -> Optional[argparse.Action]:
        """
        Get the :class:`~python:argparse.Action` instance for the specified argument.

        Parameters
        ----------
        arg : str
            The command-line flag (e.g., ``"-G"``, ``"--shared"``) or the ``dest``
            (e.g., ``"generator"``, ``"shared"``) to look for.

        Return
        ------
        argparse.Action or None
            The argument action instance (created from :func:`add_argument`).  If
            ``arg`` does not describe a command-line flag or ``dest``, ``None`` is
            returned.
        """
        # Try and get from flag / dest mappings first.
        registered = self._get_registered_argument(arg)
        if registered:
            return registered

        # If still not found, search all actions added.
        for action in self._actions:
            if arg == action.dest or arg in action.option_strings:
                return action

        return None  # Not found x0

    def _get_registered_argument(self, arg: str) -> Optional[argparse.Action]:
        # Search based off flags: --shared, -G, etc.
        if arg in self.flag_map:
            return self.flag_map[arg]

        # Search based of dest: shared, generator, etc
        if arg in self.dest_map:
            return self.dest_map[arg]

        return None  # Not found x0

    def parse_args(self, args=None, namespace=None):  # TODO: type hints???
        """
        Parse the command-line arguments.

        Typically, no arguments are needed::

            parser = CMakeParser()
            # ... add your own arguments ...
            args = parser.parse_args()  # uses sys.argv

        Parameters
        ----------
        args
            See :meth:`~python:argparse.ArgumentParser.parse_args`.

        namespace
            See :meth:`~python:argparse.ArgumentParser.parse_args`.

        Return
        ------
        argparse.Namespace
            The parsed command-line arguments in a wrapper struct.  Will also have
            ``cmake_configure_args`` and ``cmake_build_args`` (both will be lists of
            strings) attributes populated.
        """
        # NOTE: this must be last!  That is why it gets done here, since user will be
        # finished adding their own arguments.
        if self.add_extra_args:
            self.add_extra_args = False  # only add once
            self.add_argument(
                # NOTE: default must be set.  See: https://bugs.python.org/issue28609
                "extra_args", nargs="*", default=[],
                help=(
                    "Any extra *configure* arguments to pass to CMake, supplied after "
                    "the `--` sequence.  For example, "
                    "`%(prog)s [args] -- -Werror=dev -DSOME_OPTION=ON` will result in "
                    "two extra CMake configure arguments: `-Werror=dev` and "
                    "`-DSOME_OPTION=ON`."
                )
            )

        parsed_args = super().parse_args(args=args, namespace=namespace)

        # NOTE: hasattr then check value pattern is because of the remove method, the
        # user may have removed the argument so check it exists first.  The only one
        # that is not allowed to be removed is the generator argument.
        cmake_configure_args = []
        cmake_build_args = []

        # Initial generator / architecture / toolset setup.
        cmake_configure_args.extend(["-G", parsed_args.generator])
        if hasattr(parsed_args, "architecture") and parsed_args.architecture:
            cmake_configure_args.extend(["-A", parsed_args.architecture])
        if hasattr(parsed_args, "toolset") and parsed_args.toolset:
            cmake_configure_args.extend(["-T", parsed_args.toolset])

        # Setup BUILD_SHARED_LIBS if either --shared or --static requested.
        if (hasattr(parsed_args, "shared") and parsed_args.shared) or \
                (hasattr(parsed_args, "static") and parsed_args.static):
            cmake_configure_args.append(
                f"-DBUILD_SHARED_LIBS={'ON' if parsed_args.shared else 'OFF'}")

        # Setup the default compilers for single config generators.
        if self.is_single_config_generator(parsed_args.generator):
            if hasattr(parsed_args, "cc") and parsed_args.cc:
                cmake_configure_args.append(f"-DCMAKE_C_COMPILER={parsed_args.cc}")
            if hasattr(parsed_args, "cxx") and parsed_args.cxx:
                cmake_configure_args.append(f"-DCMAKE_CXX_COMPILER={parsed_args.cxx}")

        # CMAKE_BUILD_TYPE at configure time for single config generators, and
        # --config build_type build args for multi config generators.
        if hasattr(parsed_args, "build_type") and parsed_args.build_type:
            if self.is_multi_config_generator(parsed_args.generator):
                cmake_build_args.extend(["--config", parsed_args.build_type])
            else:
                cmake_configure_args.append(
                    f"-DCMAKE_BUILD_TYPE={parsed_args.build_type}")

        # Add any extra arguments that may be requested after -- sequence.
        if hasattr(parsed_args, "extra_args"):
            for arg in parsed_args.extra_args:
                cmake_configure_args.append(arg)

        # Make the parsed results available to the user and return.
        parsed_args.cmake_configure_args = cmake_configure_args
        parsed_args.cmake_build_args = cmake_build_args
        return parsed_args

    def _register_argument(self, flag: str, *, dest: str, **kwargs):
        arg = self.add_argument(flag, dest=dest, **kwargs)
        self.flag_map[flag] = arg
        self.dest_map[dest] = arg

    def remove(self, *args: str):
        """
        Remove any registered argument(s).

        This method may be used to remove any arguments not desired.  Only arguments
        that have been created by instantiating a |CMakeParser| can be removed.

        Example::

            parser = CMakeParser()
            parser.remove("--shared", "--static")  # Remove by flags, or
            parser.remove("shared", "static")      # remove by dest.

        Arguments
        ---------
        *args : str
            Arguments to remove, listed by either flag or dest names.  See |CMakeParser|
            docs for all flags / dest names added.

        Raises
        ------
        ValueError
            If ``"-G"`` or ``"generator"`` in ``args``.  The generator argument may not
            be removed.

        ValueError
            If ``"extra_args"`` in ``args``.  This is to be prevented from being added,
            see :func:`parse_args`.

        ValueError
            If any arguments requested to be removed have not been found.  This should
            only happen if (a) there was a typo, or (b) a user tries to remove an
            argument that was not registered.
        """
        if "generator" in args or "-G" in args:
            raise ValueError("'generator' argument may not be removed.")

        if "extra_args" in args:
            raise ValueError(
                "'extra_args' cannot be removed, it must be prevented.  Set "
                "`add_extra_args = False`."
            )

        missing = []
        for item in args:
            # Only support removing options that this parser class added (or more
            # specifically, were registered).
            found_arg = self._get_registered_argument(item)
            if found_arg:
                if item in self.flag_map:
                    del self.flag_map[item]
                    del self.dest_map[found_arg.dest]
                else:
                    del self.flag_map[found_arg.option_strings[0]]
                    del self.dest_map[item]

                # See: https://bugs.python.org/issue19462#msg251739
                # Only ok because we only support removing optional arguments, not
                # positional arguments.
                self._handle_conflict_resolve(  # type: ignore
                    found_arg, [(found_arg.option_strings[0], found_arg)]
                )
            else:
                missing.append(item)

        if missing:
            raise ValueError(f"Cannot remove unregistered arg(s): {missing}")

    def set_argument(self, arg: str, **attrs: Dict[str, Any]):
        """
        Set attributes for ``arg`` argument.

        Example::

            parser = CMakeParser()

            # Change default generator from Ninja to Unix Makefiles.
            parser.set_argument("generator", default="Unix Makefiles")

            # Change default build type from Release to Debug, only allow Release and
            # Debug builds (only as demonstration...not useful in practice).
            parser.set_argument("build_type", choices={"Release", "Debug"},
                                default="Debug")

        Parameters
        ----------
        arg : str
            May either be the command-line flag (e.g., ``"--shared"`` or ``"-G"``), or
            the ``dest`` of the argument (e.g., ``"shared"`` or ``"generator"``).

        **attrs
            The attributes to set.  Only the following attributes are allowed to be
            changed via this method:

            - `default <default_>`_: value returned if not specified on command-line.
            - `choices <choices_>`_: the list of valid values to validate against.
            - `required <required_>`_: whether user must specify.
            - `help <help_>`_: the help string for the argument.
            - `metavar <metavar_>`_: how the argument is displayed in usage.

            .. _default: https://docs.python.org/3/library/argparse.html#default
            .. _choices: https://docs.python.org/3/library/argparse.html#choices
            .. _required: https://docs.python.org/3/library/argparse.html#required
            .. _help: https://docs.python.org/3/library/argparse.html#help
            .. _metavar: https://docs.python.org/3/library/argparse.html#metavar

            .. note::

                Other values such as ``dest`` or ``nargs`` are disallowed from being
                changed as doing so will break all functionality this class provides.

        Raises
        ------
        ValueError
            If the argument described by ``arg`` cannot be found.

        ValueError
            The keys of ``**attrs`` are not supported to be changed.  E.g., ``dest`` may
            not be changed.

        ValueError
            ``arg in {"-G", "generator"}`` and ``"choices" in attrs``.  The generator
            choices may not be changed (detection of single vs multi config generators
            will not be reliable).
        """
        supported_keys = {"default", "choices", "required", "help", "metavar"}
        if not attrs.keys() <= supported_keys:
            disallowed = attrs.keys() - supported_keys
            raise ValueError(
                f"Setting attribute{'' if len(disallowed) == 1 else 's'} "
                f"{disallowed} not supported.")

        if arg in {"-G", "generator"} and "choices" in attrs:
            raise ValueError(
                "Changing 'generator' attribute 'choices' is not supported."
            )

        arg_obj = self.get_argument(arg)

        # Nothing to set...
        if arg_obj is None:
            raise ValueError(f"Cannot set attrs of '{arg}', argument not found.")

        # Set all the attributes to what the user requested.
        for key, val in attrs.items():
            setattr(arg_obj, key, val)
