# Copyright (C) 2024 Antonio Paolillo. All rights reserved.
# SPDX-License-Identifier: MIT

"""
This module contains examples of installation routines using Docker for different projects,
including CLSPV and RTDE (Robot Data Exchange), using the Pythainer package.
"""

import pathlib
from typing import Dict

from pythainer.builders import DockerBuilder, PartialDockerBuilder
from pythainer.builders.utils import (
    project_cmake_build_install,
    project_deb_download_install,
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


def realsense2_lib_install_from_src(
    builder: DockerBuilder,
    workdir: str,
    commit: str = "v2.55.1",
    debug: bool = True,
    extra_cmake_options: Dict[str, str] | None = None,
) -> None:
    """
    Installs the Intel Realsense library from source using a Docker builder, including necessary
    dependencies.

    Parameters:
        builder (DockerBuilder):
            The builder instance to use for Docker commands.
        workdir (str):
            The working directory path where to clone the source repository.
        commit (str):
            The specific git commit hash to checkout for the build.
        debug (bool):
            Whether to build in Debug mode. Defaults to True.
        extra_cmake_options (Dict[str, str]):
            Additional CMake options to pass to the build process.
            Defaults to None.
    """

    builder.desc("Build & Install librealsense2 from source")
    builder.desc(
        (
            "Tutorial: "
            "https://dev.intelrealsense.com/docs/compiling-librealsense-for-linux-ubuntu-guide"
        )
    )
    builder.root()
    builder.desc("Dependencies for IntelRealSense")
    builder.add_packages(
        packages=[
            "at",
            "libusb-1.0-0-dev",
            "libeigen3-dev",
            "libfmt-dev",
            "libgl1-mesa-dev",
            "libglew-dev",
            "libglfw3-dev",
            "libglu1-mesa-dev",
            "libgtk-3-dev",
            "libssl-dev",
            "libudev-dev",
            "pkg-config",
        ]
    )
    builder.user("${USER_NAME}")
    project_git_cmake_build_install(
        builder=builder,
        workdir=workdir,
        git_url="https://github.com/IntelRealSense/librealsense.git",
        commit=commit,
        submodule_init_recursive=False,
        cmake_options={
            "FORCE_RSUSB_BACKEND": "false",
            "BUILD_EXAMPLES": "true",
            "BUILD_GRAPHICAL_EXAMPLES": "true",
            "CMAKE_BUILD_TYPE": "Debug" if debug else "Release",
        }
        | extra_cmake_options,
    )


def opencv_lib_install_from_src(
    builder: DockerBuilder,
    workdir: str,
    commit_main: str = "4.8.1",
    commit_contrib: str = "4.8.1",
    debug: bool = True,
    cleanup: bool = True,
    extra_cmake_options: Dict[str, str] = None,
) -> None:
    """
    Installs the OpenCV library from source using a Docker builder, including optional contrib
    modules.

    Parameters:
        builder (DockerBuilder):
            The builder instance to use for Docker commands.
        workdir (str):
            The working directory path where to clone the source repositories.
        commit_main (str):
            The specific git commit hash to checkout for the main OpenCV repository.
            Defaults to "4.8.1".
        commit_contrib (str):
            The specific git commit hash to checkout for the OpenCV contrib repository.
            Defaults to "4.8.1".
        debug (bool): Whether to build in Debug mode.
            Defaults to True.
        cleanup (bool): Whether to remove the contrib repository after installation.
            Defaults to True.
        extra_cmake_options (Dict[str, str]):
            Additional CMake options to pass to the build process.
            Defaults to None.
    """

    builder.desc("Build & Install OpenCV from source")
    builder.desc("https://docs.opencv.org/4.x/d7/d9f/tutorial_linux_install.html")

    contrib_dir = pathlib.Path(workdir) / "opencv_contrib/modules"

    contrib_repo_name = project_git_clone(
        builder=builder,
        workdir=workdir,
        git_url="https://github.com/opencv/opencv_contrib.git",
        commit=commit_contrib,
    )

    project_git_cmake_build_install(
        builder=builder,
        workdir=workdir,
        git_url="https://github.com/opencv/opencv.git",
        commit=commit_main,
        cmake_options={
            "OPENCV_EXTRA_MODULES_PATH": f"{contrib_dir}",
            "BUILD_opencv_legacy": "OFF",
            "WITH_CUDA": "ON",
            "CMAKE_BUILD_TYPE": "Debug" if debug else "Release",
        }
        | extra_cmake_options,
        cleanup=cleanup,
    )

    if cleanup:
        builder.run(f"rm -rf {contrib_repo_name}")


def tensor_rt_lib_install_from_deb(
    builder: DockerBuilder,
    workdir: str = "/tmp",
    os: str = "ubuntu2204",
    tag: str = "10.7.0",
    cuda_tag: str = "12.6",
):
    """
    Install TensorRT library from a .deb package into a Docker image.

    Parameters:
        builder (DockerBuilder): An instance of DockerBuilder for executing commands.
        workdir (str): Working directory inside the container where the package will be downloaded.
        os (str): Operating system identifier, used in forming the download URL.
        tag (str): Version tag of the TensorRT library, used in forming the download URL.
        cuda_tag (str): CUDA version tag, used in forming the download URL.
    """
    tensorrt_download_url = (
        f"https://developer.nvidia.com/downloads/compute/machine-learning/tensorrt/"
        f"{tag}/local_repo/nv-tensorrt-local-repo-{os}-{tag}-cuda-{cuda_tag}_1.0-1_amd64.deb"
    )
    project_deb_download_install(
        builder=builder,
        workdir=workdir,
        package_name="nv-tensorrt-repo",
        package_url=tensorrt_download_url,
        extra_commands_before_install=["rm -f /etc/apt/sources.list.d/cuda*.list"],
        extra_commands_after_install=[
            (
                f"cp "
                f"/var/nv-tensorrt-local-repo-{os}-{tag}-cuda-{cuda_tag}/*-keyring.gpg "
                "/usr/share/keyrings/"
            )
        ],
    )
    # Pin the local repository to force using the given versions.
    builder.run_multiple(
        commands=[
            'echo "Package: tensorrt libnvinfer* libnvonnxparsers* libnvinfer-*" > '
            "/etc/apt/preferences.d/99-nv-tensorrt",
            f'echo "Pin: release o=nv-tensorrt-local-repo-{os}-{tag}-cuda-{cuda_tag}" >> '
            "/etc/apt/preferences.d/99-nv-tensorrt",
            'echo "Pin-Priority: 1001" >> /etc/apt/preferences.d/99-nv-tensorrt',
        ]
    )

    builder.add_packages(packages=[f"tensorrt={tag}.23-1+cuda{cuda_tag}"])


def cudnn_lib_install_from_deb(
    builder: DockerBuilder,
    workdir: str = "/tmp",
    os: str = "ubuntu2204",
    tag: str = "8.8.0.121",
):
    """
    Install cuDNN library from a .deb package into a Docker image.

    Parameters:
        builder (DockerBuilder): An instance of DockerBuilder for executing commands.
        workdir (str): Working directory inside the container where the package will be downloaded.
        os (str): Operating system identifier, used in forming the download URL.
        tag (str): Version tag of the cuDNN library, also used in forming the download URL.
    """
    cudnn_download_url = (
        f"https://developer.download.nvidia.com/compute/redist/cudnn/v8.8.0/local_installers/12.0/"
        f"cudnn-local-repo-{os}-{tag}_1.0-1_amd64.deb"
    )
    project_deb_download_install(
        builder=builder,
        workdir=workdir,
        package_name="cudnn-local-repo",
        package_url=cudnn_download_url,
        extra_commands_after_install=[
            "cp /var/cudnn-local-repo-*/cudnn-local-*-keyring.gpg /usr/share/keyrings/"
        ],
    )

    builder.add_packages(
        packages=[
            "libcudnn8",
            "libcudnn8-dev",
            "libcudnn8-samples",
        ]
    )


def nsight_systems_install(
    builder: DockerBuilder,
    os: str = "ubuntu1804",
):
    """
    Install nsight following https://docs.nvidia.com/nsight-systems/InstallationGuide/index.html
    Currently only ubuntu1804 for all linux version

    Parameters:
        builder (DockerBuilder):
            An instance of DockerBuilder for executing commands.
        os (str):
            Operating system identifier, used in forming the download URL, currently only ubuntu1804
            for all linux version.
    """
    if os == "ubuntu1804":
        builder.run_multiple(
            commands=[
                (
                    f"apt-key adv "
                    f"--fetch-keys "
                    f"https://developer.download.nvidia.com/compute/cuda/repos/{os}/x86_64/"
                    "7fa2af80.pub"
                ),
                (
                    'add-apt-repository "deb '
                    "https://developer.download.nvidia.com/devtools/repos/"
                    'ubuntu$(. /etc/lsb-release; echo "$DISTRIB_RELEASE" | tr -d .)/'
                    '$(dpkg --print-architecture)/ /"'
                ),
            ]
        )
    else:
        raise ValueError(f"Unsupported OS: {os}. Currently, only 'ubuntu1804' is supported.")

    builder.add_packages(packages=["nsight-systems"])
