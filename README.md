Introduction
============

`dh-cmake` is a set of Debhelper utilities for packaging CMake projects on
Debian systems. It consists of three main Debhelper sequences: `cmake`,
`ctest`, and `cpack`.

cmake
-----

The `cmake` Debhelper sequence provides the `dh_cmake_install` command, which
uses CMake's install components feature to put files into their proper
packages.

Let's say you have the following `CMakeLists.txt` file:

```cmake
cmake_minimum_required(VERSION 3.12)
project(example C)

include(GNUInstallDirs)

add_library(example example.c)
set_target_properties(example PROPERTIES
  PUBLIC_HEADER "example.h"
  VERSION 1.0
  SOVERSION 1
)
install(TARGETS example
  LIBRARY
    DESTINATION "${CMAKE_INSTALL_LIBDIR}"
  PUBLIC_HEADER
    DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}"
)
```

And then your `debian/rules` file will look like this:

```makefile
%:
        dh $@ --buildsystem=cmake
```

You might then have a `debian/libexample.install` file with the following:

```
usr/lib/*/*.so.*
```

and a `debian/libexample-dev.install` file with the following:

```
usr/lib/*/*.so
usr/include
```

This works, but if you have a large project that installs lots of files in
different directories, making a `*.install` file that lists all of them can be
difficult to maintain.

CMake provides a way to break an installation up into components, and
`dh_cmake_install` takes advantage of this functionality. Let's revise our
`CMakeLists.txt` file:

```cmake
cmake_minimum_required(VERSION 3.12)
project(example C)

include(GNUInstallDirs)

add_library(example example.c)
set_target_properties(example PROPERTIES
  PUBLIC_HEADER "example.h"
  VERSION 1.0
  SOVERSION 1
)
install(TARGETS example
  LIBRARY
    DESTINATION "${CMAKE_INSTALL_LIBDIR}"
    COMPONENT Libraries
    NAMELINK_COMPONENT Development
  PUBLIC_HEADER
    DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}"
    COMPONENT Development
)
```

Revised `debian/rules` file:

```makefile
%:
        dh $@ --buildsystem=cmake --with cmake
```

The `--with cmake` argument causes the `cmake` Debhelper sequence to be loaded,
which takes advantage of the `COMPONENT` arguments in the `install()` commands.
Now let's get rid of `debian/libexample.install` and replace it with a file
called `debian/libexample.cmake-components`:

```
Libraries
```

And delete `debian/libexample-dev.install` and replace it with a file called
`debian/libexample-dev.cmake-components`:

```
Development
```

Now, there's no more need to keep track of filename patterns, because the CMake
component system puts the correct files in the correct packages.

ctest
-----
TODO

cpack
-----
TODO
