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

add_library(example SHARED example.c)
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

The `ctest` sequence integrates CTest and CDash into the Debian build process.
Projects that are CTest-aware can use `--with ctest` to run CTest in dashboard
mode during a build and submit configure, build, and test logs to the CDash
server listed in the project's `CTestConfig.cmake` file. The `ctest` sequence
is designed to bring Kitware's software process to the Debian build system.

Note: `--with ctest` is primarily for use in packages that are under
development and trying to achieve Debian policy compliance. It is designed to
monitor the health of the project when being built in a Debian environment. It
is not primarily intended for use in production packages.

`--with ctest` adds five new commands to the Debhelper `build` sequence:

* `dh_ctest_start`
* `dh_ctest_configure`
* `dh_ctest_build`
* `dh_ctest_test`
* `dh_ctest_submit`

By default, the `configure`, `build`, and `test` steps are simple wrappers
around their `dh_auto_*` counterparts, and the `start` and `submit` steps do
nothing. However, they recognize a new environment variable,
`DEB_CTEST_OPTIONS`, which can be used to activate CTest's dashboard mode.
To activate dashboard mode, do the following:

```bash
DEB_CTEST_OPTIONS="model=Experimental submit" dpkg-buildpackage
```

The `model` argument will set the CTest dashboard model to "Experimental". You
can also set it to "Continuous" or "Nightly". The `submit` argument tells the
`dh_ctest_submit` command to submit the results to CDash (it does not submit by
default, due to the fact that the package may be building in an environment
without internet access.)

Note that the steps above correspond closely to CTest's
[Dashboard Client Steps](https://cmake.org/cmake/help/latest/manual/ctest.1.html#dashboard-client-steps).
Under the hood, they call the corresponding `ctest_*()` commands.

Let's add some tests to our `CMakeLists.txt` file:

```cmake
cmake_minimum_required(VERSION 3.12)
project(example C)

include(GNUInstallDirs)
include(CTest)

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
    NAMELINK_COMPONENT Development
  PUBLIC_HEADER
    DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}"
    COMPONENT Development
)

add_test(TestSuccess true)

option(EXAMPLE_RUN_BAD_TEST OFF)
if(EXAMPLE_RUN_BAD_TEST)
  add_test(TestFailure false)
endif()
```

And add a `CTestConfig.cmake` file:

```cmake
set(CTEST_PROJECT_NAME "example")
set(CTEST_NIGHTLY_START_TIME "01:00:00 UTC")

set(CTEST_DROP_METHOD "http")
set(CTEST_DROP_SITE "cdash.example.com")
set(CTEST_DROP_LOCATION "/submit.php?project=example")
set(CTEST_DROP_SITE_CDASH TRUE)
```

And finally update our `debian/rules` file:

```makefile
%:
        dh $@ --buildsystem=cmake --with cmake --with ctest
```

Now the project is CTest-aware, and you can build the Debian package and run
the test suite at the same time.

Note: if you are running the build in an isolated environment, and you want to
submit the test results to CDash, you will need to make sure that internet
access is enabled in the build environment.

Because the CTest commands are wrappers around their `dh_auto_*` counterparts,
you can pass arguments to them the way you would to the `dh_auto_*` commands.
Notice above that we added a test, `TestFailure`, that is disabled by default
because of the `EXAMPLE_RUN_BAD_TEST` option. To activate it, change your
`debian/rules` file to look like the following:

```makefile
%:
        dh $@ --buildsystem=cmake --with cmake --with ctest

override_dh_ctest_configure:
        dh_ctest_configure -- -DEXAMPLE_RUN_BAD_TEST:BOOL=ON
```

Now `dh_ctest_configure` will enable the bad test.

Note: in the default mode, because `dh_ctest_test` simply calls `dh_auto_test`,
it will still fail if any of the tests fail. However, in dashboard mode, CTest
allows tests to fail without failing the entire build process, and
`dh_ctest_test` reflects this behavior, so that the package can still build in
development even if some of the tests fail.

### A Word About Privacy

CTest and CDash are designed to aggregate test results from many machines onto
a single dashboard, to enable developers to easily monitor the health of a
software project on a variety of different platforms. However, privacy is also
very important, and as mentioned above, `dh_ctest_submit` will not attempt to
submit results to a CDash server unless `DEB_CTEST_OPTIONS` has both `model`
AND `submit` activated. The `ctest` sequence will NEVER perform internet access
without your consent. The `dh-cmake` test suite has tests to make sure
`dh_ctest_submit` behaves properly. If `dh_ctest_submit` ever performs a rogue
submission, it is an extremely serious bug, and should be reported immediately.
You are encouraged to monitor your network traffic to ensure the security of
your network.

Additionally, `DEB_CTEST_OPTIONS` should NOT be set from inside the package
scripts, but instead be set externally by the developer or machine building the
package. Packages that enable `submit` in `DEB_CTEST_OPTIONS` from inside
`debian/rules` or another script inside the package should be regarded as
malware.

If you want to run dashboard mode without submitting results from inside the
build process, simply omit the `submit` parameter from `DEB_CTEST_OPTIONS`:

```bash
DEB_CTEST_OPTIONS="model=Experimental" dpkg-buildpackage
```

This can also be useful for submitting results without enabling internet
access inside your isolated build environment: the `dh_ctest_*` commands store
their logs in `debian/.ctest`, so you can write a CTest dashboard script that
submits these logs after the package build process has completed.

cpack
-----
TODO
