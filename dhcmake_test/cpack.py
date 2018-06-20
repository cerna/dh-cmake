# This file is part of dh-cmake, and is distributed under the OSI-approved
# BSD 3-Clause license. See top-level LICENSE file or
# https://gitlab.kitware.com/debian/dh-cmake/blob/master/LICENSE for details.

from dhcmake import common, cpack
from dhcmake_test import *


class DHCPackTestCase(DebianSourcePackageTestCaseBase):
    DHClass = cpack.DHCPack

    def setUp(self):
        super().setUp()

        self.dh.parse_args([])

        os.mkdir(self.dh.get_build_directory())

        self.run_cmd(
            [
                "cmake", "-G", "Unix Makefiles", "-DCMAKE_INSTALL_PREFIX=/usr",
                self.src_dir,
            ], cwd=self.dh.get_build_directory())

        self.run_cmd(["make"], cwd=self.dh.get_build_directory())

    def test_generate(self):
        self.assertFileNotExists("debian/.cpack/cpack-metadata.json")
        self.dh.generate([])
        self.assertFileExists("debian/.cpack/cpack-metadata.json")
