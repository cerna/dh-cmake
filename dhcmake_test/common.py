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
