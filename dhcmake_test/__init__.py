# This file is part of dh-cmake.
# See top-level LICENSE file for license information.

import os.path
import tempfile
from unittest import TestCase

from dhcmake import common
import dhcmake_test


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

    def test_get_packages_default(self):
        pass
