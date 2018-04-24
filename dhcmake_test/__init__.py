# This file is part of dh-cmake.
# See top-level LICENSE file for license information.

import os.path
from unittest import TestCase

import dhcmake_test


class DHCMakeTestCaseBase(TestCase):
    def write_src_file(self, filename, contents):
        with open(os.path.join(self.src_dir.name, filename), "w") as f:
            f.write(contents)

    def make_src_dir(self, filename):
        os.mkdir(os.path.join(self.src_dir.name, filename))

    def make_sub_lib(self, libname):
        self.make_src_dir(libname)
        self.write_src_file(os.path.join(libname, "CMakeLists.txt"),
                            "declare_lib({0})".format(libname))
        self.write_src_file(os.path.join(libname, libname + ".c"), "")
        self.write_src_file(os.path.join(libname, libname + ".h"), "")

    def assertFileExists(self, path):
        assertTrue(os.path.exists(
            path, "File '{0}' does not exist".format(path)))

    def assertFileNotExists(self, path):
        assertFalse(os.path.exists(
            path, "File '{0}' exists".format(path)))

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
