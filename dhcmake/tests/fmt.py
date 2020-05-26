# This file is part of dh-cmake, and is distributed under the OSI-approved
# BSD 3-Clause license. See top-level LICENSE file or
# https://gitlab.kitware.com/debian/dh-cmake/blob/master/LICENSE for details.

import autopep8
import os.path
from unittest import TestCase


class AutoPEP8TestCase(TestCase):
    def test_autopep8(self):
        test_dir = os.path.dirname(__file__)
        root_dir = os.path.dirname(os.path.dirname(test_dir))

        for dirpath, _, filenames in os.walk(root_dir):
            for filename in filter(lambda f: f.endswith(".py"), filenames):
                with open(os.path.join(dirpath, filename)) as f:
                    contents = f.read()
                self.assertEqual(autopep8.fix_code(contents), contents,
                                 msg="File %s is incorrectly formatted" %
                                 os.path.join(os.path.relpath(dirpath, root_dir), filename))
