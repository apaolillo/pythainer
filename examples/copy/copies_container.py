#!/usr/bin/env python3
# Copyright (C) 2025 Vrije Universiteit Brussel. All rights reserved.
# SPDX-License-Identifier: MIT

"""
Pythainer example: COPY multiple host files into a directory.

This example demonstrates how to use `builder.copy(...)` with a list of source
paths in order to copy multiple host-side files into a single directory inside
a Docker image.

Key ideas
---------
- `builder.copy` accepts a list of Path objects as its `source` argument.
- When multiple sources are provided, the destination must be a directory
  inside the image.
- Each source file is copied using its basename into the destination directory.
- Ownership of the copied files can be set at build time using `chown`.

What this example does
----------------------
1. Creates a base image builder using get_user_builder.
2. Creates a target directory inside the container image.
3. Creates two files on the host filesystem.
4. Copies both files into the container directory in a single COPY operation.
5. Builds and runs the resulting image.

This pattern is useful when you want to stage several configuration files,
inputs, or resources into an image in a single, clear build step.
"""

from pathlib import Path

from pythainer.examples.builders import get_user_builder


def main() -> None:
    """
    Build and run an example image demonstrating multi-source COPY semantics.

    The script creates two host-side files and copies them into a single
    directory inside the container image, preserving their filenames.

    Raises:
        OSError: If the host files cannot be created.
    """
    # Create a base image builder with a user and common packages.
    # pylint: disable=duplicate-code
    builder = get_user_builder(
        image_name="pythnrcopy",
        base_ubuntu_image="ubuntu:24.04",
        user_name="jeffry",
        packages=["python3", "python3-pip", "python3-venv", "python3-dev", "zsh"],
    )

    # Directory inside the container image where files will be copied.
    docker_dir = Path("/home/${USER_NAME}/workspace/test")
    builder.run(f"mkdir {docker_dir}")

    # ------------------------------------------------------------------
    # Host-side setup: create two files in the same directory.
    # ------------------------------------------------------------------
    host_dir = Path("/tmp/pythainer/test/")
    host_dir.mkdir(parents=True, exist_ok=True)

    host_path1 = host_dir / "file1.txt"
    host_path2 = host_dir / "file2.txt"

    host_path1.write_text("file1\n")
    host_path2.write_text("file2\n")

    # ------------------------------------------------------------------
    # Copy multiple files into the container directory in one operation.
    # ------------------------------------------------------------------
    builder.copy(
        source=[host_path1, host_path2],
        destination=docker_dir,
        chown="${USER_NAME}:${USER_NAME}",
    )

    # Finalize the image: set working directory, build, and run.
    builder.workdir(path=docker_dir)
    builder.build()

    runner = builder.get_runner()
    runner.run()


if __name__ == "__main__":
    main()
