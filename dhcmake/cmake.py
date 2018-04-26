# This file is part of dh-cmake.
# See top-level LICENSE file for license information.

import io
import os.path
import subprocess

from dhcmake import common


class DHCMake(common.DHCMakeBase):
    def get_cmake_components(self, package):
        package_file = os.path.abspath(
            self.get_package_file(package, "cmake-components"))
        if os.path.exists(package_file):
            if os.access(package_file, os.X_OK):
                contents = subprocess.check_output([package_file]).decode("utf-8")
            else:
                with open(package_file, "r") as f:
                    contents = f.read()

            return [l.rstrip() for l in io.StringIO(contents)]
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
