# This file is part of dh-cmake, and is distributed under the OSI-approved
# BSD 3-Clause license. See top-level LICENSE file or
# https://gitlab.kitware.com/debian/dh-cmake/blob/master/LICENSE for details.

import os.path

from dhcmake import common


class DHCMake(common.DHCommon):
    def get_cmake_components(self, package):
        opened_file = self.read_package_file(package, "cmake-components")
        if opened_file:
            with opened_file as f:
                return [l.rstrip() for l in f]
        else:
            return []

    def do_cmake_install(self, builddir, destdir, component=None):
        args = ["cmake"]
        if component:
            args += ["-DCOMPONENT=" + component]
        args += ["-P", os.path.join(builddir, "cmake_install.cmake")]
        env = os.environ.copy()
        env["DESTDIR"] = destdir
        self.do_cmd(args, env=env)

    def install(self, args=None):
        self.parse_args(args)
        for p in self.get_packages():
            for c in self.get_cmake_components(p):
                self.do_cmake_install(self.get_build_directory(),
                                      self.get_tmpdir(p), c)


def install():
    dhcmake = DHCMake()
    dhcmake.install()
