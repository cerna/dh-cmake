# This file is part of dh-cmake, and is distributed under the OSI-approved
# BSD 3-Clause license. See top-level LICENSE file or
# https://gitlab.kitware.com/debian/dh-cmake/blob/master/LICENSE for details.

import os.path
import re

from dhcmake import common


class DHCMake(common.DHCommon):
    def get_cmake_components(self, package):
        opened_file = self.read_package_file(package, "cmake-components")
        if opened_file:
            with opened_file as f:
                return [l.rstrip() for l in f if not re.search("^($|#)", l)]
        else:
            return []

    def install_make_arg_parser(self, parser):
        self.make_arg_parser(parser)
        parser.add_argument(
            "--sourcedir", action="store",
            help="Source directory for installation (not used except to notify"
                 " dh_missing)",
            default="debian/tmp")

    @common.DHEntryPoint("dh_cmake_install")
    def install(self, args=None):
        self.parse_args(args, make_arg_parser=self.install_make_arg_parser)
        for p in self.get_packages():
            for c in self.get_cmake_components(p):
                self.do_cmake_install(self.get_build_directory(), p,
                                      component=c)


def install():
    dhcmake = DHCMake()
    dhcmake.install()
