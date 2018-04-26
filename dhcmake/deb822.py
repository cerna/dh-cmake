# This file is part of dh-cmake.
# See top-level LICENSE file for license information.

import debian.deb822


class ControlSource(debian.deb822.Deb822):
    @property
    def uploaders(self):
        return [s.strip() for s in self["uploaders"].split(",")]
