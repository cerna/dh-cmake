# This file is part of dh-cmake, and is distributed under the OSI-approved
# BSD 3-Clause license. See top-level LICENSE file or
# https://gitlab.kitware.com/debian/dh-cmake/blob/master/LICENSE for details.

import errno
import os.path
import shutil
import subprocess
import sys
import tempfile
from unittest import TestCase

import dhcmake.common
import dhcmake.arch


class VolatileNamedTemporaryFile:
    def __init__(self, *args, **kwargs):
        self.ntf = tempfile.NamedTemporaryFile(*args, **kwargs)

    def close(self):
        try:
            self.ntf.close()
        except OSError as e:
            if e.errno != errno.ENOENT:
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

    def assertFileContentsEqual(self, expected_contents, path):
        with open(path) as f:
            self.assertEqual(expected_contents, f.read())

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
        return (p.format(arch=dhcmake.arch \
                .dpkg_architecture()["DEB_HOST_GNU_TYPE"])
            for p in paths)

    def get_single_element(self, l):
        self.assertEqual(1, len(l))
        return l[0]

    @classmethod
    def run_cmd(cls, args, cwd=None, env=None):
        subprocess.run(args, cwd=cwd, env=env, check=True)


class DebianSourcePackageTestCaseBase(KWTestCaseBase):
    @classmethod
    def push_path(cls, name, value):
        try:
            old = os.environ[name]
        except KeyError:
            old = None

        if old is None:
            os.environ[name] = value
        else:
            os.environ[name] = value + ":" + old

        return old

    @classmethod
    def pop_path(cls, name, value):
        if value is None:
            del os.environ[name]
        else:
            os.environ[name] = value

    @classmethod
    def setUpClass(cls):
        test_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(test_dir))
        perl5_dir = os.path.join(root_dir, "perl5")

        cls.scripts_install_dir = tempfile.TemporaryDirectory()

        cls.run_cmd([os.path.join(root_dir, "setup.py"), "install_scripts",
                     "--install-dir=" + cls.scripts_install_dir.name])

        cls.old_path = cls.push_path("PATH", cls.scripts_install_dir.name)
        cls.old_perl5lib = cls.push_path("PERL5LIB", perl5_dir)
        cls.old_pythonpath = cls.push_path("PYTHONPATH", root_dir)

    @classmethod
    def tearDownClass(cls):
        cls.pop_path("PYTHONPATH", cls.old_pythonpath)
        cls.pop_path("PERL5LIB", cls.old_perl5lib)
        cls.pop_path("PATH", cls.old_path)

        cls.scripts_install_dir.cleanup()

    def setUp(self):
        self.dh = self.DHClass()

        test_dir = os.path.dirname(os.path.abspath(__file__))
        test_data_dir = os.path.join(test_dir, "data")
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
        os.makedirs(path)
        return path

    def run_debian_rules(self, rule, case=None):
        env = os.environ.copy()
        if case:
            env["DH_CMAKE_CASE"] = case

        self.run_cmd(["debian/rules", rule], env=env)


class VolatileNamedTemporaryFileTestCase(KWTestCaseBase):
    def test_normal_delete(self):
        with VolatileNamedTemporaryFile() as f:
            pass
        self.assertVolatileFileNotExists(f.name)

    def test_already_deleted(self):
        with VolatileNamedTemporaryFile() as f:
            os.unlink(f.name)
        self.assertVolatileFileNotExists(f.name)
