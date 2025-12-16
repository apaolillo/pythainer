# Copyright (C) 2024 Antonio Paolillo. All rights reserved.
# SPDX-License-Identifier: MIT

"""
This module provides various Docker builder configurations for setting up different development
environments using Docker, including setups for GUI applications, OpenCL, Vulkan, and specific
projects like CLSPV.
"""

from typing import List, Tuple

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


def vtune_builder(
    lib_dir: str = "/home/${USER_NAME}/workspace/libraries",
) -> PartialDockerBuilder:
    """
    Configures a Docker builder for VTune.
    Installs necessary VTune packages and prepares the environment variables.

    Returns:
        PartialDockerBuilder: A Docker builder ready to use the Intel VTune profiler.
    """

    builder = PartialDockerBuilder()
    builder.space()

    builder.desc("Required for Intel VTune")
    builder.root()
    builder.add_packages(
        packages=[
            "libnss3-dev",
            "libgdk-pixbuf2.0-dev",
            "libgtk-3-dev",
            "libxss-dev",
            "libasound2",
            "xdg-utils",
            "kmod",
        ]
    )

    builder.user()
    builder.workdir(path=lib_dir)
    builder.run_multiple(
        [
            "wget https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB",
            "sudo apt-key add GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB",
            "rm GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB",
            (
                'echo "deb https://apt.repos.intel.com/oneapi all main"'
                " | sudo tee /etc/apt/sources.list.d/oneAPI.list"
            ),
        ]
    )

    builder.root()
    builder.add_packages(packages=["intel-oneapi-vtune"])

    builder.user()

    # Add the script that sets up the env variables for VTune to the bashrc,
    # so they are present for the user.
    file_to_source = "/opt/intel/oneapi/vtune/latest/env/vars.sh"
    builder.run(command=f'echo "[ -e "{file_to_source}" ] && source {file_to_source}" >> ~/.bashrc')

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


def rust_builder(
    install_rustfmt: bool = True,
    install_clippy: bool = True,
    install_cargo_edit: bool = True,
    install_cargo_watch: bool = False,
    install_nightly: bool = False,
) -> PartialDockerBuilder:
    """
    Sets up a Docker builder for Rust development by installing Rust via rustup
    and optionally adding common development tools.

    Parameters:
        install_rustfmt (bool): Whether to install the rustfmt formatter.
        install_clippy (bool): Whether to install the clippy linter.
        install_cargo_edit (bool): Whether to install cargo-edit (adds `cargo add`, etc.).
        install_cargo_watch (bool): Whether to install cargo-watch for file change detection.
        install_nightly (bool): Whether to install the nightly version of rust or not.

    Returns:
        PartialDockerBuilder: Docker builder configured for Rust development.
    """
    builder = PartialDockerBuilder()
    builder.user()

    # Install Rust using rustup (non-interactive)
    cmd = "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y"
    if install_nightly:
        cmd += " --default-toolchain nightly"
    builder.run(cmd)

    # Set environment variable to include Rust's cargo bin directory in PATH
    builder.env(name="PATH", value="/home/${USER_NAME}/.cargo/bin:$PATH")

    # Check Rust version
    builder.run(command="cargo --version")

    # Add rustfmt if requested
    if install_rustfmt:
        builder.run(command="rustup component add rustfmt")

    # Add clippy if requested
    if install_clippy:
        builder.run(command="rustup component add clippy")

    # Install cargo-edit if requested
    if install_cargo_edit:
        builder.run(command="cargo install cargo-edit")

    # Install cargo-watch if requested
    if install_cargo_watch:
        builder.run(command="cargo install cargo-watch")

    return builder


def qemu_dependencies() -> List[str]:
    """
    Return the list of Ubuntu packages required to build QEMU from source.

    These cover build tools (make, ninja), Python/sphinx for docs, GLib/pixman
    for QEMU’s build/runtime, and optional GUI/audio backends (SDL2, GTK, ALSA, PulseAudio).

    Returns:
        List[str]: Package names to be installed prior to building QEMU.
    """
    qemu_packages = [
        "acpica-tools",
        "libglib2.0-dev",
        "libpixman-1-dev",
        "pkg-config",
        "python3",
        "python3-dev",
        "python3-pip",
        "python3-sphinx",
        "python3-sphinx-rtd-theme",
        "python3-venv",
        "sparse",
        "build-essential",
        "meson",
        "ninja-build",
        "pkg-config",
        "diffutils",
        "python3",
        "python3-venv",
        "libglib2.0-dev",
        "libusb-1.0-0-dev",
        "libncursesw5-dev",
        "libpixman-1-dev",
        "libepoxy-dev",
        "libv4l-dev",
        "libpng-dev",
        "libsdl2-dev",
        "libsdl2-image-dev",
        "libgtk-3-dev",
        "libgdk-pixbuf2.0-dev",
        "libasound2-dev",
        "libpulse-dev",
        "libx11-dev",
        "libslirp0",
    ]

    return qemu_packages


def qemu_builder(
    version: str = "10.0.2",
    targets: Tuple[str, ...] = ("aarch64-linux-user", "aarch64-softmmu", "riscv64-softmmu"),
    disables: Tuple[str, ...] = ("xen",),
    enables: Tuple[str, ...] = ("sdl", "gtk", "slirp"),
    cleanup: bool = False,
) -> PartialDockerBuilder:
    """
    Create build steps to download, compile, and install QEMU from source.

    Parameters:
        version (str):
            QEMU version to fetch from https://download.qemu.org (e.g., "10.0.2").
        targets (Iterable[str]):
            QEMU target list passed to `--target-list` during configure.
            Examples include "aarch64-linux-user", "aarch64-softmmu", "riscv64-softmmu".
        disables (Tuple[str]):
            QEMU disable list passed to `--disable-xxx` during configure.
        enables (Tuple[str]):
            QEMU enable list passed to `--enable-xxx` during configure.
        cleanup (bool):
            If True, remove the extracted source directory after installation.

    Returns:
        PartialDockerBuilder: A builder that, when composed/applied, installs QEMU in the image.
    """
    stemname = f"qemu-{version}"
    tarname = f"{stemname}.tar.xz"
    download_url = f"https://download.qemu.org/{tarname}"

    builder = PartialDockerBuilder()

    builder.root()
    builder.add_packages(packages=qemu_dependencies())
    builder.user()

    builder.run_multiple(
        commands=[
            f"wget -q {download_url}",
            f"tar -xf {tarname}",
            f"rm {tarname}",
        ]
    )

    builder.workdir(path=stemname)

    target_list = ",".join(targets)
    disables_str = " ".join(f"--disable-{d}" for d in disables)
    enables_str = " ".join(f"--enable-{e}" for e in enables)
    commands = [
        f'./configure --target-list="{target_list}" {disables_str} {enables_str}',
        "make -j$(nproc)",
        "sudo make install",
    ]

    if cleanup:
        commands.extend(
            [
                "cd ..",
                f"rm -r {stemname}",
            ]
        )

    builder.run_multiple(commands=commands)
    builder.workdir(path="..")

    return builder
