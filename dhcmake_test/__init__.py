# This file is part of dh-cmake.
# See top-level LICENSE file for license information.

import os.path
import shutil
import tempfile
from unittest import TestCase

import dhcmake.common


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


class KWTestCaseBase(TestCase):
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

    @classmethod
    def replace_arch_in_paths(cls, paths):
        return (p.format(arch=dhcmake.common \
                .dpkg_architecture()["DEB_HOST_GNU_TYPE"])
            for p in paths)


class DebianSourcePackageTestCaseBase(KWTestCaseBase):
    def setUp(self):
        test_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(test_dir)
        test_data_dir = os.path.join(root_dir, "test_data")
        debian_pkg_dir = os.path.join(test_data_dir, "debian_pkg")

        self.tmp_dir = tempfile.TemporaryDirectory()
        self.src_dir = os.path.join(self.tmp_dir.name, "src")

        shutil.copytree(debian_pkg_dir, self.src_dir)

        self.old_cwd = os.getcwd()
        os.chdir(self.src_dir)

    def tearDown(self):
        os.chdir(self.old_cwd)

        self.tmp_dir.cleanup()

    def make_directory_in_tmp(self, name):
        path = os.path.join(self.tmp_dir.name, name)
        os.mkdir(path)
        return path

    def open(self, filename, *args, **kwargs):
        path = os.path.join(self.src_dir, filename)
        return open(path, *args, **kwargs)


class VolatileNamedTemporaryFileTestCase(KWTestCaseBase):
    def test_normal_delete(self):
        with VolatileNamedTemporaryFile() as f:
            pass
        self.assertVolatileFileNotExists(f.name)

    def test_already_deleted(self):
        with VolatileNamedTemporaryFile() as f:
            os.unlink(f.name)
        self.assertVolatileFileNotExists(f.name)
