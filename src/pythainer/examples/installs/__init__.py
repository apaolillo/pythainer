# Copyright (C) 2024 Antonio Paolillo. All rights reserved.
# SPDX-License-Identifier: MIT

"""
This module contains examples of installation routines using Docker for different projects,
including CLSPV and RTDE (Robot Data Exchange), using the Pythainer package.
"""

from pythainer.builders import DockerBuilder, PartialDockerBuilder
from pythainer.builders.utils import (
    project_cmake_build_install,
    project_git_clone,
    project_git_cmake_build_install,
)


def clspv_build_install(
    builder: PartialDockerBuilder,
    workdir: str,
    commit: str,
    cleanup: bool = True,
) -> None:
    """
    Builds and installs CLSPV from source using the specified Docker builder.

    Parameters:
        builder (PartialDockerBuilder): The builder instance to use for Docker commands.
        workdir (str): The working directory path where to clone the source repository.
        commit (str): The specific git commit hash to checkout for the build.
        cleanup (bool): Whether to clean up the build artifacts after installation.
                        Defaults to True.
    """

    builder.desc("Build & Install Clspv from source")
    builder.desc("https://github.com/google/clspv.git")

    repo_name = project_git_clone(
        builder=builder,
        workdir=workdir,
        git_url="https://github.com/google/clspv.git",
        commit=commit,
    )
    builder.run(command="python3 utils/fetch_sources.py")

    builder.user()
    project_cmake_build_install(
        builder=builder,
        workdir=workdir,
        repo_name=repo_name,
        generator="Ninja",
        cmake_options={
            "CMAKE_BUILD_TYPE": "RelWithDebInfo",
        },
        install=True,
        cleanup=cleanup,
    )

    builder.space()


def rtde_lib_install_from_src(
    builder: DockerBuilder,
    workdir: str,
    rtde_commit: str = "a9586d09145aa4e012246236976dc79ecc7233d5",
    debug: bool = True,
) -> None:
    """
    Installs the RTDE library from source using a Docker builder, including necessary dependencies.

    Parameters:
        builder (DockerBuilder): The builder instance to use for Docker commands.
        workdir (str): The working directory path where to clone the source repository.
        rtde_commit (str): The specific git commit hash to checkout for the build.
        debug (bool): Whether to build in Debug mode. Defaults to True.
    """

    builder.desc("Boost (dependency of RTDE)")
    builder.root()
    builder.add_packages(
        packages=[
            "libboost-all-dev",
        ]
    )
    builder.user("${USER_NAME}")
    builder.space()

    # The following installs the ppa of RTDE provided by the developers,
    # but commented-out as we're compiling from sources instead (see below).
    # docker_builder.run(command="add-apt-repository ppa:sdurobotics/ur-rtde")
    # docker_builder.add_packages(packages=["librtde", "librtde-dev"])

    builder.desc("Build & install UR RTDE from source")
    project_git_cmake_build_install(
        builder=builder,
        workdir=workdir,
        git_url="https://gitlab.com/sdurobotics/ur_rtde.git",
        commit=rtde_commit,
        patch_commands=[
            # Remove remote control check when launching RTDE on URSIM
            (
                r'sed -i "s/'
                r"hostname_ != \"192.168.56.101\""
                r"/"
                r"hostname_ != \"192.168.56.101\" \&\& hostname_ != \"172.17.0.2\""
                r'/" '
                r"src/rtde_control_interface.cpp"
            ),
        ],
        submodule_init_recursive=True,
        cmake_options={
            "CMAKE_BUILD_TYPE": "Debug" if debug else "Release",
        },
        cleanup=False,
    )
