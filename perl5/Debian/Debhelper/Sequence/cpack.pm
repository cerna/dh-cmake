# This file is part of dh-cmake.
# See top-level LICENSE file for license information.

use warnings;
use strict;
use Debian::Debhelper::Dh_Lib;

insert_after("dh_auto_install", "dh_cpack");

1;
