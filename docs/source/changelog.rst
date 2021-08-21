Changelog
========================================================================================

v0.1.2
----------------------------------------------------------------------------------------

- Drop python 3.5 support (:pr:`27`): python 3.6 or later required.
- Add ``Visual Studio 17 2022`` and ``Ninja Multi-Config`` to |CMakeParser| (:pr:`29`).

v0.1.1
----------------------------------------------------------------------------------------

- Added |CMakeParser| (:pr:`16`).

v0.1.0.post0
----------------------------------------------------------------------------------------

- Fix support for early 3.5.x by conditionally importing ``NoReturn`` and
  ``TYPE_CHECKING`` (:pr:`12`).

v0.1.0
----------------------------------------------------------------------------------------

Initial release.  Broken for python 3.5.x where ``typing`` module does not house
``NoReturn`` and ``TYPE_CHECKING``.  Definitely broken on 3.5.2 and earlier.
