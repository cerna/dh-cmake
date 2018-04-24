# This file is part of dh-cmake.
# See top-level LICENSE file for license information.

import os.path
import subprocess
import tempfile

from dhcmake import common, cpack
from dhcmake_test import DHCMakeTestCaseBase


CMAKELISTS_TXT = \
r"""cmake_minimum_required(VERSION 3.5)
project(dhcmake-test C)

macro(declare_lib LIBNAME)
  add_library(${LIBNAME} SHARED "${LIBNAME}.c")
  set_property(TARGET ${LIBNAME} PROPERTY PUBLIC_HEADER "${LIBNAME}.h")
  install(TARGETS ${LIBNAME}
    LIBRARY DESTINATION lib COMPONENT Libraries
    PUBLIC_HEADER DESTINATION include COMPONENT Development
  )
endmacro()

declare_lib(dhcmake-test)
add_subdirectory(dhcmake-test-lib1)
add_subdirectory(dhcmake-test-lib2)
"""


class DHCPackTestCase(DHCMakeTestCaseBase):
    def setUp(self):
        self.dhcpack = cpack.DHCPack()

        self.src_dir = tempfile.TemporaryDirectory()

        self.write_src_file("CMakeLists.txt", CMAKELISTS_TXT)
        self.write_src_file("dhcmake-test.c", "")
        self.write_src_file("dhcmake-test.h", "")

        self.make_sub_lib("dhcmake-test-lib1")
        self.make_sub_lib("dhcmake-test-lib2")

        self.build_dir = tempfile.TemporaryDirectory()

        subprocess.run(
            [
                "cmake", "-G", "Unix Makefiles", "-DCMAKE_INSTALL_PREFIX=/usr",
                self.src_dir.name,
            ], cwd=self.build_dir.name, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=True)

        subprocess.run(["make"], cwd=self.build_dir.name,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       check=True)

        self.install_all_dir = tempfile.TemporaryDirectory()
        self.install_lib_dir = tempfile.TemporaryDirectory()
        self.install_dev_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.install_dev_dir.cleanup()
        self.install_lib_dir.cleanup()
        self.install_all_dir.cleanup()
        self.build_dir.cleanup()
        self.src_dir.cleanup()


class DHCPackDoCMakeInstallTestCase(DHCPackTestCase):
    def test_install_all(self):
        self.dhcpack.parse_args([])

        self.dhcpack.do_cmake_install(self.build_dir.name,
                                      self.install_all_dir.name,
                                      suppress_output=True)

        expected_files = {
            "usr",
            "usr/lib",
            "usr/lib/libdhcmake-test.so",
            "usr/lib/libdhcmake-test-lib1.so",
            "usr/lib/libdhcmake-test-lib2.so",
            "usr/include",
            "usr/include/dhcmake-test.h",
            "usr/include/dhcmake-test-lib1.h",
            "usr/include/dhcmake-test-lib2.h",
        }

        self.assertFileTreeEqual(expected_files, self.install_all_dir.name)

    def test_install_subdirectory(self):
        self.dhcpack.parse_args([])

        self.dhcpack.do_cmake_install(
            os.path.join(self.build_dir.name, "dhcmake-test-lib1"),
            self.install_all_dir.name,
            suppress_output=True)

        expected_files = {
            "usr",
            "usr/lib",
            "usr/lib/libdhcmake-test-lib1.so",
            "usr/include",
            "usr/include/dhcmake-test-lib1.h",
        }

        self.assertFileTreeEqual(expected_files, self.install_all_dir.name)

    def test_install_one_component(self):
        self.dhcpack.parse_args([])

        self.dhcpack.do_cmake_install(self.build_dir.name,
                                      self.install_dev_dir.name,
                                      component="Development",
                                      suppress_output=True)

        expected_files = {
            "usr",
            "usr/include",
            "usr/include/dhcmake-test.h",
            "usr/include/dhcmake-test-lib1.h",
            "usr/include/dhcmake-test-lib2.h",
        }

        self.assertFileTreeEqual(expected_files, self.install_dev_dir.name)
