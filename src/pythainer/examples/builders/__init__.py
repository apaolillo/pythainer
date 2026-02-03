# Copyright (C) 2024 Antonio Paolillo. All rights reserved.
# SPDX-License-Identifier: MIT

"""
This module provides various Docker builder configurations for setting up different development
environments using Docker, including setups for GUI applications, OpenCL, Vulkan, and specific
projects like CLSPV.
"""

from typing import List, Tuple

from pythainer.builders import PartialDockerBuilder, UbuntuDockerBuilder
from pythainer.builders.utils import cmake_build_install, project_git_clone
from pythainer.examples.installs import clspv_build_install


def configure_ubuntu_user(
    builder: UbuntuDockerBuilder,
    user_name: str,
    lib_dir: str,
    default_packages: list[str],
    additional_packages: list[str],
    unminimize: bool,
) -> None:
    """
    Configure a standard Ubuntu user environment inside a Docker image.

    This helper applies a common sequence of steps on an existing
    ``UbuntuDockerBuilder`` to:
    - install base and optional packages,
    - configure locales,
    - ensure the image is unminimized when requested,
    - create a non-root user,
    - set up a default workspace layout,
    - and prepare a directory for user-installed libraries/tools.

    It is intended to factor out repeated user-setup logic shared across
    multiple image recipes.

    Parameters:
        builder (UbuntuDockerBuilder):
            An initialized Docker builder targeting an Ubuntu-based image.
            The builder is mutated in-place.
        user_name (str):
            Name of the non-root user to create and configure.
        lib_dir (str):
            Path to the directory where libraries and tools should be installed
            (e.g., under the user's workspace).
        default_packages (list[str]):
            Base set of Ubuntu packages to install early in the image setup.
        additional_packages (list[str]):
            Optional extra packages required by specific recipes. If empty,
            no additional installation step is performed.
        unminimize (bool):
            Whether the base image is unminimized. If True, the image is
            unminimized to restore standard Ubuntu tooling and documentation.

    Returns:
        None
    """

    builder.desc("General packages & tools")
    builder.add_packages(packages=default_packages)
    builder.space()

    builder.desc("Set locales")
    builder.set_locales()
    builder.space()

    builder.desc("Set root password")
    builder.run(command="echo 'root:root' | chpasswd")
    builder.space()

    if unminimize:
        builder.desc("Unminimize image")
        builder.unminimize()
        builder.space()
    else:
        builder.run_multiple(
            commands=[
                "locale-gen en_US.UTF-8",
                "update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8",
            ]
        )

    if additional_packages:
        builder.desc("Required packages")
        builder.add_packages(packages=additional_packages)
        builder.space()

    builder.desc("Create a non-root user")
    builder.create_user(username=user_name)
    builder.space()

    builder.desc("Configure user environment")
    builder.user()
    builder.workdir(path="/home/${USER_NAME}")
    builder.run(command="touch ~/.sudo_as_admin_successful")
    builder.run(command="mkdir workspace")
    builder.workdir(path="/home/${USER_NAME}/workspace")
    builder.space()

    builder.run(command=f"mkdir -p {lib_dir}")
    builder.space()


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

    configure_ubuntu_user(
        builder=docker_builder,
        user_name=user_name,
        lib_dir=lib_dir,
        default_packages=default_packages,
        additional_packages=packages,
        unminimize=True,
    )

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


def get_min_user_builder(
    image_name: str,
    base_ubuntu_image: str = "ubuntu:24.04",
    user_name: str = "user",
    lib_dir: str = "/home/${USER_NAME}/workspace/libraries",
    packages: list[str] = (),
) -> UbuntuDockerBuilder:
    """
    Create a minimal Ubuntu-based Docker builder with a non-root user.

    This is a lightweight variant of ``get_user_builder()`` aimed at
    small images and fast builds. It installs only a minimal set of
    development essentials (compiler toolchain, git, locales, sudo, wget,
    adduser), optionally adds extra packages, and configures a standard
    user workspace layout via ``configure_ubuntu_user()``.

    Notably, this builder does **not** unminimize the base image
    (``unminimize=False``), which keeps the resulting image smaller but
    may omit some Ubuntu tooling/docs present in unminimized images.

    Parameters:
        image_name (str):
            Tag to assign to the Docker image that will be built with the
            returned builder.
        base_ubuntu_image (str):
            Base Ubuntu image tag to use (e.g., "ubuntu:24.04").
        user_name (str):
            Name of the non-root user to create and configure.
        lib_dir (str):
            Path to the directory where libraries and tools should be installed
            (typically under the user's workspace).
        packages (list[str]):
            Optional additional Ubuntu packages to install on top of the minimal
            default package set.

    Returns:
        UbuntuDockerBuilder:
            A configured Ubuntu Docker builder instance with a non-root user,
            basic packages installed, locales configured, and a ready-to-use
            workspace layout.
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
        "build-essential",
        "ca-certificates",
        "git",
        "locales",
        "sudo",
        "wget",
        "adduser",
    ]

    configure_ubuntu_user(
        builder=docker_builder,
        user_name=user_name,
        lib_dir=lib_dir,
        default_packages=default_packages,
        additional_packages=packages,
        unminimize=False,
    )

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
    rust_default_version: str = "stable",
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

    if rust_default_version:
        builder.run(command=f"rustup default {rust_default_version}")

    return builder


def qemu_dependencies(
    enables: Tuple[str, ...] = (),
    disables: Tuple[str, ...] = (),
) -> List[str]:
    """
    Return the list of Ubuntu packages required to build QEMU from source.

    Core build packages are always included. Optional GUI/audio/docs packages
    are included unless their corresponding feature is in ``disables``, or
    excluded unless explicitly in ``enables``.

    Parameters:
        enables: QEMU features passed to ``--enable-*``.
        disables: QEMU features passed to ``--disable-*``.

    Returns:
        List[str]: Package names to be installed prior to building QEMU.
    """

    def _want(feature: str) -> bool:
        """Return True if a feature is not explicitly disabled."""
        if feature in disables:
            return False
        if feature in enables:
            return True
        # Default: include for backward compatibility
        return True

    packages = [
        # Core build tools
        "build-essential",
        "diffutils",
        "libglib2.0-dev",
        "libpixman-1-dev",
        "meson",
        "ninja-build",
        "pkg-config",
        "python3",
        "python3-dev",
        "python3-venv",
    ]

    if _want("docs"):
        packages += [
            "python3-sphinx",
            "python3-sphinx-rtd-theme",
        ]

    if _want("sdl"):
        packages += [
            "libsdl2-dev",
            "libsdl2-image-dev",
        ]

    if _want("gtk"):
        packages += [
            "libepoxy-dev",
            "libgdk-pixbuf2.0-dev",
            "libgtk-3-dev",
            "libx11-dev",
        ]

    if _want("opengl"):
        packages += [
            "libepoxy-dev",
        ]

    if _want("slirp"):
        packages += [
            "libslirp0",
        ]

    if _want("guest-agent") or _want("tools"):
        packages += [
            "acpica-tools",
            "libusb-1.0-0-dev",
        ]

    if _want("vnc"):
        packages += [
            "libpng-dev",
        ]

    if _want("curses"):
        packages += [
            "libncursesw5-dev",
        ]

    if _want("pa"):
        packages += [
            "libpulse-dev",
            "libasound2-dev",
        ]

    if _want("alsa"):
        packages += [
            "libasound2-dev",
        ]

    # Deduplicate while preserving order
    seen: set = set()
    return [p for p in packages if not (p in seen or seen.add(p))]


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
    builder.add_packages(packages=qemu_dependencies(enables=enables, disables=disables))
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


def lime_rtw_builder(
    workdir: str,
    install: bool = False,
) -> PartialDockerBuilder:
    """
    Installs LIME RTW from source using the specified Docker builder.
    Warning: current LIME 0.2.2 do not support catching any signal in docker container!
    Parameters:
        workdir: folder path to save the lime-rtw folder
        install: True if you want to install lime-rtw
    """
    builder = PartialDockerBuilder()
    builder.user()

    builder.desc("Build & Install LIME RTW from source")
    builder.desc("https://lime.mpi-sws.org/installation/#kernel-requirements")

    builder.root()
    builder.add_packages(
        packages=[
            "libbpf-dev",
            "libelf-dev",
            "zlib1g-dev",
            "pkg-config",
            "clang",
            "protobuf-compiler",
        ]
    )
    builder.user()

    lime_rtw_name = project_git_clone(
        builder=builder,
        workdir=workdir,
        git_url="https://github.com/LiME-org/lime-rtw.git",
        commit="main",
    )

    # Build LIME RTW
    builder.run_multiple(
        commands=[
            f"cd {workdir}/{lime_rtw_name}",
            "cargo +stable build --release",
        ]
    )
    # install if needed, lime can run from executable
    if install:
        builder.run(
            command="sudo install -m 0755 target/release/lime-rtw /usr/local/bin/lime-rtw",
        )
        builder.user()

    builder.run(command="target/release/lime-rtw -V")

    return builder
