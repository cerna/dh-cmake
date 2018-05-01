%:
	dh $@ --buildsystem=cmake --builddir=$(CURDIR)/debian/build --with ctest

override_dh_ctest_configure:
	dh_ctest_configure --builddir=$(CURDIR)/debian/build -- -DDH_CMAKE_ENABLE_BAD_TEST:BOOL=OFF
