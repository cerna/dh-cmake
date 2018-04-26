# This file is part of dh-cmake.
# See top-level LICENSE file for license information.

import os.path
import subprocess
import tempfile

from dhcmake import common, cmake
from dhcmake_test import DebianSourcePackageTestCaseBase


class DHCMakeTestCase(DebianSourcePackageTestCaseBase):
    def setUp(self):
        super().setUp()

        self.dhcmake = cmake.DHCMake()

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
        self.dhcmake.parse_args([])

        self.dhcmake.do_cmake_install(self.build_dir,
                                      self.install_all_dir,
                                      suppress_output=True)

        expected_files = {
            "usr",
            "usr/lib",
            "usr/lib/libdh-cmake-test.so",
            "usr/lib/libdh-cmake-test-lib1.so",
            "usr/lib/libdh-cmake-test-lib2.so",
            "usr/include",
            "usr/include/dh-cmake-test.h",
            "usr/include/dh-cmake-test-lib1.h",
            "usr/include/dh-cmake-test-lib2.h",
        }

        self.assertFileTreeEqual(expected_files, self.install_all_dir)

    def test_cmake_install_subdirectory(self):
        self.dhcmake.parse_args([])

        self.dhcmake.do_cmake_install(
            os.path.join(self.build_dir, "lib1"),
            self.install_all_dir,
            suppress_output=True)

        expected_files = {
            "usr",
            "usr/lib",
            "usr/lib/libdh-cmake-test-lib1.so",
            "usr/include",
            "usr/include/dh-cmake-test-lib1.h",
        }

        self.assertFileTreeEqual(expected_files, self.install_all_dir)

    def test_cmake_install_one_component(self):
        self.dhcmake.parse_args([])

        self.dhcmake.do_cmake_install(self.build_dir,
                                      self.install_dev_dir,
                                      component="dh-cmake-test-Development",
                                      suppress_output=True)

        expected_files = {
            "usr",
            "usr/include",
            "usr/include/dh-cmake-test.h",
        }

        self.assertFileTreeEqual(expected_files, self.install_dev_dir)

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
