# Copyright (C) 2024 Antonio Paolillo. All rights reserved.
# SPDX-License-Identifier: MIT

"""
This module provides various Docker builder configurations for setting up different development
environments using Docker, including setups for GUI applications, OpenCL, Vulkan, and specific
projects like CLSPV.
"""

from typing import List

from pythainer.builders import PartialDockerBuilder, UbuntuDockerBuilder
from pythainer.builders.utils import cmake_build_install
from pythainer.examples.installs import clspv_build_install


def get_user_builder(
    image_name: str,
    base_ubuntu_image: str,
    user_name: str = "user",
    lib_dir: str = "/home/${USER_NAME}/workspace/libraries",
    cmake_version: str = "3.27.9",
    packages: List[str] = (),
) -> UbuntuDockerBuilder:
    """
    Creates a customized Docker builder with a non-root user and general
    development tools installed.

    Parameters:
        image_name (str): Tag to assign to the Docker image that will be built
                          with the returned builder.
        base_ubuntu_image (str): Base docker base image to use.
        user_name (str): Name of the non-root user to create.
        lib_dir (str): Directory for libraries and tools.
        cmake_version (str): Version of CMake to install.
        packages (List[str]): Additional packages to install in the Docker image.

    Returns:
        UbuntuDockerBuilder: A configured Docker builder instance with a non-root user.
    """

    docker_builder = UbuntuDockerBuilder(
        tag=image_name,
        ubuntu_base_tag=base_ubuntu_image,
    )
    docker_builder.space()

    docker_builder.env(name="DEBIAN_FRONTEND", value="noninteractive")
    docker_builder.space()

    docker_builder.add_packages(
        packages=[
            "apt-utils",
        ]
    )
    docker_builder.space()

    default_packages = [
        "apt-transport-https",
        "build-essential",
        "ca-certificates",
        "curl",
        "file",
        "gdb",
        "git",
        "gnupg",
        "less",
        "libssl-dev",
        "locales",
        "locales-all",
        "lsb-release",
        "ninja-build",
        "software-properties-common",
        "sudo",
        "telnet",
        "tmux",
        "tree",
        "vim",
        "wget",
    ]

    docker_builder.desc("General packages & tools")
    docker_builder.add_packages(packages=default_packages)
    docker_builder.space()

    docker_builder.desc("Set locales")
    docker_builder.set_locales()
    docker_builder.space()

    docker_builder.desc("Set root password")
    docker_builder.run(command="echo 'root:root' | chpasswd")
    docker_builder.space()

    docker_builder.desc("Unminimize image")
    docker_builder.unminimize()
    docker_builder.space()

    additional_packages = [p for p in packages if p not in default_packages]
    if additional_packages:
        docker_builder.desc("Required packages")
        docker_builder.add_packages(packages=additional_packages)
        docker_builder.space()

    docker_builder.desc("Create a non-root user")
    docker_builder.create_user(username=user_name)
    docker_builder.space()

    docker_builder.desc("Configure user environment")
    docker_builder.user()
    docker_builder.workdir(path="/home/${USER_NAME}")
    docker_builder.run(command="touch ~/.sudo_as_admin_successful")
    docker_builder.run(command="mkdir workspace")
    docker_builder.workdir(path="/home/${USER_NAME}/workspace")
    docker_builder.space()

    docker_builder.run(command=f"mkdir -p {lib_dir}")
    docker_builder.space()

    docker_builder.desc("Build & install CMake from source")
    cmake_build_install(builder=docker_builder, version=cmake_version, workdir=lib_dir)

    return docker_builder


def get_user_gui_builder(
    image_name: str,
    base_ubuntu_image: str,
    user_name: str = "user",
    lib_dir: str = "/home/${USER_NAME}/workspace/libraries",
    cmake_version: str = "3.27.9",
    packages: List[str] = (),
) -> UbuntuDockerBuilder:
    """
    Extends the user builder to include GUI support, and specifically installs X11 apps
    for testing GUI applications.

    Parameters:
        image_name (str): Tag to assign to the Docker image that will be built
                          with the returned builder.
        base_ubuntu_image (str): Base docker base image to use.
        user_name (str): Name of the non-root user to create.
        lib_dir (str): Directory for libraries and tools.
        cmake_version (str): Version of CMake to install.
        packages (List[str]): Additional packages to install in the Docker image.

    Returns:
        UbuntuDockerBuilder: Docker builder configured for GUI support.
    """

    docker_builder = get_user_builder(
        image_name=image_name,
        base_ubuntu_image=base_ubuntu_image,
        user_name=user_name,
        lib_dir=lib_dir,
        cmake_version=cmake_version,
        packages=packages,
    )
    docker_builder.space()

    docker_builder.desc('Just to test the "xeyes" binary that uses the GUI.')
    docker_builder.user(name="root")
    docker_builder.add_packages(packages=["x11-apps"])

    return docker_builder


def opencl_builder() -> PartialDockerBuilder:
    """
    Sets up a Docker builder for OpenCL development, including the installation
    of OpenCL headers and libraries.

    Returns:
        PartialDockerBuilder: Docker builder configured for OpenCL development.
    """

    docker_builder = PartialDockerBuilder()
    docker_builder.space()

    docker_builder.desc("Required for OpenCL")
    docker_builder.user("root")
    docker_builder.add_packages(
        packages=[
            "clinfo",
            "ocl-icd-opencl-dev",
            "opencl-c-headers",
            "opencl-clhpp-headers",
            "opencl-headers",
        ]
    )

    docker_builder.run_multiple(
        commands=[
            "mkdir -p /etc/OpenCL/vendors",
            "echo libamdocl64.so > /etc/OpenCL/vendors/amdocl64.icd",
            "echo libnvidia-opencl.so.1 > /etc/OpenCL/vendors/nvidia.icd",
        ]
    )
    docker_builder.run(
        command="ln -s /usr/lib/x86_64-linux-gnu/libOpenCL.so.1 /usr/lib/libOpenCL.so"
    )
    docker_builder.env(name="NVIDIA_VISIBLE_DEVICES", value="all")
    docker_builder.env(name="NVIDIA_DRIVER_CAPABILITIES", value="compute,utility")

    return docker_builder


def vulkan_builder() -> PartialDockerBuilder:
    """
    Configures a Docker builder for Vulkan development, preparing the environment
    and installing necessary Vulkan packages.

    Returns:
        PartialDockerBuilder: A Docker builder ready for Vulkan development.
    """

    builder = PartialDockerBuilder()
    builder.space()

    xdg_runtime_dir = "/home/${USER_NAME}/.xdg-runtime-dir"
    builder.env(name="XDG_RUNTIME_DIR", value=xdg_runtime_dir)
    builder.env(name="NVIDIA_DRIVER_CAPABILITIES", value="all")
    builder.env(name="NVIDIA_VISIBLE_DEVICES", value="all")
    builder.space()

    builder.root()
    builder.add_packages(
        packages=[
            "mesa-utils",
            "vulkan-tools",
            "libvulkan-dev",
            "pciutils",
            "vulkan-validationlayers",
            "vulkan-validationlayers-dev",
        ]
    )

    builder.user()
    builder.run(command=f"mkdir -p {xdg_runtime_dir}")
    builder.space()

    return builder


def clspv_builder() -> PartialDockerBuilder:
    """
    Prepares a Docker builder specifically for building and installing CLSPV,
    a SPIR-V compiler for OpenCL kernels.

    Returns:
        PartialDockerBuilder: Configured Docker builder for CLSPV.
    """

    builder = PartialDockerBuilder()
    builder.space()
    builder.user()
    clspv_build_install(
        builder=builder,
        workdir="/home/${USER_NAME}/workspace/libraries",
        commit="3617a5d662082bf565e54e23956ee63f255ebbbd",
        cleanup=True,
    )
    return builder
