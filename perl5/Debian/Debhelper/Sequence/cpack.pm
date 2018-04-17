use warnings;
use strict;
use Debian::Debhelper::Dh_Lib;

insert_after("dh_auto_install", "dh_cpack_install");

1;
