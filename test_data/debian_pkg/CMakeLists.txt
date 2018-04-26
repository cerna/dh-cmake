cmake_minimum_required(VERSION 3.5)
project(dh-cmake-test C)

include(CPack)

macro(declare_lib LIBNAME)
  add_library(${LIBNAME} SHARED "${LIBNAME}.c")
  set_property(TARGET ${LIBNAME} PROPERTY PUBLIC_HEADER "${LIBNAME}.h")
  install(TARGETS ${LIBNAME}
    LIBRARY
      DESTINATION lib
      COMPONENT ${LIBNAME}-Libraries
    PUBLIC_HEADER
      DESTINATION include
      COMPONENT ${LIBNAME}-Development
  )
endmacro()

declare_lib(dh-cmake-test)
add_subdirectory(lib1)
add_subdirectory(lib2)

cpack_add_component_group(Libraries)
cpack_add_component_group(Development)

foreach(_n dh-cmake-test dh-cmake-test-lib1 dh-cmake-test-lib2)
  cpack_add_component(${_n}-Libraries GROUP Libraries)
  cpack_add_component(${_n}-Development GROUP Development)
endforeach()
