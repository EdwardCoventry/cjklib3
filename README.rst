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

Notes
=====
- This fork is maintained to keep the code usable in newer Python/tooling environments.
- Some legacy behavior and compatibility constraints still exist (for example older SQLAlchemy integration paths).
