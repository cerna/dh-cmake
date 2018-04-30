#!/usr/bin/env python3

# This file is part of dh-cmake, and is distributed under the OSI-approved
# BSD 3-Clause license. See top-level LICENSE file or
# https://gitlab.kitware.com/debian/dh-cmake/blob/master/LICENSE for details.

from setuptools import setup


setup(
    name="dh-cmake",
    version="0.1",
    description="Debhelper program for CMake projects",
    url="https://gitlab.kitware.com/debian/dh-cmake",
    author="Kyle Edwards",
    author_email="kyle.edwards@kitware.com",
    maintainer="Kitware Debian Maintainers",
    maintainer_email="debian@kitware.com",
    classifiers=[
        "License :: OSI Approved :: BSD License",
    ],
    packages=["dhcmake"],
    install_requires=["python-debian"],
    entry_points={
        "console_scripts": [
            "dh_cmake_install=dhcmake.cmake:install",
            "dh_ctest_start=dhcmake.ctest:start",
            "dh_ctest_configure=dhcmake.ctest:configure",
            "dh_ctest_build=dhcmake.ctest:build",
            "dh_ctest_test=dhcmake.ctest:test",
            "dh_ctest_submit=dhcmake.ctest:submit",
        ],
    },
    package_data={
        "dhcmake": ["dh_ctest_driver.cmake"],
    },
    data_files=[
        ("share/perl5/Debian/Debhelper/Sequence", ["perl5/Debian/Debhelper/Sequence/cmake.pm"]),
    ],
)
