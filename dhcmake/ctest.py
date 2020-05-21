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
    def make_arg_parser(self, parser):
        super().make_arg_parser(parser)

        parser.add_argument(
            "--no-submit", action="store_true",
            help="Don't submit after each part")
        parser.add_argument(
            "--ctest-build", action="store",
            help="Name of the CTest build")
        parser.add_argument(
            "extra_args", nargs="*")

    def get_dh_ctest_driver(self):
        return pkg_resources.resource_filename(__name__,
            "dh_ctest_driver.cmake")

    def do_ctest_step(self, step, cmd=None):
        dashboard_model = get_deb_ctest_option("model")
        if dashboard_model is None:
            if cmd is not None:
                self.do_cmd([cmd, *self.parsed_args])
            return False
        else:
            args = [
                "ctest", "-VV", "-S", self.get_dh_ctest_driver(),
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
            if get_deb_ctest_option("submit") and not self.options.no_submit:
                args.append("-DDH_CTEST_STEP_SUBMIT:BOOL=ON")

            site = get_deb_ctest_option("site")
            if isinstance(site, str):
                args.append("-DDH_CTEST_SITE:STRING=" + site)

            build = get_deb_ctest_option("build")
            if self.options.ctest_build:
                build = self.options.ctest_build
            if isinstance(build, str):
                args.append("-DDH_CTEST_BUILD:STRING=" + build)

            if step == "submit" and self.options.parts:
                args.append("-DDH_CTEST_SUBMIT_PARTS:STRING=" +
                        ";".join(self.options.parts))

            args.extend(self.options.extra_args)
            self.do_cmd(args)
            return True

    @common.DHEntryPoint("dh_ctest_start")
    def start(self, args=None):
        self.parse_args(args)
        self.do_ctest_step("start")

    @common.DHEntryPoint("dh_ctest_configure")
    def configure(self, args=None):
        self.parse_args(args)
        self.do_ctest_step("configure", "dh_auto_configure")

    @common.DHEntryPoint("dh_ctest_build")
    def build(self, args=None):
        self.parse_args(args)
        self.do_ctest_step("build", "dh_auto_build")

    @common.DHEntryPoint("dh_ctest_test")
    def test(self, args=None):
        self.parse_args(args)
        if not self.do_ctest_step("test"):
            self.do_cmd(["ctest", "-VV", *self.options.extra_args],
                        cwd=self.get_build_directory())

    def submit_make_arg_parser(self, parser):
        super().make_arg_parser(parser)

        parser.add_argument("--parts", action="store", nargs="*",
                            help="Parts to submit to CDash")

    @common.DHEntryPoint("dh_ctest_submit")
    def submit(self, args=None):
        self.parse_args(args, make_arg_parser=self.submit_make_arg_parser)
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
