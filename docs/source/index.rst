ci_exec
========================================================================================

.. contents::
   :local:
   :backlinks: none

About
----------------------------------------------------------------------------------------

.. include:: ../../README.rst
   :start-after: begin_brief_desc
   :end-before: end_brief_desc

.. include:: ../../README.rst
   :start-after: begin_long_desc
   :end-before: end_long_desc

Installation
----------------------------------------------------------------------------------------

.. include:: ../../README.rst
   :start-after: begin_install
   :end-before: end_install

Intended Audience
----------------------------------------------------------------------------------------

.. note::

    ``ci_exec`` can be used for anything related to writing build steps, but it was
    originally written to manage C++ projects.  The documentation will often have
    examples using ``cmake`` and ``ninja``, users do not need to understand what these
    commands are for.

``ci_exec`` utilizes some "advanced" features of Python that pertain to how the library
itself is consumed.  It may not be appropriate for users who do not know any Python at
all.  The main features a user should be aware of:

- ``*args`` and ``**kwargs`` are used liberally.  ``ci_exec`` mostly consists of wrapper
  classes / functions around the python standard library, and in most cases ``*args``
  and ``**kwargs`` are the "pass-through" parameters.
- Keyword-only arguments.  Many library signatures look something like::

      def foo(a: str, *, b: int = 2):
          pass

      foo("hi")       # OK: b = 2
      foo("hi", 3)    # ERROR: b is keyword only
      foo("hi", b=3)  # OK: b = 3

  Anything after the ``*,`` must be named explicitly.
- Operator overloading, particularly what ``__call__`` means and how it works.  A quick
  overview::

      from ci_exec import Executable

      # Typically: prefer ci_exec.which instead, which returns a ci_exec.Executable.
      cmake = Executable("/usr/bin/cmake")

      # cmake.__call__ invoked with args = [".."], kwargs = {}
      cmake("..")

      # cmake.__call__ invoked with args = [".."], kwargs = {"check": False}
      cmake("..", check=False)

None of these features are altogether that special, but it must be stated clearly and
plainly: this library is designed for users who already know Python.

Put differently: if you don't know why writing script-like Python is useful for CI,
while still having access to a full-fledged programming language, this package likely
has no use for you.  In particular, C++ users are encouraged to look at
`conan <https://conan.io/>`_ as an alternative.  ``ci_exec`` has zero intention of
becoming a package manager, and was written to help manage projects that are not well
suited to conan for various reasons.

Full Documentation
----------------------------------------------------------------------------------------

Quick reference:

.. coresummary::

.. toctree::
   :maxdepth: 2

   api/root
   demos
   important_usage_notes
   changelog
