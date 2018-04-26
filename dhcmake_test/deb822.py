# This file is part of dh-cmake.
# See top-level LICENSE file for license information.

import io

from dhcmake import deb822
from dhcmake_test import DebianSourcePackageTestCaseBase


class Deb822TestCase(DebianSourcePackageTestCaseBase):
    def test_control_source(self):
        with self.open("debian/control", "r") as f:
            control_source = deb822.ControlSource(f)

        self.assertEqual("dh-cmake-test", control_source["source"])
        self.assertEqual("Kitware Debian Maintainers <debian@kitware.com>",
                         control_source["maintainer"])
        self.assertEqual([
            "Kyle Edwards <kyle.edwards@kitware.com>",
            "Kitware Robot <kwrobot@kitware.com>",
        ], control_source.uploaders)
