# This file is part of dh-cmake, and is distributed under the OSI-approved
# BSD 3-Clause license. See top-level LICENSE file or
# https://gitlab.kitware.com/debian/dh-cmake/blob/master/LICENSE for details.

import os.path

from dhcmake import common


class DHCPack(common.DHCommon):
    @common.DHEntryPoint
    def generate(self, args=None):
        self.parse_args(args)

        cmd_args = [
                "cpack",
                "--config",
                os.path.join(self.get_build_directory(), "CPackConfig.cmake"),
                "-G", "Ext",
                "-D", "CPACK_PACKAGE_FILE_NAME=cpack-metadata",
                "-B", "debian/.cpack",
        ]
        self.do_cmd(cmd_args)


def generate():
    dhcpack = DHCPack()
    dhcpack.generate()
