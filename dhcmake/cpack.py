# This file is part of dh-cmake, and is distributed under the OSI-approved
# BSD 3-Clause license. See top-level LICENSE file or
# https://gitlab.kitware.com/debian/dh-cmake/blob/master/LICENSE for details.

import json
import os.path
import re

from dhcmake import common


class DHCPack(common.DHCommon):
    def read_cpack_metadata(self):
        with open("debian/.cpack/cpack-metadata.json", "r") as f:
            self.cpack_metadata = json.load(f)

        # Manually populate the sub-groups and components of each group
        for name, group in self.cpack_metadata["componentGroups"].items():
            group["groups"] = []
            group["components"] = []

        for name, group in self.cpack_metadata["componentGroups"].items():
            try:
                parent_group = group["parentGroup"]
            except KeyError:  # Optional field
                continue
            self.cpack_metadata["componentGroups"][parent_group]["groups"] \
                    .append(name)

        for name, component in self.cpack_metadata["components"].items():
            try:
                group = component["group"]
            except KeyError:  # Optional field
                continue
            self.cpack_metadata["componentGroups"][group]["components"] \
                    .append(name)

    def get_cpack_components(self, package):
        opened_file = self.read_package_file(package, "cpack-components")
        if opened_file:
            retval = []
            with opened_file as f:
                for l in f:
                    if not re.search("^($|#)", l):
                        group = l.rstrip()
                        if group in self.cpack_metadata["components"]:
                            retval.append(group)
                        else:
                            raise ValueError(
                                    "Invalid CPack components in %s" % package)
            return retval
        else:
            return []

    def get_cpack_component_groups(self, package):
        opened_file = self.read_package_file(package, "cpack-component-groups")
        if opened_file:
            retval = []
            with opened_file as f:
                for l in f:
                    if not re.search("^($|#)", l):
                        group = l.rstrip()
                        if group in self.cpack_metadata["componentGroups"]:
                            retval.append(group)
                        else:
                            raise ValueError(
                                    "Invalid CPack component groups in %s" %
                                        package)
            return retval
        else:
            return []

    def get_all_cpack_components_for_group(self, group, visited=None):
        if visited is None:
            visited = set()

        if group in visited:
            return set()
        visited.add(group)

        all_components = set(self.cpack_metadata["componentGroups"][group] \
                ["components"])

        for sub_group in self.cpack_metadata["componentGroups"][group] \
                ["groups"]:
            all_components.update(
                    self.get_all_cpack_components_for_group(
                        sub_group, visited))

        return all_components

    def get_all_cpack_components(self, package):
        all_components = set(self.get_cpack_components(package))

        for group in self.get_cpack_component_groups(package):
            all_components.update(
                    self.get_all_cpack_components_for_group(group))

        return all_components

    def get_package_dependencies(self, package):
        deps = set()

        for component in self.get_all_cpack_components(package):
            for component_dep in self.cpack_metadata["components"][component] \
                    ["dependencies"]:
                for other_package, _, _ in self.get_all_packages():
                    if component_dep in \
                            self.get_all_cpack_components(other_package):
                        deps.add(other_package)

        return deps

    @common.DHEntryPoint
    def generate(self, args=None):
        self.parse_args(args)

        cmd_args = [
                "cpack",
                "--config",
                os.path.join(self.get_build_directory(), "CPackConfig.cmake"),
                "-G", "Ext",
                "-D", "CPACK_PACKAGE_FILE_NAME=cpack-metadata",
                "-B", "debian/.cpack",
        ]
        self.do_cmd(cmd_args)

    @common.DHEntryPoint
    def substvars(self, args=None):
        self.parse_args(args)
        self.read_cpack_metadata()

        for package in self.get_packages():
            depends = ", ".join(dep + " (= ${binary:Version})" for dep in
                    sorted(self.get_package_dependencies(package)))
            if depends:
                self.write_substvar("cpack:Depends", depends, package)


def generate():
    dhcpack = DHCPack()
    dhcpack.generate()
