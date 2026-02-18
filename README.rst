===========================
cjklib3 (EdwardCoventry fork)
===========================

This repository is a personal fork of cjklib for ongoing Python 3 compatibility and maintenance.

Original project
================
- Upstream repository: https://github.com/cburgmer/cjklib
- Historical project page: http://code.google.com/p/cjklib/

Fork changes
============
- Replaced deprecated ``pkg_resources`` usage in ``cjklib.util.locateProjectFile()`` with ``importlib.metadata``-based lookup.
- Removed legacy ``ez_setup.py`` bootstrap flow from packaging.
- Removed deprecated runtime references to ``distutils`` and ``imp``.
- Fixed invalid escape sequence warnings across source and test files.
- Added small packaging and repo-maintenance updates (e.g. ``.gitignore`` temp path handling).
- Added SQLAlchemy compatibility updates in ``cjklib.dbconnector`` for modern SQLAlchemy usage.
- Added Windows-safe handling for Unix-style absolute search paths (for example ``/usr/local/share/cjklib/``).
- Fixed Python 3 compatibility issues in utility and test modules (``crossDict`` bug, ``new.classobj``/``types.ClassType`` replacements).
- Fixed indentation issues in ``cjklib-dico/dict.py`` so it compiles on modern Python.

Notes
=====
- This fork is maintained to keep the code usable in newer Python/tooling environments.
- Python 3.13 is validated in local development with editable install and runtime smoke checks.

Quick local verification
========================

From this repository root:

.. code-block:: powershell

   python -m compileall .
   python -c "import pkgutil, importlib, cjklib; [importlib.import_module(m.name) for m in pkgutil.walk_packages(cjklib.__path__, prefix='cjklib.')]"
   python -c "from cjklib import characterlookup; cjk=characterlookup.CharacterLookup('J'); print(type(cjk).__name__)"
