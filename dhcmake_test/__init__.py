# This file is part of dh-cmake.
# See top-level LICENSE file for license information.

import os.path
import tempfile
from unittest import TestCase, skip

from dhcmake import common
import dhcmake_test


DEBIAN_CONTROL = \
r"""Source: libdhcmake-test
Maintainer: Kitware Debian Maintainers <debian@kitware.com>

Package: libdhcmake-test
Architecture: any

Package: libdhcmake-test-dev
Architecture: any

Package: libdhcmake-test-doc
Architecture: all
"""


class VolatileNamedTemporaryFile:
    def __init__(self, *args, **kwargs):
        self.ntf = tempfile.NamedTemporaryFile(*args, **kwargs)

    def close(self):
        try:
            self.ntf.close()
        except OSError as e:
            if e.errno != os.errno.ENOENT:
                raise

    @property
    def name(self):
        return self.ntf.name

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class DHCMakeTestCaseBase(TestCase):
    def assertFileExists(self, path):
        self.assertTrue(os.path.exists(
            path), "File '{0}' does not exist".format(path))

    def assertFileNotExists(self, path):
        self.assertFalse(os.path.exists(
            path), "File '{0}' exists".format(path))

    def assertFileTreeEqual(self, expected_files, path):
        actual_files = set()
        for dirpath, dirnames, filenames in os.walk(path):
            rel = os.path.relpath(dirpath, path)
            if rel == ".":
                actual_files.update(dirnames)
                actual_files.update(filenames)
            else:
                actual_files.update(os.path.join(rel, p) for p in dirnames)
                actual_files.update(os.path.join(rel, p) for p in filenames)

        self.assertEqual(expected_files, actual_files)

    def assertVolatileFileNotExists(self, name):
        try:
            self.assertFileNotExists(name)
        except AssertionError:
            os.unlink(name)
            raise


class VolatileNamedTemporaryFileTestCase(DHCMakeTestCaseBase):
    def test_normal_delete(self):
        with VolatileNamedTemporaryFile() as f:
            pass
        self.assertVolatileFileNotExists(f.name)

    def test_already_deleted(self):
        with VolatileNamedTemporaryFile() as f:
            os.unlink(f.name)
        self.assertVolatileFileNotExists(f.name)


class RunCMakeTestCaseBase(DHCMakeTestCaseBase):
    def setUp(self):
        self.src_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.src_dir.cleanup()

    def write_src_file(self, filename, contents):
        with open(os.path.join(self.src_dir.name, filename), "w") as f:
            f.write(contents)

    def make_src_dir(self, filename):
        os.mkdir(os.path.join(self.src_dir.name, filename))


class DHCMakeBaseTestCase(RunCMakeTestCaseBase):
    def setUp(self):
        super().setUp()
        self.dhcmake_base = common.DHCMakeBase()

        self.make_src_dir("debian")

        self.write_src_file("debian/control", DEBIAN_CONTROL)

        self.old_cwd = os.getcwd()
        os.chdir(self.src_dir.name)

    def tearDown(self):
        os.chdir(self.old_cwd)
        super().tearDown()

    def check_packages(self, expected_packages):
        self.assertEqual(expected_packages, set(self.dhcmake_base.get_packages()))

    def test_do_cmd(self):
        self.dhcmake_base.parse_args([])

        with VolatileNamedTemporaryFile() as f:
            self.dhcmake_base.do_cmd(["rm", f.name])
            self.assertVolatileFileNotExists(f.name)

    def test_do_cmd_no_act(self):
        self.dhcmake_base.parse_args(["--no-act"])

        with VolatileNamedTemporaryFile() as f:
            self.dhcmake_base.do_cmd(["rm", f.name])
            self.assertFileExists(f.name)

    @skip("Not implemented yet")
    def test_get_packages_default(self):
        self.dhcmake_base.parse_args([])

        self.check_packages({
            "libdhcmake-test",
            "libdhcmake-test-dev",
            "libdhcmake-test-doc",
        })

    @skip("Not implemented yet")
    def test_get_packages_whitelist_short(self):
        self.dhcmake_base.parse_args(["-plibdhcmake-test-dev",
                                      "-plibdhcmake-test-doc"])

        self.check_packages({
            "libdhcmake-test-dev",
            "libdhcmake-test-doc",
        })

    @skip("Not implemented yet")
    def test_get_packages_whitelist_long(self):
        self.dhcmake_base.parse_args(["--package", "libdhcmake-test-dev",
                                      "--package", "libdhcmake-test-doc"])

        self.check_packages({
            "libdhcmake-test-dev",
            "libdhcmake-test-doc",
        })

    @skip("Not implemented yet")
    def test_get_packages_blacklist_short(self):
        self.dhcmake_base.parse_args(["-Nlibdhcmake-test-dev",
                                      "-Nlibdhcmake-test-doc"])

        self.check_packages({
            "libdhcmake-test",
        })

    @skip("Not implemented yet")
    def test_get_packages_blacklist_long(self):
        self.dhcmake_base.parse_args(["--no-package", "libdhcmake-test-dev",
                                      "--no-package", "libdhcmake-test-doc"])

        self.check_packages({
            "libdhcmake-test",
        })
