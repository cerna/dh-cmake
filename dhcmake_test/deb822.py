# This file is part of dh-cmake, and is distributed under the OSI-approved
# BSD 3-Clause license. See top-level LICENSE file or
# https://gitlab.kitware.com/debian/dh-cmake/blob/master/LICENSE for details.

import io

from dhcmake import deb822
from dhcmake_test import DebianSourcePackageTestCaseBase


class Deb822TestCase(DebianSourcePackageTestCaseBase):
    def test_control(self):
        with self.open("debian/control", "r") as f:
            source, packages = deb822.read_control(f)

        self.assertEqual("dh-cmake-test", source["source"])

        self.assertEqual(3, len(packages))

        package = packages[0]
        self.assertEqual("libdh-cmake-test", package["package"])
        self.assertEqual("any", package["architecture"])

        package = packages[1]
        self.assertEqual("libdh-cmake-test-dev", package["package"])
        self.assertEqual("any", package["architecture"])

        package = packages[2]
        self.assertEqual("libdh-cmake-test-doc", package["package"])
        self.assertEqual("all", package["architecture"])
