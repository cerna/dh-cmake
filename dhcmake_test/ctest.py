# This file is part of dh-cmake, and is distributed under the OSI-approved
# BSD 3-Clause license. See top-level LICENSE file or
# https://gitlab.kitware.com/debian/dh-cmake/blob/master/LICENSE for details.

import http.server
import re
import threading
import urllib.parse
import xml.etree.ElementTree

from dhcmake import common, ctest
from dhcmake_test import *


class PushEnvironmentVariable:
    def __init__(self, name, value):
        self.name = name
        try:
            self.old_value = os.environ[name]
        except KeyError:
            self.old_value = None

        os.environ[name] = value

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.old_value is None:
            del os.environ[self.name]
        else:
            os.environ[self.name] = self.old_value


class PushEnvironmentVariableTestCase(KWTestCaseBase):
    varname = "DH_CMAKE_TEST_VARIABLE_DO_NOT_SET"

    def test_create_new(self):
        try:
            del os.environ[self.varname]
        except KeyError:
            pass

        with PushEnvironmentVariable(self.varname, "value"):
            self.assertEqual("value", os.environ[self.varname])

        self.assertNotIn(self.varname, os.environ)

    def test_change(self):
        os.environ[self.varname] = "old"

        with PushEnvironmentVariable(self.varname, "new"):
            self.assertEqual("new", os.environ[self.varname])

        self.assertEqual("old", os.environ[self.varname])


class MockCDashServerHandler(http.server.BaseHTTPRequestHandler):
    def do_PUT(self):
        match = re.search(r"^/submit\.php\?(.*)$", self.path)
        if not match:
            self.send_error(404)
            return
        query_string_params = urllib.parse.parse_qs(match.group(1))

        if query_string_params["project"] != ["dh-cmake-test"]:
            self.send_error(404)
            return

        self.send_response(100)
        self.end_headers()
        self.flush_headers()

        input_file = self.rfile.read(int(self.headers.get("content-length")))
        self.server.submitted_files.add(input_file)

        self.send_response(200)
        self.end_headers()
        self.flush_headers()

    def log_message(self, format, *args):
        pass


class MockCDashServer(http.server.HTTPServer):
    def __init__(self, server_address):
        super().__init__(server_address, MockCDashServerHandler)

        self.submitted_files = set()


class DHCTestTestCase(DebianSourcePackageTestCaseBase):
    DHClass = ctest.DHCTest

    def setUp(self):
        super().setUp()

        try:
            del os.environ["DEB_CTEST_OPTIONS"]
        except KeyError:
            pass  # No variable, no problem

        self.cdash_server = MockCDashServer(("127.0.0.1", 47806))
        self.cdash_server_thread = \
            threading.Thread(target=self.cdash_server.serve_forever)
        self.cdash_server_thread.daemon = True
        self.cdash_server_thread.start()

    def tearDown(self):
        self.cdash_server.shutdown()
        self.cdash_server_thread.join()
        self.cdash_server.server_close()

        super().tearDown()

    def assertFilesSubmittedEqual(self, steps):
        contents_set = set()
        for step in steps:
            date = self.get_testing_tag_date()
            with open(os.path.join("debian/.ctest/Testing", date,
                                   step + ".xml"), "rb") as f:
                contents = f.read()
            contents_set.add(contents)

        self.assertEqual(contents_set, self.cdash_server.submitted_files)

    def get_testing_tag_date(self):
        with open("debian/.ctest/Testing/TAG", "r") as f:
            return next(f).rstrip()

    def test_start_none(self):
        self.assertFileNotExists("debian/.ctest/Testing/TAG")
        self.dh.start([])
        self.assertFileNotExists("debian/.ctest/Testing/TAG")

    def test_start_experimental(self):
        self.assertFileNotExists("debian/.ctest/Testing/TAG")

        with PushEnvironmentVariable("DEB_CTEST_OPTIONS",
                                     "model=Experimental"):
            self.dh.start([])
            with open("debian/.ctest/Testing/TAG", "r") as f:
                self.assertRegex(next(f), "^[0-9]{8}-[0-9]{4}$")
                self.assertEqual("Experimental", next(f).rstrip())
                try:  # Extra line here as of CMake 3.12
                    self.assertEqual("Experimental", next(f).rstrip())
                except StopIteration:
                    pass
                with self.assertRaises(StopIteration):
                    next(f)

    def test_start_nightly(self):
        self.assertFileNotExists("debian/.ctest/Testing/TAG")

        with PushEnvironmentVariable("DEB_CTEST_OPTIONS", "model=Nightly"):
            self.dh.start([])
            with open("debian/.ctest/Testing/TAG", "r") as f:
                self.assertRegex(next(f), "^[0-9]{8}-[0-9]{4}$")
                self.assertEqual("Nightly", next(f).rstrip())
                try:  # Extra line here as of CMake 3.12
                    self.assertEqual("Nightly", next(f).rstrip())
                except StopIteration:
                    pass
                with self.assertRaises(StopIteration):
                    next(f)

    def test_configure_none(self):
        self.dh.start([])
        self.dh.configure([])

        self.assertFileNotExists(os.path.join("debian/.ctest/Testing/TAG"))
        self.assertFileExists(os.path.join(self.dh.get_build_directory(),
                                           "CMakeCache.txt"))

    def test_configure_none_bad(self):
        self.dh.start([])
        with self.assertRaises(subprocess.CalledProcessError):
            self.dh.configure(["--", "-DDH_CMAKE_ENABLE_BAD_CONFIGURE:BOOL=ON"])

        self.assertFileNotExists(os.path.join("debian/.ctest/Testing/TAG"))
        self.assertFileExists(os.path.join(self.dh.get_build_directory(),
                                           "CMakeCache.txt"))

    def test_configure_experimental(self):
        with PushEnvironmentVariable("DEB_CTEST_OPTIONS",
                                     "model=Experimental"):
            self.dh.start([])
            self.dh.configure([])
            date = self.get_testing_tag_date()

            self.assertFileExists(os.path.join("debian/.ctest/Testing", date,
                                               "Configure.xml"))

            self.assertFileNotExists(os.path.join("debian/.ctest/Testing",
                                                  date, "Build.xml"))

            self.assertFileNotExists(
                os.path.join(self.dh.get_build_directory(),
                             "testflag.txt"))

            self.assertFilesSubmittedEqual({})

            with open(os.path.join("debian/.ctest/Testing", date,
                                   "Configure.xml"),
                      "r") as f:
                tree = xml.etree.ElementTree.fromstring(f.read())

            self.assertEqual("(empty)", tree.attrib["Name"])
            self.assertEqual("(empty)", tree.attrib["BuildName"])

    def test_configure_experimental_site_build_names(self):
        with PushEnvironmentVariable(
                "DEB_CTEST_OPTIONS",
                "model=Experimental site=debtest build=debian-cmake-test"):
            self.dh.start([])
            self.dh.configure([])
            date = self.get_testing_tag_date()

            with open(os.path.join("debian/.ctest/Testing", date,
                                   "Configure.xml"),
                      "r") as f:
                tree = xml.etree.ElementTree.fromstring(f.read())

            self.assertEqual("debtest", tree.attrib["Name"])
            self.assertEqual("debian-cmake-test", tree.attrib["BuildName"])

    def test_configure_experimental_submit(self):
        with PushEnvironmentVariable("DEB_CTEST_OPTIONS",
                                     "model=Experimental submit"):
            self.dh.start([])
            self.dh.configure([])
            date = self.get_testing_tag_date()

            self.assertFileExists(os.path.join("debian/.ctest/Testing", date,
                                               "Configure.xml"))

            self.assertFileNotExists(os.path.join("debian/.ctest/Testing",
                                                  date, "Build.xml"))

            self.assertFileNotExists(
                os.path.join(self.dh.get_build_directory(),
                             "testflag.txt"))

            self.assertFilesSubmittedEqual({"Configure"})

    def test_configure_experimental_no_submit(self):
        with PushEnvironmentVariable("DEB_CTEST_OPTIONS",
                                     "model=Experimental submit"):
            self.dh.start([])
            self.dh.configure(["-O--no-submit"])
            date = self.get_testing_tag_date()

            self.assertFileExists(os.path.join("debian/.ctest/Testing", date,
                                               "Configure.xml"))

            self.assertFileNotExists(os.path.join("debian/.ctest/Testing",
                                                  date, "Build.xml"))

            self.assertFileNotExists(
                os.path.join(self.dh.get_build_directory(),
                             "testflag.txt"))

            self.assertFilesSubmittedEqual({})

    def test_configure_experimental_args(self):
        with PushEnvironmentVariable("DEB_CTEST_OPTIONS",
                                     "model=Experimental"):
            self.dh.start([])
            self.dh.configure(["--", "-DDH_CMAKE_TEST_FLAG:BOOL=ON"])
            date = self.get_testing_tag_date()

            self.assertFileExists(os.path.join("debian/.ctest/Testing", date,
                                               "Configure.xml"))

            self.assertFileNotExists(os.path.join("debian/.ctest/Testing",
                                                  date, "Build.xml"))

            self.assertFileExists(
                os.path.join(self.dh.get_build_directory(),
                             "testflag.txt"))

    def test_configure_experimental_bad(self):
        with PushEnvironmentVariable("DEB_CTEST_OPTIONS",
                                     "model=Experimental"):
            self.dh.start([])
            with self.assertRaises(subprocess.CalledProcessError):
                self.dh.configure([
                    "--", "-DDH_CMAKE_ENABLE_BAD_CONFIGURE:BOOL=ON"])
            date = self.get_testing_tag_date()

            self.assertFileExists(os.path.join("debian/.ctest/Testing", date,
                                               "Configure.xml"))

            self.assertFileNotExists(os.path.join("debian/.ctest/Testing",
                                                  date, "Build.xml"))

            self.assertFilesSubmittedEqual({})

    def test_configure_experimental_bad_submit(self):
        with PushEnvironmentVariable("DEB_CTEST_OPTIONS",
                                     "model=Experimental submit"):
            self.dh.start([])
            with self.assertRaises(subprocess.CalledProcessError):
                self.dh.configure([
                    "--", "-DDH_CMAKE_ENABLE_BAD_CONFIGURE:BOOL=ON"])
            date = self.get_testing_tag_date()

            self.assertFileExists(os.path.join("debian/.ctest/Testing", date,
                                               "Configure.xml"))

            self.assertFileNotExists(os.path.join("debian/.ctest/Testing",
                                                  date, "Build.xml"))

            self.assertFilesSubmittedEqual({"Configure"})

    def test_build_none(self):
        self.dh.start([])
        self.dh.configure([])
        self.dh.build([])

        self.assertFileNotExists(os.path.join("debian/.ctest/Testing/TAG"))
        self.assertFileExists(os.path.join(self.dh.get_build_directory(),
                                           "CMakeCache.txt"))
        self.assertFileExists(os.path.join(self.dh.get_build_directory(),
                                           "libdh-cmake-test.so"))

    def test_build_none_bad(self):
        self.dh.start([])
        self.dh.configure(["--", "-DDH_CMAKE_ENABLE_BAD_BUILD:BOOL=ON"])
        with self.assertRaises(subprocess.CalledProcessError):
            self.dh.build([])

        self.assertFileNotExists(os.path.join("debian/.ctest/Testing/TAG"))
        self.assertFileExists(os.path.join(self.dh.get_build_directory(),
                                           "CMakeCache.txt"))
        self.assertFileNotExists(os.path.join(self.dh.get_build_directory(),
                                              "libdh-cmake-test.so"))

    def test_build_experimental(self):
        with PushEnvironmentVariable("DEB_CTEST_OPTIONS",
                                     "model=Experimental"):
            self.dh.start([])
            self.dh.configure([])
            self.dh.build([])
            date = self.get_testing_tag_date()

            self.assertFileExists(os.path.join("debian/.ctest/Testing", date,
                                               "Build.xml"))
            self.assertFileNotExists(os.path.join("debian/.ctest/Testing",
                                                  date, "Test.xml"))

            self.assertFilesSubmittedEqual({})

    def test_build_experimental_submit(self):
        with PushEnvironmentVariable("DEB_CTEST_OPTIONS",
                                     "model=Experimental submit"):
            self.dh.start([])
            self.dh.configure([])
            self.dh.build([])
            date = self.get_testing_tag_date()

            self.assertFileExists(os.path.join("debian/.ctest/Testing", date,
                                               "Build.xml"))
            self.assertFileNotExists(os.path.join("debian/.ctest/Testing",
                                                  date, "Test.xml"))

            self.assertFilesSubmittedEqual({"Configure", "Build"})

    def test_build_experimental_no_submit(self):
        with PushEnvironmentVariable("DEB_CTEST_OPTIONS",
                                     "model=Experimental submit"):
            self.dh.start([])
            self.dh.configure([])
            self.dh.build(["-O--no-submit"])
            date = self.get_testing_tag_date()

            self.assertFileExists(os.path.join("debian/.ctest/Testing", date,
                                               "Build.xml"))
            self.assertFileNotExists(os.path.join("debian/.ctest/Testing",
                                                  date, "Test.xml"))

            self.assertFilesSubmittedEqual({"Configure"})

    def test_build_experimental_bad(self):
        with PushEnvironmentVariable("DEB_CTEST_OPTIONS",
                                     "model=Experimental"):
            self.dh.start([])
            self.dh.configure([
                "--", "-DDH_CMAKE_ENABLE_BAD_BUILD:BOOL=ON"])
            with self.assertRaises(subprocess.CalledProcessError):
                self.dh.build([])
            date = self.get_testing_tag_date()

            self.assertFileExists(os.path.join("debian/.ctest/Testing", date,
                                               "Build.xml"))
            self.assertFileNotExists(os.path.join("debian/.ctest/Testing",
                                                  date, "Test.xml"))

            self.assertFilesSubmittedEqual({})

    def test_build_experimental_bad_submit(self):
        with PushEnvironmentVariable("DEB_CTEST_OPTIONS",
                                     "model=Experimental submit"):
            self.dh.start([])
            self.dh.configure([
                "--", "-DDH_CMAKE_ENABLE_BAD_BUILD:BOOL=ON"])
            with self.assertRaises(subprocess.CalledProcessError):
                self.dh.build([])
            date = self.get_testing_tag_date()

            self.assertFileExists(os.path.join("debian/.ctest/Testing", date,
                                               "Build.xml"))
            self.assertFileNotExists(os.path.join("debian/.ctest/Testing",
                                                  date, "Test.xml"))

            self.assertFilesSubmittedEqual({"Configure", "Build"})

    def test_test_none(self):
        self.dh.start([])
        self.dh.configure([])
        self.dh.build([])
        self.dh.test([])

        self.assertFileNotExists(os.path.join("debian/.ctest/Testing/TAG"))

    def test_test_none_bad(self):
        self.dh.start([])
        self.dh.configure(["--", "-DDH_CMAKE_ENABLE_BAD_TEST:BOOL=ON"])
        self.dh.build([])
        with self.assertRaises(subprocess.CalledProcessError):
            self.dh.test([])

        self.assertFileNotExists(os.path.join("debian/.ctest/Testing/TAG"))

    def test_test_experimental(self):
        with PushEnvironmentVariable("DEB_CTEST_OPTIONS",
                                     "model=Experimental"):
            self.dh.start([])
            self.dh.configure([])
            self.dh.build([])
            self.dh.test([])
            date = self.get_testing_tag_date()

            with open(os.path.join("debian/.ctest/Testing", date, "Test.xml"),
                      "r") as f:
                tree = xml.etree.ElementTree.fromstring(f.read())

            tests = tree.findall("Testing/Test")
            self.assertEqual(1, len(tests))

            test_true = self.get_single_element(tree.findall(
                "Testing/Test[Name='TestTrue']"))
            self.assertEqual("passed", test_true.get("Status"))

            self.assertFilesSubmittedEqual({})

    def test_test_experimental_submit(self):
        with PushEnvironmentVariable("DEB_CTEST_OPTIONS",
                                     "model=Experimental submit"):
            self.dh.start([])
            self.dh.configure([])
            self.dh.build([])
            self.dh.test([])
            date = self.get_testing_tag_date()

            with open(os.path.join("debian/.ctest/Testing", date, "Test.xml"),
                      "r") as f:
                tree = xml.etree.ElementTree.fromstring(f.read())

            tests = tree.findall("Testing/Test")
            self.assertEqual(1, len(tests))

            test_true = self.get_single_element(tree.findall(
                "Testing/Test[Name='TestTrue']"))
            self.assertEqual("passed", test_true.get("Status"))

            self.assertFilesSubmittedEqual({"Configure", "Build", "Test"})

    def test_test_experimental_no_submit(self):
        with PushEnvironmentVariable("DEB_CTEST_OPTIONS",
                                     "model=Experimental submit"):
            self.dh.start([])
            self.dh.configure([])
            self.dh.build([])
            self.dh.test(["-O--no-submit"])
            date = self.get_testing_tag_date()

            with open(os.path.join("debian/.ctest/Testing", date, "Test.xml"),
                      "r") as f:
                tree = xml.etree.ElementTree.fromstring(f.read())

            tests = tree.findall("Testing/Test")
            self.assertEqual(1, len(tests))

            test_true = self.get_single_element(tree.findall(
                "Testing/Test[Name='TestTrue']"))
            self.assertEqual("passed", test_true.get("Status"))

            self.assertFilesSubmittedEqual({"Configure", "Build"})

    def test_test_experimental_bad(self):
        with PushEnvironmentVariable("DEB_CTEST_OPTIONS",
                                     "model=Experimental"):
            self.dh.start([])
            self.dh.configure([
                "--", "-DDH_CMAKE_ENABLE_BAD_TEST:BOOL=ON"])
            self.dh.build([])
            self.dh.test([])
            date = self.get_testing_tag_date()

            with open(os.path.join("debian/.ctest/Testing", date, "Test.xml"),
                      "r") as f:
                tree = xml.etree.ElementTree.fromstring(f.read())

            tests = tree.findall("Testing/Test")
            self.assertEqual(2, len(tests))

            test_true = self.get_single_element(tree.findall(
                "Testing/Test[Name='TestTrue']"))
            self.assertEqual("passed", test_true.get("Status"))

            test_false = self.get_single_element(tree.findall(
                "Testing/Test[Name='TestFalse']"))
            self.assertEqual("failed", test_false.get("Status"))

            self.assertFilesSubmittedEqual({})

    def test_test_experimental_bad_submit(self):
        with PushEnvironmentVariable("DEB_CTEST_OPTIONS",
                                     "model=Experimental submit"):
            self.dh.start([])
            self.dh.configure([
                "--", "-DDH_CMAKE_ENABLE_BAD_TEST:BOOL=ON"])
            self.dh.build([])
            self.dh.test([])
            date = self.get_testing_tag_date()

            with open(os.path.join("debian/.ctest/Testing", date, "Test.xml"),
                      "r") as f:
                tree = xml.etree.ElementTree.fromstring(f.read())

            tests = tree.findall("Testing/Test")
            self.assertEqual(2, len(tests))

            test_true = self.get_single_element(tree.findall(
                "Testing/Test[Name='TestTrue']"))
            self.assertEqual("passed", test_true.get("Status"))

            test_false = self.get_single_element(tree.findall(
                "Testing/Test[Name='TestFalse']"))
            self.assertEqual("failed", test_false.get("Status"))

            self.assertFilesSubmittedEqual({"Configure", "Build", "Test"})

    def test_submit_none(self):
        self.dh.start([])
        self.dh.configure(["-O--no-submit"])
        self.dh.build(["-O--no-submit"])
        self.dh.test(["-O--no-submit"])
        self.dh.submit([])

        self.assertFilesSubmittedEqual(set())

    def test_submit_experimental_nosubmit(self):
        with PushEnvironmentVariable("DEB_CTEST_OPTIONS",
                                     "model=Experimental"):
            self.dh.start([])
            self.dh.configure(["-O--no-submit"])
            self.dh.build(["-O--no-submit"])
            self.dh.test(["-O--no-submit"])
            self.dh.submit([])

            self.assertFilesSubmittedEqual(set())

    def test_submit_experimental_submit(self):
        with PushEnvironmentVariable("DEB_CTEST_OPTIONS",
                                     "model=Experimental submit"):
            self.dh.start([])
            self.dh.configure(["-O--no-submit"])
            self.dh.build(["-O--no-submit"])
            self.dh.test(["-O--no-submit"])
            self.dh.submit([])

            self.assertFilesSubmittedEqual({"Configure", "Build", "Test", "Done"})

    def test_submit_experimental_submit_parts(self):
        with PushEnvironmentVariable("DEB_CTEST_OPTIONS",
                                     "model=Experimental submit"):
            self.dh.start([])
            self.dh.configure(["-O--no-submit"])
            self.dh.build(["-O--no-submit"])
            self.dh.test(["-O--no-submit"])
            self.dh.submit(["--parts", "Configure", "Build"])

            self.assertFilesSubmittedEqual({"Configure", "Build"})

    def test_run_debian_rules_none(self):
        self.run_debian_rules("build", "ctest")

        self.assertFileNotExists("debian/.ctest/Testing/TAG")
        self.assertFileExists("debian/build/CMakeCache.txt")
        self.assertFilesSubmittedEqual(set())

    def test_run_debian_rules_experimental(self):
        with PushEnvironmentVariable("DEB_CTEST_OPTIONS",
                                     "model=Experimental"):
            self.run_debian_rules("build", "ctest")

            self.assertFileExists("debian/.ctest/Testing/TAG")
            self.assertFileExists("debian/build/CMakeCache.txt")
            self.assertFilesSubmittedEqual(set())

    def test_run_debian_rules_experimental_submit(self):
        with PushEnvironmentVariable("DEB_CTEST_OPTIONS",
                                     "model=Experimental submit"):
            self.run_debian_rules("build", "ctest")

            self.assertFileExists("debian/.ctest/Testing/TAG")
            self.assertFileExists("debian/build/CMakeCache.txt")
            self.assertFilesSubmittedEqual({"Configure", "Build", "Test"})
