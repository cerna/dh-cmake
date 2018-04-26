# This file is part of dh-cmake.
# See top-level LICENSE file for license information.

from unittest import skip

from dhcmake import common
from dhcmake_test import *


class DHCMakeBaseTestCase(DebianSourcePackageTestCaseBase):
    def setUp(self):
        super().setUp()
        self.dhcmake_base = common.DHCMakeBase()

    def check_packages(self, expected_packages):
        self.assertEqual(expected_packages, set(self.dhcmake_base.get_packages()))

    def test_do_cmd(self):
        self.dhcmake_base.parse_args([])

        with VolatileNamedTemporaryFile() as f:
            self.dhcmake_base.do_cmd(["rm", f.name])
            self.assertVolatileFileNotExists(f.name)

    def test_do_cmd_no_act(self):
        self.dhcmake_base.parse_args(["--no-act"])

        with VolatileNamedTemporaryFile() as f:
            self.dhcmake_base.do_cmd(["rm", f.name])
            self.assertFileExists(f.name)

    def test_get_packages_default(self):
        self.dhcmake_base.parse_args([])

        self.check_packages({
            "libdh-cmake-test",
            "libdh-cmake-test-dev",
            "libdh-cmake-test-doc",
        })

    def test_get_packages_whitelist_short(self):
        self.dhcmake_base.parse_args(["-plibdh-cmake-test-dev",
                                      "-plibdh-cmake-test-doc"])

        self.check_packages({
            "libdh-cmake-test-dev",
            "libdh-cmake-test-doc",
        })

    def test_get_packages_whitelist_long(self):
        self.dhcmake_base.parse_args(["--package", "libdh-cmake-test-dev",
                                      "--package", "libdh-cmake-test-doc"])

        self.check_packages({
            "libdh-cmake-test-dev",
            "libdh-cmake-test-doc",
        })

    def test_get_packages_blacklist_short(self):
        self.dhcmake_base.parse_args(["-Nlibdh-cmake-test-dev",
                                      "-Nlibdh-cmake-test-doc"])

        self.check_packages({
            "libdh-cmake-test",
        })

    def test_get_packages_blacklist_long(self):
        self.dhcmake_base.parse_args(["--no-package", "libdh-cmake-test-dev",
                                      "--no-package", "libdh-cmake-test-doc"])

        self.check_packages({
            "libdh-cmake-test",
        })

    def test_get_packages_arch_short(self):
        self.dhcmake_base.parse_args(["-a"])

        self.check_packages({
            "libdh-cmake-test",
            "libdh-cmake-test-dev",
        })

    def test_get_packages_arch_long(self):
        self.dhcmake_base.parse_args(["--arch"])

        self.check_packages({
            "libdh-cmake-test",
            "libdh-cmake-test-dev",
        })

    def test_get_packages_arch_deprecated(self):
        self.dhcmake_base.parse_args(["-s"])

        self.check_packages({
            "libdh-cmake-test",
            "libdh-cmake-test-dev",
        })

    def test_get_packages_indep_short(self):
        self.dhcmake_base.parse_args(["-i"])

        self.check_packages({
            "libdh-cmake-test-doc",
        })

    def test_get_packages_indep_long(self):
        self.dhcmake_base.parse_args(["--indep"])

        self.check_packages({
            "libdh-cmake-test-doc",
        })

    def test_get_main_package_default(self):
        self.dhcmake_base.parse_args([])

        self.assertEqual("libdh-cmake-test",
                         self.dhcmake_base.get_main_package())

    def test_get_main_package_specified(self):
        self.dhcmake_base.parse_args(["--mainpackage=libdh-cmake-test-dev"])

        self.assertEqual("libdh-cmake-test-dev",
                         self.dhcmake_base.get_main_package())

    def test_get_package_file_main(self):
        self.dhcmake_base.parse_args([])

        self.assertEqual(
            "debian/cmake-components",
            self.dhcmake_base.get_package_file(
                "libdh-cmake-test","cmake-components"
            )
        )

    def test_get_package_file_other(self):
        self.dhcmake_base.parse_args([])

        self.assertEqual(
            "debian/libdh-cmake-test-dev.cmake-components",
            self.dhcmake_base.get_package_file(
                "libdh-cmake-test-dev","cmake-components"
            )
        )

    def test_build_directory_default(self):
        self.dhcmake_base.parse_args([])

        self.assertEqual(
            "obj-" + common.dpkg_architecture()["DEB_HOST_GNU_TYPE"],
            self.dhcmake_base.get_build_directory())

    def test_build_directory_short(self):
        self.dhcmake_base.parse_args(["-B", "debian/build"])

        self.assertEqual("debian/build",
                         self.dhcmake_base.get_build_directory())

    def test_build_directory_long(self):
        self.dhcmake_base.parse_args(["--builddirectory", "debian/build"])

        self.assertEqual("debian/build",
                         self.dhcmake_base.get_build_directory())

    def test_tmpdir_default(self):
        self.dhcmake_base.parse_args([])

        self.assertEqual("debian/libdh-cmake-test",
                         self.dhcmake_base.get_tmpdir("libdh-cmake-test"))
        self.assertEqual("debian/libdh-cmake-test-dev",
                         self.dhcmake_base.get_tmpdir("libdh-cmake-test-dev"))

    def test_tmpdir_short(self):
        self.dhcmake_base.parse_args(["-P", "debian/tmpdir"])

        self.assertEqual("debian/tmpdir",
                         self.dhcmake_base.get_tmpdir("libdh-cmake-test"))
        self.assertEqual("debian/tmpdir",
                         self.dhcmake_base.get_tmpdir("libdh-cmake-test-dev"))

    def test_tmpdir_long(self):
        self.dhcmake_base.parse_args(["--tmpdir=debian/tmpdir"])

        self.assertEqual("debian/tmpdir",
                         self.dhcmake_base.get_tmpdir("libdh-cmake-test"))
        self.assertEqual("debian/tmpdir",
                         self.dhcmake_base.get_tmpdir("libdh-cmake-test-dev"))
