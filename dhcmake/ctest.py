# This file is part of dh-cmake, and is distributed under the OSI-approved
# BSD 3-Clause license. See top-level LICENSE file or
# https://gitlab.kitware.com/debian/dh-cmake/blob/master/LICENSE for details.

import os.path
import pkg_resources

from dhcmake import common


def format_arg_for_ctest(arg):
    arg = arg.replace("\\", "\\\\")
    arg = arg.replace('"', '\\"')
    arg = arg.replace("'", "\\'")
    arg = arg.replace(" ", "\\ ")
    arg = arg.replace("\t", "\\\t")
    return arg


def format_args_for_ctest(args):
    return " ".join(format_arg_for_ctest(a) for a in args)


class DHCTest(common.DHCommon):
    def get_dh_ctest_driver(self):
        return pkg_resources.resource_filename(__name__,
            "dh_ctest_driver.cmake")

    def do_ctest_step(self, step, extra_params=None, suppress_output=False):
        args = [
            "ctest", "-S", self.get_dh_ctest_driver(),
            "-DDH_CTEST_SRCDIR:PATH=" + os.getcwd(),
            "-DDH_CTEST_CTESTDIR:PATH=" + os.path.join(os.getcwd(),
                                                       "debian/.ctest"),
            "-DDH_CTEST_BUILDDIR:PATH=" + self.get_build_directory(),
            "-DDH_CTEST_DASHBOARD_MODEL:STRING=Experimental",
            "-DDH_CTEST_CONFIGURE_CMD:STRING=" \
                + format_args_for_ctest(["dh_auto_configure",
                                         *self.parsed_args]),
            "-DDH_CTEST_BUILD_CMD:STRING=" \
                + format_args_for_ctest(["dh_auto_build",
                                         *self.parsed_args]),
            "-DDH_CTEST_STEP:STRING=" + step,
        ]
        self.do_cmd(args, suppress_output=suppress_output)

    def start(self, args=None):
        self.parse_args(args)
        self.do_ctest_step("start")

    def configure(self, args=None):
        self.parse_args(args)
        self.do_ctest_step("configure")

    def build(self, args=None):
        self.parse_args(args)
        self.do_ctest_step("build")

    def test(self, args=None):
        self.parse_args(args)
        self.do_ctest_step("test")

    def submit(self, args=None):
        self.parse_args(args)
        self.do_ctest_step("submit")


def start():
    dhctest = DHCTest()
    dhctest.start()


def configure():
    dhctest = DHCTest()
    dhctest.configure()


def build():
    dhctest = DHCTest()
    dhctest.build()


def test():
    dhctest = DHCTest()
    dhctest.test()


def submit():
    dhctest = DHCTest()
    dhctest.submit()
