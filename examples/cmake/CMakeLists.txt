cmake_minimum_required(VERSION 3.5)
project(example C)

include(GNUInstallDirs)

add_library(example SHARED example.c)
set_target_properties(example PROPERTIES
  PUBLIC_HEADER "example.h"
  VERSION 1.0
  SOVERSION 1
)
install(TARGETS example
  LIBRARY
    DESTINATION "${CMAKE_INSTALL_LIBDIR}"
    COMPONENT Libraries
    NAMELINK_SKIP
  PUBLIC_HEADER
    DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}"
    COMPONENT Development
)
install(TARGETS example
  LIBRARY
    DESTINATION "${CMAKE_INSTALL_LIBDIR}"
    COMPONENT Development
    NAMELINK_ONLY
)
