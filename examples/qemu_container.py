#!/usr/bin/env python3
# Copyright (C) 2025 Antonio Paolillo. All rights reserved.
# SPDX-License-Identifier: MIT

"""
QEMU Docker Image Builder Script.

This script uses the `pythainer` framework to build a Docker image containing
a specified version of QEMU installed from source. It creates a development
environment with a custom non-root user, installs necessary dependencies, and
builds QEMU in the container.

Example:
    $ python3 build_qemu_image.py

Main Steps:
    1. Create a base Ubuntu image with required dependencies.
    2. Add a non-root user and configure the workspace.
    3. Download, build, and install QEMU from source.
    4. Build the Docker image and optionally run it.
"""

from pythainer.builders import UbuntuDockerBuilder
from pythainer.examples.builders import (
    get_user_builder,
    qemu_builder,
    qemu_dependencies,
)


def get_qemu_builder(
    image_name: str,
    user_name: str,
    work_dir: str,
    base_ubuntu_image: str = "ubuntu:24.04",
    qemu_version: str = "10.0.2",
) -> UbuntuDockerBuilder:
    """
    Create a Docker builder for a QEMU installation.

    Args:
        image_name (str):
            Name of the Docker image to create.
        user_name (str):
            Username to create inside the container.
        work_dir (str):
            Path to the working directory inside the container.
        base_ubuntu_image (str, optional):
            Base Ubuntu image to use.
             Defaults to "ubuntu:24.04".
        qemu_version (str, optional):
            QEMU version to build from source.
            Defaults to "10.0.2".

    Returns:
        UbuntuDockerBuilder: Configured builder instance ready to build the image.
    """
    qemu_packages = qemu_dependencies()

    builder = get_user_builder(
        image_name=image_name,
        base_ubuntu_image=base_ubuntu_image,
        user_name=user_name,
        lib_dir=f"{work_dir}/libraries",
        packages=qemu_packages,
    )

    builder.user()
    builder.workdir(path=work_dir)
    builder.space()

    builder.desc(f"Build & Install QEMU v{qemu_version} from source")
    builder |= qemu_builder(version=qemu_version, cleanup=False)

    builder.space()
    builder.workdir(path=work_dir)

    return builder


def main():
    """
    Build and run a Docker image containing QEMU.

    Steps:
        1. Create the Docker builder using `get_qemu_builder`.
        2. Build the Docker image.
        3. Retrieve a runner for the built image.
        4. Print the Docker run command, generate a run script, and execute it.
    """
    user_name = "user"
    dock_work_dir = f"/home/{user_name}/workspace"

    builder = get_qemu_builder(
        image_name="qemuer",
        user_name="user",
        work_dir=dock_work_dir,
    )
    builder.build()

    runner = builder.get_runner()

    cmd = runner.get_command()
    print(" ".join(cmd))
    runner.generate_script()

    runner.run()


if __name__ == "__main__":
    main()
