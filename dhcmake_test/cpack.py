# This file is part of dh-cmake.
# See top-level LICENSE file for license information.

import os.path
import subprocess
import tempfile

from dhcmake import common, cpack
from dhcmake_test import RunCMakeTestCaseBase


CMAKELISTS_TXT = \
r"""cmake_minimum_required(VERSION 3.5)
project(dhcmake-test C)

include(CPack)

macro(declare_lib LIBNAME)
  add_library(${LIBNAME} SHARED "${LIBNAME}.c")
  set_property(TARGET ${LIBNAME} PROPERTY PUBLIC_HEADER "${LIBNAME}.h")
  install(TARGETS ${LIBNAME}
    LIBRARY DESTINATION lib COMPONENT ${LIBNAME}-Libraries
    PUBLIC_HEADER DESTINATION include COMPONENT ${LIBNAME}-Development
  )
endmacro()

declare_lib(dhcmake-test)
add_subdirectory(dhcmake-test-lib1)
add_subdirectory(dhcmake-test-lib2)

cpack_add_component_group(Libraries)
cpack_add_component_group(Development)

foreach(_n dhcmake-test dhcmake-test-lib1 dhcmake-test-lib2)
  cpack_add_component(${_n}-Libraries GROUP Libraries)
  cpack_add_component(${_n}-Development GROUP Development)
endforeach()
"""


class DHCPackTestCase(RunCMakeTestCaseBase):
    def make_sub_lib(self, libname):
        self.make_src_dir(libname)
        self.write_src_file(os.path.join(libname, "CMakeLists.txt"),
                            "declare_lib({0})".format(libname))
        self.write_src_file(os.path.join(libname, libname + ".c"), "")
        self.write_src_file(os.path.join(libname, libname + ".h"), "")

    def setUp(self):
        super().setUp()

        self.dhcpack = cpack.DHCPack()

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

        super().tearDown()

    def test_cmake_install_all(self):
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

    def test_cmake_install_subdirectory(self):
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

    def test_cmake_install_one_component(self):
        self.dhcpack.parse_args([])

        self.dhcpack.do_cmake_install(self.build_dir.name,
                                      self.install_dev_dir.name,
                                      component="dhcmake-test-Development",
                                      suppress_output=True)

        expected_files = {
            "usr",
            "usr/include",
            "usr/include/dhcmake-test.h",
        }

        self.assertFileTreeEqual(expected_files, self.install_dev_dir.name)
