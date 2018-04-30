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


class MockCDashServer(http.server.HTTPServer):
    def __init__(self, server_address):
        super().__init__(server_address, MockCDashServerHandler)

        self.submitted_files = set()


class DHCTestTestCase(DebianSourcePackageTestCaseBase):
    def setUp(self):
        super().setUp()

        self.dhctest = ctest.DHCTest()
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
        date = self.get_testing_tag_date()
        for step in steps:
            with open(os.path.join("debian/.ctest/Testing", date,
                                   step + ".xml"), "rb") as f:
                contents = f.read()
            contents_set.add(contents)

        self.assertEqual(contents_set, self.cdash_server.submitted_files)

    def get_testing_tag_date(self):
        with open("debian/.ctest/Testing/TAG", "r") as f:
            return next(f).rstrip()

    def test_start(self):
        self.assertFileNotExists("debian/.ctest/Testing/TAG")

        self.dhctest.start([])
        with open("debian/.ctest/Testing/TAG", "r") as f:
            self.assertRegex(next(f), "^[0-9]{8}-[0-9]{4}$")
            self.assertEqual("Experimental", next(f).rstrip())
            with self.assertRaises(StopIteration):
                next(f)

    def test_configure(self):
        self.dhctest.start([])
        self.dhctest.configure([])
        date = self.get_testing_tag_date()

        self.assertFileExists(os.path.join("debian/.ctest/Testing", date,
                                           "Configure.xml"))

        self.assertFileNotExists(os.path.join("debian/.ctest/Testing", date,
                                              "Build.xml"))

        self.assertFileNotExists(
            os.path.join(self.dhctest.get_build_directory(), "testflag.txt"))

    def test_configure_args(self):
        self.dhctest.start([])
        self.dhctest.configure(["--", "-DDH_CMAKE_TEST_FLAG:BOOL=ON"])
        date = self.get_testing_tag_date()

        self.assertFileExists(os.path.join("debian/.ctest/Testing", date,
                                           "Configure.xml"))

        self.assertFileNotExists(os.path.join("debian/.ctest/Testing", date,
                                              "Build.xml"))

        self.assertFileExists(
            os.path.join(self.dhctest.get_build_directory(), "testflag.txt"))

    def test_build(self):
        self.dhctest.start([])
        self.dhctest.configure([])
        self.dhctest.build([])
        date = self.get_testing_tag_date()

        self.assertFileExists(os.path.join("debian/.ctest/Testing", date,
                                           "Build.xml"))
        self.assertFileNotExists(os.path.join("debian/.ctest/Testing", date,
                                              "Test.xml"))

    def test_test(self):
        self.dhctest.start([])
        self.dhctest.configure([])
        self.dhctest.build([])
        self.dhctest.test([])
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

    def test_submit(self):
        self.dhctest.start([])
        self.dhctest.configure([])
        self.dhctest.build([])
        self.dhctest.test([])
        self.dhctest.submit([])

        self.assertFilesSubmittedEqual({"Configure", "Build", "Test"})
