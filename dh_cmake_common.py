# This file is part of dh-cmake.
# See top-level LICENSE file for license information.

import argparse
import os.path
import subprocess
import sys


dpkg_architecture_values = None


def dpkg_architecture():
    global dpkg_architecture_values
    if dpkg_architecture_values is None:
        dpkg_architecture_values = dict()
        proc = subprocess.run(["dpkg-architecture"], stdout=subprocess.PIPE)
        output = proc.stdout.decode()
        for line in output.split("\n"):
            if line:
                key, value = line.split("=", maxsplit=1)
                dpkg_architecture_values[key] = value

    return dpkg_architecture_values

def get_options(parser, args, ns, known):
    if known:
        parser.parse_known_args(args=args, namespace=ns)
    else:
        parser.parse_args(args=args, namespace=ns)

    if ns.options:
        options = ns.options
        ns.options = []
        get_options(parser, options, ns, True)

def init():
    parser = argparse.ArgumentParser()

    # Required arguments
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--no-act", action="store_true", help="Dry run (don't actually do anything)")
    parser.add_argument("-a", "-s", "--arch", action="store_true", help="Act on all architecture dependent packages")
    parser.add_argument("-i", "--indep", action="store_true", help="Act on all architecture independent packages")
    parser.add_argument("-p", "--package", action="append", help="Act on a specific package or set of packages")
    parser.add_argument("-N", "--no-package", action="append", help="Do not act on a specific package or set of packages")
    parser.add_argument("--remaining-packages", action="append", help="Do not act on packages which have already been acted on")
    parser.add_argument("--ignore", action="append", help="Ignore a file or set of files")
    parser.add_argument("-P", "--tmpdir", action="store", help="Use tmpdir for package build directory")
    parser.add_argument("--mainpackage", action="store", help="Change which package is the \"main package\"")
    parser.add_argument("-O", action="append", help="Pass additional arguments to called programs", dest="options")

    # More arguments
    parser.add_argument("-B", "--builddirectory", action="store", help="Build directory for out of source building", \
            default=os.path.join(os.getcwd(), "obj-" + dpkg_architecture()["DEB_HOST_GNU_TYPE"]))

    global options
    options = argparse.Namespace()
    get_options(parser, None, options, False)

def format_arg_for_print(arg):
    arg = arg.replace("\\", "\\\\")
    arg = arg.replace('"', '\\"')
    arg = arg.replace("'", "\\'")
    arg = arg.replace("$", "\\$")
    if " " in arg:
        return '"%s"' % arg
    else:
        return arg

def do_cmd(args):
    if options.verbose:
        print_args = (format_arg_for_print(a) for a in args)
        print("\t" + " ".join(print_args))
    if not options.no_act:
        subprocess.run(args, stdout=sys.stdout, stderr=sys.stderr)
