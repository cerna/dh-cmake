# This file is part of dh-cmake, and is distributed under the OSI-approved
# BSD 3-Clause license. See top-level LICENSE file or
# https://gitlab.kitware.com/debian/dh-cmake/blob/master/LICENSE for details.

import os.path
import subprocess
import tempfile

from dhcmake import common, cmake
from dhcmake_test import *


class DHCMakeTestCase(DebianSourcePackageTestCaseBase):
    DHClass = cmake.DHCMake

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

    libdh_cmake_test_files = {
        "usr",
        "usr/share",
        "usr/share/doc",
        "usr/share/doc/libdh-cmake-test",
        "usr/share/doc/libdh-cmake-test/changelog.Debian.gz",
    }

    libdh_cmake_test_dev_files = {
        "usr",
        "usr/share",
        "usr/share/doc",
        "usr/share/doc/libdh-cmake-test-dev",
        "usr/share/doc/libdh-cmake-test-dev/changelog.Debian.gz",
    }

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
        self.dh.parse_args([])

        self.dh.do_cmake_install(self.build_dir,
                                 self.install_all_dir,
                                 suppress_output=True)

        self.assertFileTreeEqual(self.libraries_files | self.headers_files \
                                 | self.namelinks_files, self.install_all_dir)

    def test_cmake_install_subdirectory(self):
        self.setup_do_cmake_install()
        self.dh.parse_args([])

        self.dh.do_cmake_install(
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
        self.dh.parse_args([])

        self.dh.do_cmake_install(self.build_dir,
                                 self.install_dev_dir,
                                 component="Headers",
                                 suppress_output=True)

        self.assertFileTreeEqual(self.headers_files, self.install_dev_dir)

    def test_get_cmake_components(self):
        self.dh.parse_args([])

        self.assertEqual([
            "Libraries",
        ], self.dh.get_cmake_components("libdh-cmake-test"))

    def test_get_cmake_components_executable(self):
        self.dh.parse_args([])

        self.assertEqual([
            "Headers",
            "Namelinks",
        ], self.dh.get_cmake_components("libdh-cmake-test-dev"))

    def test_get_cmake_components_noexist(self):
        self.dh.parse_args([])

        self.assertEqual([], self.dh.get_cmake_components(
            "libdh-cmake-test-doc"))

    def do_dh_cmake_install(self, args):
        self.dh.parse_args(args)

        os.mkdir(self.dh.get_build_directory())

        subprocess.run(
            [
                "cmake", "-G", "Unix Makefiles", "-DCMAKE_INSTALL_PREFIX=/usr",
                self.src_dir,
            ], cwd=self.dh.get_build_directory(), stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=True)

        subprocess.run(["make"], cwd=self.dh.get_build_directory(),
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       check=True)

        self.dh.install(args)

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

    def run_debian_rules(self, rule, case=None):
        env = os.environ.copy()
        if case:
            env["DH_CMAKE_CASE"] = case

        subprocess.run(["fakeroot", "debian/rules", rule], env=env,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, check=True)

    def test_run_debian_rules(self):
        self.run_debian_rules("build")
        self.run_debian_rules("install")

        self.assertFileTreeEqual(self.libraries_files \
                                 | self.libdh_cmake_test_files,
                                 "debian/libdh-cmake-test")

        self.assertFileTreeEqual(self.headers_files | self.namelinks_files \
                                 | self.libdh_cmake_test_dev_files,
                                 "debian/libdh-cmake-test-dev")
