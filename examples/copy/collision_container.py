#!/usr/bin/env python3
# Copyright (C) 2025 Vrije Universiteit Brussel. All rights reserved.
# SPDX-License-Identifier: MIT

"""
Pythainer example: COPY with PartialDockerBuilder and explicit build contexts.

This example shows how Pythainer handles Docker COPY instructions when multiple
host files share the same filename, and why an explicit build context root is
sometimes required.

Key ideas
---------
- PartialDockerBuilder records Dockerfile fragments (such as COPY instructions)
  independently of a full image build.
- Docker COPY operates relative to a single build context.
- If two source files have the same basename and no context root is specified,
  the mapping becomes ambiguous and is rejected.
- Providing a context_root makes the mapping explicit and safe.

What this example does
----------------------
1. Creates a base image builder using get_user_builder.
2. Creates a directory inside the container image.
3. Creates two host-side files with the same name but in different directories.
4. Shows that copying both files without a context_root triggers an error.
5. Shows that copying the same files with an explicit context_root succeeds.
6. Merges the valid partial builder into the main builder.
7. Builds and runs the resulting image.

This pattern is useful when assembling Docker images from multiple reusable
fragments while keeping build contexts explicit and reproducible.

Notes:
- Without context_root, COPY sources are staged by basename only, which can
  collide when multiple host files share the same name.
- With context_root, host paths become relative to that root inside the Docker
  build context, so directory structure is preserved and collisions are avoided.
"""

from pathlib import Path

from pythainer.builders import PartialDockerBuilder
from pythainer.examples.builders import get_user_builder


def main() -> None:
    """
    Build and run an image demonstrating COPY semantics with PartialDockerBuilder.

    The script creates two host files with identical names in different
    directories and demonstrates how Pythainer enforces explicit context roots
    to avoid ambiguous Docker COPY behavior.

    Raises:
        AssertionError: If the expected COPY ambiguity error is not raised.
    """
    # Create a base image builder with a user and common packages.
    # pylint: disable=duplicate-code
    builder = get_user_builder(
        image_name="pythnrcopy",
        base_ubuntu_image="ubuntu:24.04",
        user_name="jeffry",
        packages=["python3", "python3-pip", "python3-venv", "python3-dev", "zsh"],
    )

    # Directory inside the container image.
    docker_dir = Path("/home/${USER_NAME}/workspace/test")
    builder.run(f"mkdir {docker_dir}")

    # ------------------------------------------------------------------
    # Host-side setup: two files with the same name in different folders.
    # ------------------------------------------------------------------
    host_dir = Path("/tmp/pythainer/test/")
    host_dir_nested = host_dir / "nested"

    host_dir.mkdir(parents=True, exist_ok=True)
    host_dir_nested.mkdir(parents=True, exist_ok=True)

    host_path1 = host_dir / "file.txt"
    host_path2 = host_dir_nested / "file.txt"

    host_path1.write_text("file1\n")
    host_path2.write_text("file2\n")

    # ------------------------------------------------------------------
    # Case 1: No context_root -> ambiguous COPY -> error expected.
    # ------------------------------------------------------------------
    partial_builder1 = PartialDockerBuilder()

    partial_builder1.copy(
        source=host_path1,
        destination=docker_dir / "file1.txt",
        chown="${USER_NAME}:${USER_NAME}",
    )

    expected = False
    try:
        # Reusing the same basename without a context root is ambiguous.
        partial_builder1.copy(
            source=host_path2,
            destination=docker_dir / "file1.txt",
            chown="${USER_NAME}:${USER_NAME}",
        )
    except ValueError:
        expected = True  # Ambiguity correctly detected.

    assert expected, "Expected COPY ambiguity error was not raised"

    # ------------------------------------------------------------------
    # Case 2: Explicit context_root -> unambiguous COPY -> success.
    # ------------------------------------------------------------------
    partial_builder2 = PartialDockerBuilder(context_root=host_dir)

    partial_builder2.copy(
        source=host_path1,
        destination=docker_dir / "file1.txt",
        chown="${USER_NAME}:${USER_NAME}",
    )

    # No error here because the context root is explicit.
    partial_builder2.copy(
        source=host_path2,
        destination=docker_dir / "file2.txt",
        chown="${USER_NAME}:${USER_NAME}",
    )

    # Merge the valid partial builder into the main builder.
    builder |= partial_builder2

    # Finalize the image: set working directory, build, and run.
    builder.workdir(path=docker_dir)
    builder.build()

    runner = builder.get_runner()
    runner.run()


if __name__ == "__main__":
    main()
