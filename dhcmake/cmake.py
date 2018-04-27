# This file is part of dh-cmake.
# See top-level LICENSE file for license information.

import os.path
import subprocess

from dhcmake import common


class DHCMake(common.DHCommon):
    def get_cmake_components(self, package):
        opened_file = self.read_package_file(package, "cmake-components")
        if opened_file:
            with opened_file as f:
                return [l.rstrip() for l in f]
        else:
            return []

    def do_cmake_install(self, builddir, destdir, component=None,
                         suppress_output=False):
        args = ["cmake"]
        if component:
            args += ["-DCOMPONENT=" + component]
        args += ["-P", os.path.join(builddir, "cmake_install.cmake")]
        env = os.environ.copy()
        env["DESTDIR"] = destdir
        self.do_cmd(args, env=env, suppress_output=suppress_output)

    def install(self):
        for p in self.get_packages():
            for c in self.get_cmake_components(p):
                self.do_cmake_install(self.get_build_directory(),
                                      self.get_tmpdir(p), c)


def install():
    dhcmake = DHCMake()
    dhcmake.parse_args()
    dhcmake.install()
