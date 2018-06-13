# This file is part of dh-cmake, and is distributed under the OSI-approved
# BSD 3-Clause license. See top-level LICENSE file or
# https://gitlab.kitware.com/debian/dh-cmake/blob/master/LICENSE for details.

import argparse
import io
import os.path
import subprocess
import sys

from dhcmake import deb822


_dpkg_architecture_values = None


def dpkg_architecture():
    global _dpkg_architecture_values
    if _dpkg_architecture_values is None:
        _dpkg_architecture_values = dict()
        proc = subprocess.run(["dpkg-architecture"], stdout=subprocess.PIPE)
        output = proc.stdout.decode()
        for line in output.split("\n"):
            if line:
                key, value = line.split("=", maxsplit=1)
                _dpkg_architecture_values[key] = value

    return _dpkg_architecture_values


def format_arg_for_print(arg):
    arg = arg.replace("\\", "\\\\")
    arg = arg.replace('"', '\\"')
    arg = arg.replace("'", "\\'")
    arg = arg.replace("$", "\\$")
    if " " in arg:
        return '"%s"' % arg
    else:
        return arg


class DHCommon:
    def __init__(self):
        self.options = argparse.Namespace()
        self.options.type = "both"
        self.stdout = sys.stdout
        self.stdout_b = sys.stdout
        self.stderr = sys.stderr
        self.stderr_b = sys.stderr

    def _parse_args(self, parser, args, known):
        if known:
            parser.parse_known_args(args=args, namespace=self.options)
        else:
            parser.parse_args(args=args, namespace=self.options)

        if self.options.options:
            options = self.options.options
            self.options.options = []
            self._parse_args(parser, options, True)

    def parse_args(self, args=None):
        parser = argparse.ArgumentParser()
        self.make_arg_parser(parser)

        if args is None:
            self.parsed_args = sys.argv[1:]
        else:
            self.parsed_args = list(args)

        self._parse_args(parser, args, False)

    def make_arg_parser(self, parser):
        # Required arguments
        parser.add_argument(
            "-v", "--verbose", action="store_true", help="Verbose output")
        parser.add_argument(
            "--no-act", action="store_true",
            help="Dry run (don't actually do anything)")
        parser.add_argument(
            "-a", "-s", "--arch", action="store_const", const="arch",
            dest="type", help="Act on all architecture dependent packages")
        parser.add_argument(
            "-i", "--indep", action="store_const", const="indep",
            dest="type", help="Act on all architecture independent packages")
        parser.add_argument(
            "-p", "--package", action="append",
            help="Act on a specific package or set of packages")
        parser.add_argument(
            "-N", "--no-package", action="append",
            help="Do not act on a specific package or set of packages")
        parser.add_argument(
            "--remaining-packages", action="append",
            help="Do not act on packages which have already been acted on")
        parser.add_argument(
            "--ignore", action="append", help="Ignore a file or set of files")
        parser.add_argument(
            "-P", "--tmpdir", action="store",
            help="Use tmpdir for package build directory")
        parser.add_argument(
            "--mainpackage", action="store",
            help="Change which package is the \"main package\"")
        parser.add_argument(
            "-O", action="append",
            help="Pass additional arguments to called programs",
            dest="options")

        # More arguments
        parser.add_argument(
            "-B", "--builddirectory", action="store",
            help="Build directory for out of source building",
            default="obj-" + dpkg_architecture()["DEB_HOST_GNU_TYPE"])

    def do_cmd(self, args, env=None, cwd=None):
        if self.options.verbose:
            print_args = (format_arg_for_print(a) for a in args)
            print("\t" + " ".join(print_args), file=self.stdout)
        if not self.options.no_act:
            subprocess.run(args, stdout=self.stdout, stderr=self.stderr,
                           env=env, cwd=cwd, check=True)

    def get_packages(self):
        with open("debian/control", "r") as f:
            source, packages = deb822.read_control(f)

        result = []

        for p in packages:
            name = p["package"]
            if self.options.package:
                if name in self.options.package:
                    result.append(name)
            elif self.options.no_package:
                if name not in self.options.no_package:
                    result.append(name)
            elif self.options.type == "indep":
                if p["architecture"] == "all":
                    result.append(name)
            elif self.options.type == "arch":
                if p["architecture"] == "any":
                    result.append(name)
            elif self.options.type == "both":
                result.append(name)

        return result

    def get_main_package(self):
        if self.options.mainpackage:
            return self.options.mainpackage
        else:
            with open("debian/control", "r") as f:
                source, packages = deb822.read_control(f)

            return packages[0]["package"]

    def get_package_file(self, package, extension):
        paths = [
            os.path.join("debian", package + "." + extension),
        ]

        if package == self.get_main_package():
            paths.append(os.path.join("debian", extension))

        for p in paths:
            if os.path.exists(p):
                return p
        return None

    def read_package_file(self, package, extension):
        path = self.get_package_file(package, extension)
        if path is None:
            return None
        elif os.access(path, os.X_OK):
            return io.StringIO(subprocess.check_output(
                [os.path.abspath(path)]).decode("utf-8"))
        else:
            return open(path, "r")

    def get_build_directory(self):
        return self.options.builddirectory

    def get_tmpdir(self, package):
        if self.options.tmpdir:
            return self.options.tmpdir
        else:
            return os.path.join("debian", package)
