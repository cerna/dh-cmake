# This file is part of dh-cmake.
# See top-level LICENSE file for license information.

import io

from dhcmake import deb822
from dhcmake_test import KWTestCaseBase


class Deb822TestCase(KWTestCaseBase):
    def test_control_source(self):
        control_source_txt = \
        "Source: dhcmake-test\n" \
        "Maintainer: Kitware Debian Maintainers <debian@kitware.com>\n" \
        "Uploaders:\n" \
        "        Kyle Edwards <kyle.edwards@kitware.com>,\n" \
        "        Kitware Robot <kwrobot@kitware.com>\n" \

        control_source = deb822.ControlSource(io.StringIO(control_source_txt))
        self.assertEqual("dhcmake-test", control_source["source"])
        self.assertEqual("Kitware Debian Maintainers <debian@kitware.com>",
                         control_source["maintainer"])
        self.assertEqual([
            "Kyle Edwards <kyle.edwards@kitware.com>",
            "Kitware Robot <kwrobot@kitware.com>",
        ], control_source.uploaders)
