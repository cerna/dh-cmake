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

    def test_get_cpack_components(self):
        with open("debian/libdh-cmake-test-extra-32.cpack-components", "w") \
                as f:
            f.write("InvalidComponent\n")

        self.dh.generate([])
        self.dh.read_cpack_metadata()

        self.assertEqual(
                ["Libraries"],
                self.dh.get_cpack_components("libdh-cmake-test")
        )

        with self.assertRaises(
                ValueError,
                msg="Invalid CPack components in libdh-cmake-test-extra-32"
        ):
            self.dh.get_cpack_components("libdh-cmake-test-extra-32")

    def test_get_cpack_component_groups(self):
        with open("debian/libdh-cmake-test-extra-32.cpack-component-groups",
                "w") as f:
            f.write("InvalidGroup\n")

        self.dh.generate([])
        self.dh.read_cpack_metadata()

        self.assertEqual(
                ["Development"],
                self.dh.get_cpack_component_groups("libdh-cmake-test-dev")
        )

        with self.assertRaises(
                ValueError,
                msg="Invalid CPack component groups "
                    "in libdh-cmake-test-extra-32"
        ):
            self.dh.get_cpack_component_groups("libdh-cmake-test-extra-32")

    def test_get_all_cpack_components_for_group(self):
        self.dh.generate([])
        self.dh.read_cpack_metadata()

        self.assertEqual({"Headers", "Namelinks"},
                self.dh.get_all_cpack_components_for_group("Development"))

        self.assertEqual({"Libraries", "Headers", "Namelinks"},
                self.dh.get_all_cpack_components_for_group("All"))

    def test_get_all_cpack_components(self):
        self.dh.generate([])
        self.dh.read_cpack_metadata()

        self.assertEqual({"Headers", "Namelinks"},
                self.dh.get_all_cpack_components("libdh-cmake-test-dev"))

        self.assertEqual({"Libraries"},
                self.dh.get_all_cpack_components("libdh-cmake-test"))

    def test_get_package_dependencies(self):
        self.dh.generate([])
        self.dh.read_cpack_metadata()

        self.assertEqual({"libdh-cmake-test"},
                self.dh.get_package_dependencies("libdh-cmake-test-dev"))

    def test_substvars(self):
        self.dh.generate([])
        self.dh.substvars([])

        with open("debian/libdh-cmake-test-dev.substvars", "r") as f:
            self.assertEqual("cpack:Depends=libdh-cmake-test "
                    "(= ${binary:Version})\n", f.read())
