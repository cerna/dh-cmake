# This file is part of dh-cmake, and is distributed under the OSI-approved
# BSD 3-Clause license. See top-level LICENSE file or
# https://gitlab.kitware.com/debian/dh-cmake/blob/master/LICENSE for details.

set(CTEST_SOURCE_DIRECTORY "${DH_CTEST_SRCDIR}")
set(CTEST_BINARY_DIRECTORY "${DH_CTEST_CTESTDIR}")

set(CTEST_CONFIGURE_COMMAND "${DH_CTEST_CONFIGURE_CMD}")
set(CTEST_BUILD_COMMAND "${DH_CTEST_BUILD_CMD}")

if(DH_CTEST_STEP STREQUAL start)
  ctest_start("${DH_CTEST_DASHBOARD_MODEL}")
elseif(DH_CTEST_STEP STREQUAL configure)
  ctest_start("${DH_CTEST_DASHBOARD_MODEL}" APPEND)
  ctest_configure(BUILD "${DH_CTEST_TOPDIR}")
elseif(DH_CTEST_STEP STREQUAL build)
  ctest_start("${DH_CTEST_DASHBOARD_MODEL}" APPEND)
  ctest_build(BUILD "${DH_CTEST_TOPDIR}")
elseif(DH_CTEST_STEP STREQUAL test)
  ctest_start("${DH_CTEST_DASHBOARD_MODEL}" APPEND)
  ctest_test(BUILD "${DH_CTEST_BUILDDIR}")
elseif(DH_CTEST_STEP STREQUAL submit)
  ctest_start("${DH_CTEST_DASHBOARD_MODEL}" APPEND)
  ctest_submit()
endif()