# This file is part of dh-cmake, and is distributed under the OSI-approved
# BSD 3-Clause license. See top-level LICENSE file or
# https://gitlab.kitware.com/debian/dh-cmake/blob/master/LICENSE for details.

from unittest import skip

from dhcmake import common
from dhcmake_test import *


class DHCommonTestCase(DebianSourcePackageTestCaseBase):
    def setUp(self):
        super().setUp()
        self.dhcommon = common.DHCommon()

    def check_packages(self, expected_packages):
        self.assertEqual(expected_packages, set(self.dhcommon.get_packages()))

    def test_do_cmd(self):
        self.dhcommon.parse_args([])

        with VolatileNamedTemporaryFile() as f:
            self.dhcommon.do_cmd(["rm", f.name])
            self.assertVolatileFileNotExists(f.name)

    def test_do_cmd_no_act(self):
        self.dhcommon.parse_args(["--no-act"])

        with VolatileNamedTemporaryFile() as f:
            self.dhcommon.do_cmd(["rm", f.name])
            self.assertFileExists(f.name)

    def test_get_packages_default(self):
        self.dhcommon.parse_args([])

        self.check_packages({
            "libdh-cmake-test",
            "libdh-cmake-test-dev",
            "libdh-cmake-test-doc",
        })

    def test_get_packages_whitelist_short(self):
        self.dhcommon.parse_args(["-plibdh-cmake-test-dev",
                                      "-plibdh-cmake-test-doc"])

        self.check_packages({
            "libdh-cmake-test-dev",
            "libdh-cmake-test-doc",
        })

    def test_get_packages_whitelist_long(self):
        self.dhcommon.parse_args(["--package", "libdh-cmake-test-dev",
                                      "--package", "libdh-cmake-test-doc"])

        self.check_packages({
            "libdh-cmake-test-dev",
            "libdh-cmake-test-doc",
        })

    def test_get_packages_blacklist_short(self):
        self.dhcommon.parse_args(["-Nlibdh-cmake-test-dev",
                                      "-Nlibdh-cmake-test-doc"])

        self.check_packages({
            "libdh-cmake-test",
        })

    def test_get_packages_blacklist_long(self):
        self.dhcommon.parse_args(["--no-package", "libdh-cmake-test-dev",
                                      "--no-package", "libdh-cmake-test-doc"])

        self.check_packages({
            "libdh-cmake-test",
        })

    def test_get_packages_arch_short(self):
        self.dhcommon.parse_args(["-a"])

        self.check_packages({
            "libdh-cmake-test",
            "libdh-cmake-test-dev",
        })

    def test_get_packages_arch_long(self):
        self.dhcommon.parse_args(["--arch"])

        self.check_packages({
            "libdh-cmake-test",
            "libdh-cmake-test-dev",
        })

    def test_get_packages_arch_deprecated(self):
        self.dhcommon.parse_args(["-s"])

        self.check_packages({
            "libdh-cmake-test",
            "libdh-cmake-test-dev",
        })

    def test_get_packages_indep_short(self):
        self.dhcommon.parse_args(["-i"])

        self.check_packages({
            "libdh-cmake-test-doc",
        })

    def test_get_packages_indep_long(self):
        self.dhcommon.parse_args(["--indep"])

        self.check_packages({
            "libdh-cmake-test-doc",
        })

    def test_get_main_package_default(self):
        self.dhcommon.parse_args([])

        self.assertEqual("libdh-cmake-test",
                         self.dhcommon.get_main_package())

    def test_get_main_package_specified(self):
        self.dhcommon.parse_args(["--mainpackage=libdh-cmake-test-dev"])

        self.assertEqual("libdh-cmake-test-dev",
                         self.dhcommon.get_main_package())

    def test_get_package_file(self):
        self.dhcommon.parse_args([])

        self.assertEqual(
            "debian/cmake-components",
            self.dhcommon.get_package_file(
                "libdh-cmake-test", "cmake-components"
            )
        )

        self.assertEqual(
            "debian/libdh-cmake-test-dev.cmake-components",
            self.dhcommon.get_package_file(
                "libdh-cmake-test-dev", "cmake-components"
            )
        )

        self.assertIsNone(self.dhcommon.get_package_file(
            "libdh-cmake-test-doc", "cmake-components"))

        self.assertEqual(
            "debian/libdh-cmake-test.specific",
            self.dhcommon.get_package_file(
                "libdh-cmake-test", "specific"
            )
        )

        self.assertEqual(
            "debian/libdh-cmake-test.both",
            self.dhcommon.get_package_file(
                "libdh-cmake-test", "both"
            )
        )

    def test_read_package_file(self):
        self.dhcommon.parse_args([])

        with self.dhcommon.read_package_file(
                "libdh-cmake-test", "cmake-components") as f:
            self.assertEqual("Libraries\n", f.read())
        with self.dhcommon.read_package_file(
                "libdh-cmake-test-dev", "cmake-components") as f:
            self.assertEqual("Headers\nNamelinks\n", f.read())
        self.assertIsNone(self.dhcommon.read_package_file(
            "libdh-cmake-test-doc", "cmake-components"))

    def test_build_directory_default(self):
        self.dhcommon.parse_args([])

        self.assertEqual(
            "obj-" + common.dpkg_architecture()["DEB_HOST_GNU_TYPE"],
            self.dhcommon.get_build_directory())

    def test_build_directory_short(self):
        self.dhcommon.parse_args(["-B", "debian/build"])

        self.assertEqual("debian/build",
                         self.dhcommon.get_build_directory())

    def test_build_directory_long(self):
        self.dhcommon.parse_args(["--builddirectory", "debian/build"])

        self.assertEqual("debian/build",
                         self.dhcommon.get_build_directory())

    def test_tmpdir_default(self):
        self.dhcommon.parse_args([])

        self.assertEqual("debian/libdh-cmake-test",
                         self.dhcommon.get_tmpdir("libdh-cmake-test"))
        self.assertEqual("debian/libdh-cmake-test-dev",
                         self.dhcommon.get_tmpdir("libdh-cmake-test-dev"))

    def test_tmpdir_short(self):
        self.dhcommon.parse_args(["-P", "debian/tmpdir"])

        self.assertEqual("debian/tmpdir",
                         self.dhcommon.get_tmpdir("libdh-cmake-test"))
        self.assertEqual("debian/tmpdir",
                         self.dhcommon.get_tmpdir("libdh-cmake-test-dev"))

    def test_tmpdir_long(self):
        self.dhcommon.parse_args(["--tmpdir=debian/tmpdir"])

        self.assertEqual("debian/tmpdir",
                         self.dhcommon.get_tmpdir("libdh-cmake-test"))
        self.assertEqual("debian/tmpdir",
                         self.dhcommon.get_tmpdir("libdh-cmake-test-dev"))

    def test_o_flag(self):
        self.dhcommon.parse_args(["-O=-v"])

        self.assertTrue(self.dhcommon.options.verbose)
