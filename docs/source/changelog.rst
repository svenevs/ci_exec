Changelog
========================================================================================

v0.1.0.post0
----------------------------------------------------------------------------------------

- Fix support for early 3.5.x by conditionally importing ``NoReturn`` and
  ``TYPE_CHECKING`` (:pr:`12`).

v0.1.0
----------------------------------------------------------------------------------------

Initial release.  Broken for python 3.5.x where ``typing`` module does not house
``NoReturn`` and ``TYPE_CHECKING``.  Definitely broken on 3.5.2 and earlier.
