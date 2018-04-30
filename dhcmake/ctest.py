# This file is part of dh-cmake, and is distributed under the OSI-approved
# BSD 3-Clause license. See top-level LICENSE file or
# https://gitlab.kitware.com/debian/dh-cmake/blob/master/LICENSE for details.

import os.path
import pkg_resources

from dhcmake import common


class DHCTest(common.DHCommon):
    def get_dh_ctest_driver(self):
        return pkg_resources.resource_filename(__name__,
            "dh_ctest_driver.cmake")

    def do_ctest_step(self, step, extra_params=None, suppress_output=False):
        args = [
            "ctest", "-S", self.get_dh_ctest_driver(),
            "-DDH_CTEST_SRCDIR=" + os.getcwd(),
            "-DDH_CTEST_CTESTDIR=" + os.path.join(os.getcwd(),
                                                  "debian/.ctest"),
            "-DDH_CTEST_BUILDDIR=" + self.get_build_directory(),
            "-DDH_CTEST_DASHBOARD_MODEL=Experimental",
            "-DDH_CTEST_CONFIGURE_CMD=dh_auto_configure",
            "-DDH_CTEST_BUILD_CMD=dh_auto_build",
            "-DDH_CTEST_STEP=" + step,
        ]
        self.do_cmd(args, suppress_output=suppress_output)

    def start(self):
        self.do_ctest_step("start")

    def configure(self):
        self.do_ctest_step("configure")

    def build(self):
        self.do_ctest_step("build")

    def test(self):
        self.do_ctest_step("test")

    def submit(self):
        self.do_ctest_step("submit")


def start():
    dhctest = DHCTest()
    dhctest.parse_args()
    dhctest.start()


def configure():
    dhctest = DHCTest()
    dhctest.parse_args()
    dhctest.configure()


def build():
    dhctest = DHCTest()
    dhctest.parse_args()
    dhctest.build()


def test():
    dhctest = DHCTest()
    dhctest.parse_args()
    dhctest.test()


def submit():
    dhctest = DHCTest()
    dhctest.parse_args()
    dhctest.submit()
