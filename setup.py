#!/usr/bin/env python3

# This file is part of dh-cmake.
# See top-level LICENSE file for license information.

from setuptools import setup


setup( \
    name="dh-cmake",
    description="Debhelper program for CMake projects",
    url="https://gitlab.kitware.com/debian/dh-cmake",
    author="Kyle Edwards",
    author_email="kyle.edwards@kitware.com",
    license="BSD 3 clause",
    packages=["dhcmake"],
    entry_points={
        "console_scripts": ["dh_cpack=dhcmake.cpack.main"],
    },
)
