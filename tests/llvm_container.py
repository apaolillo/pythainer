#!/usr/bin/env python3
# Copyright (C) 2025 Antonio Paolillo. All rights reserved.
# SPDX-License-Identifier: MIT

"""
MLIR-enabled LLVM Docker Builder.

This script defines functions to build a Docker image with LLVM and MLIR support,
using the `pythainer` framework. It provides:
    - A partial builder for building and installing LLVM with MLIR enabled.
    - A full Ubuntu-based builder with a non-root user and LLVM installed.
    - A helper to build and run the container with a personal runner setup.

Example usage:
- Create add.mlir file:
module {
  llvm.func @main() -> i32 {
    %a = llvm.mlir.constant(10 : i32) : i32
    %b = llvm.mlir.constant(20 : i32) : i32
    %sum = llvm.add %a, %b : i32
    llvm.return %sum : i32
  }
}
- Translate it into LLVM with `mlir-translate --mlir-to-llvmir add.mlir -o add.ll`
"""

from pythainer.builders import PartialDockerBuilder, UbuntuDockerBuilder
from pythainer.builders.utils import project_git_cmake_build_install
from pythainer.examples.builders import get_user_builder
from pythainer.examples.runners import personal_runner


def llvm_builder(work_dir: str) -> PartialDockerBuilder:
    """
    Create build steps for compiling and installing LLVM with MLIR enabled.

    Args:
        work_dir (str):
            Working directory path inside the container where LLVM will be built.

    Returns:
        PartialDockerBuilder: Builder containing steps to build and install LLVM+MLIR.
    """
    docker_builder = PartialDockerBuilder()
    docker_builder.space()

    docker_builder.desc("Build & install llvm with mlir enabled")
    project_git_cmake_build_install(
        builder=docker_builder,
        workdir=f"{work_dir}/libraries",
        git_url="https://github.com/llvm/llvm-project.git",
        commit="llvmorg-19.1.0",
        cmake_src_dir="../llvm",
        generator="Ninja",
        cmake_options={
            "LLVM_ENABLE_PROJECTS": "mlir",
            "LLVM_TARGETS_TO_BUILD": '"X86;AArch64"',
            "CMAKE_BUILD_TYPE": "Release",
            "LLVM_ENABLE_ASSERTIONS": "ON",
        },
        install=False,
        cleanup=False,
    )
    docker_builder.env(
        name="PATH",
        value="$PATH:/home/${USER_NAME}/workspace/libraries/llvm-project/build/bin",
    )

    return docker_builder


def get_builder(
    image_name: str = "mlir",
    base_image: str = "ubuntu:24.04",
) -> UbuntuDockerBuilder:
    """
    Create an Ubuntu-based Docker builder with a non-root user and LLVM+MLIR installed.

    Args:
        image_name (str, optional):
            Name/tag for the resulting Docker image.
            Defaults to "tonymlir".
        base_image (str, optional):
            Base Ubuntu image tag.
            Defaults to "ubuntu:24.04".

    Returns:
        UbuntuDockerBuilder: Fully configured Docker builder with LLVM+MLIR installed.
    """
    user_name = "tony"
    work_dir = "/home/${USER_NAME}/workspace"
    lib_dir = f"{work_dir}/libraries"

    docker_builder = get_user_builder(
        image_name=image_name,
        base_ubuntu_image=base_image,
        user_name=user_name,
        lib_dir=lib_dir,
    )

    docker_builder |= llvm_builder(work_dir=work_dir)

    docker_builder.space()
    docker_builder.workdir(path=work_dir)

    return docker_builder


def buildrun() -> None:
    """
    Build the Docker image and run it interactively with personal runner settings.

    This:
        1. Creates a builder via `get_builder()`.
        2. Builds the Docker image.
        3. Configures the runner using `personal_runner()`.
        4. Prints the run command, generates a run script, and executes it.
    """
    docker_builder = get_builder()
    docker_builder.build()
    docker_runner = docker_builder.get_runner()

    docker_runner |= personal_runner()

    cmd = docker_runner.get_command()
    print(" ".join(cmd))
    docker_runner.generate_script()

    docker_runner.run()


def main() -> None:
    """
    Main entry point: builds and runs the MLIR-enabled LLVM Docker container.
    """
    buildrun()


if __name__ == "__main__":
    main()
