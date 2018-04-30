cmake_minimum_required(VERSION 3.5)
project(dh-cmake-test C)

include(GNUInstallDirs)
include(CTest)

macro(declare_lib LIBNAME)
  add_library(${LIBNAME} SHARED "${LIBNAME}.c")
  set_target_properties(${LIBNAME} PROPERTIES
    PUBLIC_HEADER "${LIBNAME}.h"
    VERSION 1.0
    SOVERSION 1
  )
  install(TARGETS ${LIBNAME}
    LIBRARY
      DESTINATION "${CMAKE_INSTALL_LIBDIR}"
      COMPONENT Libraries
      NAMELINK_SKIP
    PUBLIC_HEADER
      DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}"
      COMPONENT Headers
  )
  install(TARGETS ${LIBNAME}
    LIBRARY
      DESTINATION "${CMAKE_INSTALL_LIBDIR}"
      COMPONENT Namelinks
      NAMELINK_ONLY
  )
endmacro()

declare_lib(dh-cmake-test)
add_subdirectory(lib1)
add_subdirectory(lib2)

option(DH_CMAKE_TEST_FLAG "For testing -D definitions" OFF)
if(DH_CMAKE_TEST_FLAG)
  file(WRITE "${CMAKE_BINARY_DIR}/testflag.txt" "Test flag set\n")
endif()

add_test(TestTrue true)
add_test(TestFalse false)
