#!/usr/bin/env python3
# Copyright (C) 2025 Aaron Bogaert. All rights reserved.
# SPDX-License-Identifier: MIT

"""
This example demonstrates how to copy files from the host filesystem
into a Docker image at build time using ``builder.copy(...)``.

Overview
--------
- `builder.copy()` registers one or more host-side paths to be included
  in the Docker build context.
- These paths are then copied into the image using a Dockerfile
  `COPY` instruction.
- The destination path refers to a location *inside the image*.
- Source paths may be absolute or relative on the host system.

Notes
-----
- All staging of host files into the build context is handled by the
  builder; Dockerfile instructions only reference context-relative paths.
- Ownership and permissions can be controlled using `chown` and
  `chmod` arguments, which are forwarded to the Dockerfile `COPY`
  instruction.
"""


from pathlib import Path

from pythainer.examples.builders import get_user_builder


def main():
    """
    Main entry point: builds and runs COPY example.
    """
    builder = get_user_builder(
        image_name="pythnrcopy",
        base_ubuntu_image="ubuntu:24.04",
        user_name="jeffry",
        packages=["python3", "python3-pip", "python3-venv", "python3-dev", "zsh"],
    )

    p = Path("/home/${USER_NAME}/workspace/test")
    builder.run("mkdir {p}")

    data_dir = Path(__file__).parent
    file_to_copy = data_dir / "file_to_coppy.txt"
    builder.copy(
        source=file_to_copy,
        destination=p / "resulting_file.txt",
        chown="${USER_NAME}:${USER_NAME}",
    )

    builder.workdir(p)
    builder.build()
    runner = builder.get_runner()
    runner.run()


if __name__ == "__main__":
    main()
