#!/usr/bin/env python3
# Copyright (C) 2025 Aaron Bogaert. All rights reserved.
# SPDX-License-Identifier: MIT

"""
Example of using the docker COPY directive.

The builder.copy takes two path arguments
The first a path to the file on the host system you want to copy
and second a path inside of the the docker image where you want these files to be copied over to.

These Paths can be absolute as well as relative.
"""

import os
from pathlib import Path

from pythainer.examples.builders import get_user_builder


def main():
    """
    Main entry point: builds and runs COPY example.
    """
    builder = get_user_builder(
        image_name="test",
        base_ubuntu_image="ubuntu:24.04",
        user_name="jeffry",
        packages=["python3", "python3-pip", "python3-venv", "python3-dev", "zsh"],
    )

    p = Path("/home/${USER_NAME}/workspace/libraries")
    builder.run("mkdir {p}")

    builder.copy(Path(os.path.dirname(__file__)) / "file_to_coppy.txt", p / "resulting_file.txt")

    builder.workdir(p)
    builder.build()
    runner = builder.get_runner()
    runner.run()


if __name__ == "__main__":
    main()
