# This file is part of dh-cmake, and is distributed under the OSI-approved
# BSD 3-Clause license. See top-level LICENSE file or
# https://gitlab.kitware.com/debian/dh-cmake/blob/master/LICENSE for details.

import os.path
import pkg_resources
import re

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


def get_deb_ctest_option(name):
    try:
        deb_ctest_options = os.environ["DEB_CTEST_OPTIONS"]
    except KeyError:
        return None

    split = re.split("\\s+", deb_ctest_options)
    for item in split:
        eq_split = item.split("=", 1)
        if eq_split[0] == name:
            if len(eq_split) > 1:
                return eq_split[1]
            else:
                return True

    return None


class DHCTest(common.DHCommon):
    def get_dh_ctest_driver(self):
        return pkg_resources.resource_filename(__name__,
            "dh_ctest_driver.cmake")

    def do_ctest_step(self, step, cmd=None):
        dashboard_model = get_deb_ctest_option("model")
        if dashboard_model is None:
            if cmd is not None:
                self.do_cmd([cmd, *self.parsed_args])
        else:
            args = [
                "ctest", "-S", self.get_dh_ctest_driver(),
                "-DDH_CTEST_SRCDIR:PATH=" + os.getcwd(),
                "-DDH_CTEST_CTESTDIR:PATH=" + os.path.join(os.getcwd(),
                                                           "debian/.ctest"),
                "-DDH_CTEST_BUILDDIR:PATH=" + self.get_build_directory(),
                "-DDH_CTEST_DASHBOARD_MODEL:STRING=" + dashboard_model,
                "-DDH_CTEST_STEP:STRING=" + step,
            ]
            if cmd:
                args.append("-DDH_CTEST_RUN_CMD:STRING=" \
                    + format_args_for_ctest([cmd, *self.parsed_args]))
            if get_deb_ctest_option("submit"):
                args.append("-DDH_CTEST_STEP_SUBMIT:BOOL=ON")
            self.do_cmd(args)

    def start(self, args=None):
        self.parse_args(args)
        self.do_ctest_step("start")

    def configure(self, args=None):
        self.parse_args(args)
        self.do_ctest_step("configure", "dh_auto_configure")

    def build(self, args=None):
        self.parse_args(args)
        self.do_ctest_step("build", "dh_auto_build")

    def test(self, args=None):
        self.parse_args(args)
        self.do_ctest_step("test", "dh_auto_test")

    def submit(self, args=None):
        self.parse_args(args)
        if get_deb_ctest_option("submit"):
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
