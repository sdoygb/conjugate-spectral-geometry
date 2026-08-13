"""Traditional setuptools entry point: supports editable installs on old pip.

All configuration lives in pyproject.toml (PEP 621); this file only provides
the setup.py develop path for pip < 21.3.
"""
from setuptools import setup

setup()
