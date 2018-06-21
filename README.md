Introduction
============

`dh-cmake` is a set of Debhelper utilities for packaging CMake projects on
Debian systems. It consists of three main Debhelper sequences: `cmake`,
`ctest`, and `cpack`.

### What About `--buildsystem=cmake`?

If you've ever packaged a CMake project for Debian before, you probably know
that Debhelper includes a `--buildsystem=cmake` option to handle the configure,
build, and test steps. `dh-cmake` does not replace this option, but instead
complements it with additional CMake functionality, such as:

* Basic CMake component installation (for example, separate packages for
  `Development` and `Runtime` components)
* Integration with CTest dashboard mode to submit build and test logs to CDash
  (for continuous integration on Debian systems)
* Advanced CPack component and component group installation and dependency
  metadata (for example, if CPack component A depends on component B, this will
  be reflected in the generated Debian packages)

The Debhelper team has done an excellent job of incorporating the CMake
buildsystem into Debian, and our hope is that `dh-cmake` will make it even
easier to package CMake projects on Debian. If you package a CMake project on
Debian, you should use both the Debhelper CMake buildsystem AND `dh-cmake`.

Note: as of Debhelper 11.2, you can use CMake's Ninja generator, by declaring
`--buildsystem=cmake+ninja`. Kitware highly recommends using this option,
especially for large projects, because it will speed up build time
significantly.

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

And a `debian/control` file (minimalistic, many fields have been omitted for
brevity):

```
Source: libexample
Maintainer: Example <example@example.com>
Build-Depends: cmake (>= 3.12), dh-cmake, debhelper (>= 11)

Package: libexample
Architecture: any
Depends: ${shlibs:Depends}, ${misc:Depends}

Package: libexample-dev
Architecture: any
Depends: libexample (= ${binary:Version}), ${misc:Depends}
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

`--with ctest` adds four new commands to the Debhelper `build` sequence:

* `dh_ctest_start`
* `dh_ctest_configure`
* `dh_ctest_build`
* `dh_ctest_test`

By default, the `configure`, `build`, and `test` steps are simple wrappers
around their `dh_auto_*` counterparts, and the `start` step does nothing.
However, they recognize a new environment variable, `DEB_CTEST_OPTIONS`, which
can be used to activate CTest's dashboard mode. To activate dashboard mode, do
the following:

```bash
DEB_CTEST_OPTIONS="model=Experimental submit" dpkg-buildpackage
```

The `model` argument will set the CTest dashboard model to "Experimental". You
can also set it to "Continuous" or "Nightly". The `submit` argument tells each
`dh_ctest_*` command to submit its own results to CDash (it does not submit by
default, due to the fact that the package may be building in an environment
without internet access.)

When used without any options, the `configure`, `build`, and `test` steps each
submit their own results to CDash upon completion, but you can disable this
behavior by passing a `--no-submit` option to them. You can also submit results
explicitly with another optional command, `dh_ctest_submit`, which is not
included in `--with ctest` by default.

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
        dh_ctest_configure -- -- -DEXAMPLE_RUN_BAD_TEST:BOOL=ON
```

Now `dh_ctest_configure` will enable the bad test.

Note that there are two `--` arguments in the command above. This is because
`dh_ctest_configure` invokes `dh_auto_configure` under the hood, and everything
after the first `--` argument gets passed to `dh_auto_configure`.
`dh_auto_configure` in turn invokes CMake, which is what the second `--`
argument is for - everything after it gets passed to CMake.

Note: in the default mode, because `dh_ctest_test` simply calls `dh_auto_test`,
it will still fail if any of the tests fail. However, in dashboard mode, CTest
allows tests to fail without failing the entire build process, and
`dh_ctest_test` reflects this behavior, so that the package can still build in
development even if some of the tests fail.

### A Word About Privacy

CTest and CDash are designed to aggregate test results from many machines onto
a single dashboard, to enable developers to easily monitor the health of a
software project on a variety of different platforms. However, privacy is also
very important, and as mentioned above, `dh_ctest_*` commands will not attempt
to submit results to a CDash server unless `DEB_CTEST_OPTIONS` has both `model`
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

The `cpack` Debhelper sequence provides integration with CPack's component
system. If a CMake project is CPack aware, you can have binary packages
correspond to CPack components or component groups, with the CPack dependency
graph propagated into the output packages. The `cpack` sequence takes advantage
of the new "CPack External" generator available in CMake 3.13.

`--with cpack` adds three new commands to the Debhelper sequence:

* `dh_cpack_generate`
* `dh_cpack_substvars`
* `dh_cpack_install`

`dh_cpack_generate` does the initial generation with CPack, which generates a
JSON file containing CPack metadata for dh-cmake to use. `dh_cpack_substvars`
reads this JSON file and writes the CPack dependencies to a new substvars
variable, `${cpack:Depends}`. Finally, `dh_cpack_install` is very similar to
`dh_cmake_install` in that it installs components into a package, but it can
also install entire CPack component groups into a package instead of having to
enumerate every component in the component group. `dh_cpack_install` also has
the limitation that the component or component group must be listed in the
CMake project with `cpack_add_component()` or `cpack_add_component_group()`
respectively.

To use the `cpack` sequence, update your `debian/rules` file to look like the
following:

```makefile
%:
        dh $@ --buildsystem=cmake --with cpack --with ctest
```

Note that we have removed the `cmake` sequence here, because in our use case,
the `cpack` sequence provides a more advanced version of the same features.
However, there's no reason why you can't use `cmake` and `cpack` together if
you want to.

Now update your `CMakeLists.txt` file to look like this:

```cmake
cmake_minimum_required(VERSION 3.12)
project(example C)

include(GNUInstallDirs)
include(CPackComponent)

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
    NAMELINK_COMPONENT Namelinks
  PUBLIC_HEADER
    DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}"
    COMPONENT Headers
)

cpack_add_component(Libraries)
cpack_add_component(Namelinks GROUP Development DEPENDS Libraries)
cpack_add_component(Headers GROUP Development DEPENDS Libraries)

cpack_add_component_group(Development)

include(CPack)
```

Note that we have changed the `COMPONENT` of the `PUBLIC_HEADER` block and the
`NAMELINK_COMPONENT` of the `LIBRARY` block to be separate components, and we
have placed both of these components in the `Development` component group. This
is to demonstrate the group functionality of the `cpack` sequence. We have also
added `DEPENDS` fields to the `Namelinks` and `Headers` components so they
depend on `Libraries`.

Since we have switched to `cpack`, rename `debian/libexample.cmake-components`
to `debian/libexample.cpack-components`. This is the file that will be read by
`dh_cpack_substvars` and `dh_cpack_install`. In addition, rename
`debian/libexample-dev.cmake-components` to
`debian/libexample-dev.cpack-component-groups`. We are doing a simple rename
here because the old component name was `Development`, and the new group name
is also `Development`.

Finally, update `debian/control` to look like the following:

```
Source: libexample
Maintainer: Example <example@example.com>
Build-Depends: cmake (>= 3.13), dh-cmake, debhelper (>= 11)

Package: libexample
Architecture: any
Depends: ${shlibs:Depends}, ${misc:Depends}

Package: libexample-dev
Architecture: any
Depends: ${cpack:Depends}, ${misc:Depends}
```

Note that we have bumped the CMake version to 3.13 for the CPack External
generator, and we have also replaced the `libexample` dependency in
`libexample-dev` with `${cpack:Depends}`. This is a new field added by
`dh_cpack_substvars`, which uses the `DEPENDS` field from
`cpack_add_component()` to automatically generate this dependency. This may not
be a big deal for small projects, but for a large project with lots of output
packages, automatically using the dependency graph from CPack can be very
useful.
