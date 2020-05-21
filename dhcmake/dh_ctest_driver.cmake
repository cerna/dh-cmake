# This file is part of dh-cmake, and is distributed under the OSI-approved
# BSD 3-Clause license. See top-level LICENSE file or
# https://gitlab.kitware.com/debian/dh-cmake/blob/master/LICENSE for details.

set(CTEST_SOURCE_DIRECTORY "${DH_CTEST_SRCDIR}")
set(CTEST_BINARY_DIRECTORY "${DH_CTEST_CTESTDIR}")

if(DEFINED DH_CTEST_SITE)
  set(CTEST_SITE "${DH_CTEST_SITE}")
endif()

if(DEFINED DH_CTEST_BUILD)
  set(CTEST_BUILD_NAME "${DH_CTEST_BUILD}")
endif()

function(step_submit)
  if(DH_CTEST_STEP_SUBMIT)
    ctest_submit(PARTS ${ARGN})
  endif()
endfunction()

if(DH_CTEST_STEP STREQUAL start)

  set(_track_args)
  if(DEFINED DH_CTEST_TRACK)
    set(_track_args TRACK "${DH_CTEST_TRACK}")
  endif()
  ctest_start("${DH_CTEST_DASHBOARD_MODEL}" ${_track_args})

elseif(DH_CTEST_STEP STREQUAL configure)

  set(CTEST_CONFIGURE_COMMAND "${DH_CTEST_RUN_CMD}")
  ctest_start("${DH_CTEST_DASHBOARD_MODEL}" APPEND)
  ctest_configure(BUILD "${DH_CTEST_SRCDIR}")

  step_submit(Configure)

elseif(DH_CTEST_STEP STREQUAL build)

  set(CTEST_BUILD_COMMAND "${DH_CTEST_RUN_CMD}")
  ctest_start("${DH_CTEST_DASHBOARD_MODEL}" APPEND)
  ctest_build(BUILD "${DH_CTEST_SRCDIR}")

  step_submit(Build)

elseif(DH_CTEST_STEP STREQUAL test)

  ctest_start("${DH_CTEST_DASHBOARD_MODEL}" APPEND)
  ctest_test(BUILD "${DH_CTEST_BUILDDIR}")

  step_submit(Test)

elseif(DH_CTEST_STEP STREQUAL submit)

  ctest_start("${DH_CTEST_DASHBOARD_MODEL}" APPEND)

  if(DEFINED DH_CTEST_SUBMIT_PARTS)
    ctest_submit(PARTS ${DH_CTEST_SUBMIT_PARTS})
  else()
    ctest_submit()
  endif()

endif()
