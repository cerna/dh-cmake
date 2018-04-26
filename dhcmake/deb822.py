# This file is part of dh-cmake.
# See top-level LICENSE file for license information.

import debian.deb822


def read_control(sequence, *args, **kwargs):
    iterator = debian.deb822.Deb822.iter_paragraphs(sequence, *args, **kwargs)
    source = ControlSource(next(iterator).dump())
    packages = [ControlPackage(p.dump()) for p in iterator]

    return source, packages


class ControlSource(debian.deb822.Deb822):
    pass


class ControlPackage(debian.deb822.Deb822):
    pass
