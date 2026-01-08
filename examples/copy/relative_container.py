#!/usr/bin/env python3
# Copyright (C) 2025 Vrije Universiteit Brussel. All rights reserved.
# SPDX-License-Identifier: MIT

"""
Pythainer example: COPY a host file into a Docker image.

This script demonstrates how to use Pythainer's `builder.copy(...)` primitive to
copy a file from the *host* filesystem into the *container image* filesystem at
build time.

What this example does
----------------------
1. Creates a Docker image based on Ubuntu 24.04 with a few packages installed.
2. Creates a directory inside the image.
3. Copies a local file (`./file_to_copy.txt`) from the host into the image.
4. Sets the working directory inside the image.
5. Builds the image and runs it.

Prerequisites
-------------
- You must run this script from a directory that contains `file_to_copy.txt`.
- You must have Pythainer installed and configured to build Docker images.

Notes
-----
- `builder.copy(...)` maps to Docker's `COPY` semantics (build-time copy), not a
  runtime bind mount.
- The destination path is inside the image filesystem.
- The `chown` argument is passed through to Docker so the copied file has the
  right owner inside the container.
"""

from pathlib import Path

from pythainer.examples.builders import get_user_builder


def main() -> None:
    """
    Build and run an example image that uses Docker COPY via Pythainer.

    The script expects a file named `file_to_copy.txt` in the current working
    directory. It copies that file into `/home/${USER_NAME}/workspace/test/`
    inside the image as `file2.txt`, then builds and runs the resulting image.

    Raises:
        AssertionError: If `./file_to_copy.txt` does not exist or is not a file.
    """
    # Create a builder pre-configured with a base image, a user, and packages.
    # pylint: disable=duplicate-code
    builder = get_user_builder(
        image_name="pythnrcopy",
        base_ubuntu_image="ubuntu:24.04",
        user_name="jeffry",
        packages=["python3", "python3-pip", "python3-venv", "python3-dev", "zsh"],
    )

    # Path inside the image. `${USER_NAME}` is substituted by Pythainer at build time.
    docker_dir = Path("/home/${USER_NAME}/workspace/test")

    # Create the directory in the image filesystem.
    builder.run(f"mkdir {docker_dir}")

    # Path on the host machine (relative to the directory where you run this script).
    file_to_copy = Path("./file_to_copy.txt")
    assert file_to_copy.is_file(), (
        "Missing `./file_to_copy.txt` (host file). "
        "Create it or run the script from the directory that contains it."
    )

    # Copy host file into the image filesystem.
    builder.copy(
        source=file_to_copy,  # host path
        destination=docker_dir / "file.txt",  # image path
        chown="${USER_NAME}:${USER_NAME}",  # ownership inside the image
    )

    # Set the working directory for subsequent build steps and for the container entrypoint.
    builder.workdir(path=docker_dir)

    # Build the Docker image.
    builder.build()

    # Run the built image using the associated runner.
    runner = builder.get_runner()
    runner.run()


if __name__ == "__main__":
    main()
