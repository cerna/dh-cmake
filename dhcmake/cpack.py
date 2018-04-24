#!/usr/bin/env python3

# This file is part of dh-cmake.
# See top-level LICENSE file for license information.

import dhcmake.common

import os.path
import re


class DHCPack(dhcmake.common.DHCMakeBase):
    def do_cmake_install(self, builddir, destdir, component=None,
                         suppress_output=False):
        args = ["cmake"]
        if component:
            args += ["-DCOMPONENT=" + component]
        args += ["-P", os.path.join(builddir, "cmake_install.cmake")]
        env = os.environ.copy()
        env["DESTDIR"] = destdir
        self.do_cmd(args, env=env, suppress_output=suppress_output)
