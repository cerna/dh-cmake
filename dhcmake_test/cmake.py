# This file is part of dh-cmake, and is distributed under the OSI-approved
# BSD 3-Clause license. See top-level LICENSE file or
# https://gitlab.kitware.com/debian/dh-cmake/blob/master/LICENSE for details.

import os.path
import subprocess
import tempfile

from dhcmake import common, cmake
from dhcmake_test import *


class DHCMakeTestCase(DebianSourcePackageTestCaseBase):
    libraries_files = set(KWTestCaseBase.replace_arch_in_paths({
        "usr",
        "usr/lib",
        "usr/lib/{arch}",
        "usr/lib/{arch}/libdh-cmake-test.so.1",
        "usr/lib/{arch}/libdh-cmake-test.so.1.0",
        "usr/lib/{arch}/libdh-cmake-test-lib1.so.1",
        "usr/lib/{arch}/libdh-cmake-test-lib1.so.1.0",
        "usr/lib/{arch}/libdh-cmake-test-lib2.so.1",
        "usr/lib/{arch}/libdh-cmake-test-lib2.so.1.0",
    }))

    headers_files = set(KWTestCaseBase.replace_arch_in_paths({
        "usr",
        "usr/include",
        "usr/include/dh-cmake-test.h",
        "usr/include/dh-cmake-test-lib1.h",
        "usr/include/dh-cmake-test-lib2.h",
    }))

    namelinks_files = set(KWTestCaseBase.replace_arch_in_paths({
        "usr",
        "usr/lib",
        "usr/lib/{arch}",
        "usr/lib/{arch}/libdh-cmake-test.so",
        "usr/lib/{arch}/libdh-cmake-test-lib1.so",
        "usr/lib/{arch}/libdh-cmake-test-lib2.so",
    }))

    def setUp(self):
        super().setUp()

        self.dhcmake = cmake.DHCMake()

    def setup_do_cmake_install(self):

        self.build_dir = self.make_directory_in_tmp("build")

        subprocess.run(
            [
                "cmake", "-G", "Unix Makefiles", "-DCMAKE_INSTALL_PREFIX=/usr",
                self.src_dir,
            ], cwd=self.build_dir, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=True)

        subprocess.run(["make"], cwd=self.build_dir,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       check=True)

        self.install_all_dir = self.make_directory_in_tmp("install-all")
        self.install_lib_dir = self.make_directory_in_tmp("install-lib")
        self.install_dev_dir = self.make_directory_in_tmp("install-dev")

    def test_cmake_install_all(self):
        self.setup_do_cmake_install()
        self.dhcmake.parse_args([])

        self.dhcmake.do_cmake_install(self.build_dir,
                                      self.install_all_dir,
                                      suppress_output=True)

        self.assertFileTreeEqual(self.libraries_files | self.headers_files \
                                 | self.namelinks_files, self.install_all_dir)

    def test_cmake_install_subdirectory(self):
        self.setup_do_cmake_install()
        self.dhcmake.parse_args([])

        self.dhcmake.do_cmake_install(
            os.path.join(self.build_dir, "lib1"),
            self.install_all_dir,
            suppress_output=True)

        self.assertFileTreeEqual(set(self.replace_arch_in_paths({
            "usr",
            "usr/lib",
            "usr/lib/{arch}",
            "usr/lib/{arch}/libdh-cmake-test-lib1.so",
            "usr/lib/{arch}/libdh-cmake-test-lib1.so.1",
            "usr/lib/{arch}/libdh-cmake-test-lib1.so.1.0",
            "usr/include",
            "usr/include/dh-cmake-test-lib1.h",
        })), self.install_all_dir)

    def test_cmake_install_one_component(self):
        self.setup_do_cmake_install()
        self.dhcmake.parse_args([])

        self.dhcmake.do_cmake_install(self.build_dir,
                                      self.install_dev_dir,
                                      component="Headers",
                                      suppress_output=True)

        self.assertFileTreeEqual(self.headers_files, self.install_dev_dir)

    def test_get_cmake_components(self):
        self.dhcmake.parse_args([])

        self.assertEqual([
            "Libraries",
        ], self.dhcmake.get_cmake_components("libdh-cmake-test"))

    def test_get_cmake_components_executable(self):
        self.dhcmake.parse_args([])

        self.assertEqual([
            "Headers",
            "Namelinks",
        ], self.dhcmake.get_cmake_components("libdh-cmake-test-dev"))

    def test_get_cmake_components_noexist(self):
        self.dhcmake.parse_args([])

        self.assertEqual([], self.dhcmake.get_cmake_components(
            "libdh-cmake-test-doc"))

    def do_dh_cmake_install(self, args):
        self.dhcmake.parse_args(args)

        os.mkdir(self.dhcmake.get_build_directory())

        subprocess.run(
            [
                "cmake", "-G", "Unix Makefiles", "-DCMAKE_INSTALL_PREFIX=/usr",
                self.src_dir,
            ], cwd=self.dhcmake.get_build_directory(), stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=True)

        subprocess.run(["make"], cwd=self.dhcmake.get_build_directory(),
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       check=True)

        self.dhcmake.install()

    def test_dh_cmake_install_default(self):
        self.do_dh_cmake_install([])

        self.assertFileTreeEqual(self.libraries_files,
                                 "debian/libdh-cmake-test")

        self.assertFileTreeEqual(self.headers_files | self.namelinks_files,
                                 "debian/libdh-cmake-test-dev")

    def test_dh_cmake_install_tmpdir(self):
        self.do_dh_cmake_install(["--tmpdir=debian/tmp"])

        self.assertFileTreeEqual(self.libraries_files | self.headers_files \
                                 | self.namelinks_files,
                                 "debian/tmp")
