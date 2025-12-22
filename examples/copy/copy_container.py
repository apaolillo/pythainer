#!/usr/bin/env python3
# Copyright (C) 2025 Vrije Universiteit Brussel. All rights reserved.
# SPDX-License-Identifier: MIT

"""
Pythainer example: COPY with PartialDockerBuilder and build contexts.

This example demonstrates how `PartialDockerBuilder` handles Docker COPY
instructions when multiple host files share the same basename, and how
providing an explicit build context (`context_root`) resolves ambiguities.

Key concepts illustrated
------------------------
1. **PartialDockerBuilder**:
   A lightweight builder that records Dockerfile fragments (e.g., COPY
   instructions) without immediately attaching them to a full image build.

2. **Build context ambiguity**:
   Docker COPY requires a single build context root. When two host paths with
   identical filenames but different directories are copied without an explicit
   context root, ambiguity arises.

3. **context_root**:
   By explicitly setting `context_root`, Pythainer can safely map multiple host
   files with overlapping names into the image without collisions.

What this example does
----------------------
1. Creates a base image using `get_user_builder`.
2. Creates a target directory inside the image filesystem.
3. Creates a temporary directory tree on the host with two files:
   - `/tmp/pythainer/test/file.txt`
   - `/tmp/pythainer/test/nested/file.txt`
4. Demonstrates that copying both files *without* a context root raises an error.
5. Demonstrates that copying the same files *with* a context root succeeds.
6. Merges the valid partial builder into the main builder.
7. Builds and runs the resulting image.

Why this matters
----------------
This pattern is important when:
- You want to assemble Dockerfile fragments incrementally.
- You copy many files from the host with overlapping names.
- You want explicit, reproducible control over Docker build contexts.
"""

from pathlib import Path

from pythainer.builders import PartialDockerBuilder
from pythainer.examples.builders import get_user_builder


def main() -> None:
    """
    Build and run an example image demonstrating PartialDockerBuilder COPY rules.

    The script constructs two host files with identical names in different
    directories and shows how Pythainer enforces explicit context roots to avoid
    ambiguous Docker COPY semantics.

    Raises:
        AssertionError: If the expected COPY ambiguity error is not raised.
    """
    # Base image builder with user and common packages.
    # pylint: disable=duplicate-code
    builder = get_user_builder(
        image_name="pythnrcopy",
        base_ubuntu_image="ubuntu:24.04",
        user_name="jeffry",
        packages=["python3", "python3-pip", "python3-venv", "python3-dev", "zsh"],
    )

    # Target directory inside the container image.
    docker_dir = Path("/home/${USER_NAME}/workspace/test")
    builder.run(f"mkdir {docker_dir}")

    # -------------------------------------------------------------------------
    # Host-side setup: create two files with the same name in different folders.
    # -------------------------------------------------------------------------
    host_dir = Path("/tmp/pythainer/test/")
    host_dir_nested = host_dir / "nested"

    host_dir.mkdir(parents=True, exist_ok=True)
    host_dir_nested.mkdir(parents=True, exist_ok=True)

    host_path1 = host_dir / "file.txt"
    host_path2 = host_dir_nested / "file.txt"

    host_path1.write_text("file1\n")
    host_path2.write_text("file2\n")

    # -------------------------------------------------------------------------
    # Case 1: No explicit context_root -> ambiguous COPY -> error (expected).
    # -------------------------------------------------------------------------
    partial_builder1 = PartialDockerBuilder()

    partial_builder1.copy(
        source=host_path1,
        destination=docker_dir / "file1.txt",
        chown="${USER_NAME}:${USER_NAME}",
    )

    expected = False
    try:
        # This COPY reuses the same basename ("file.txt") from another directory.
        # Without a context_root, Pythainer refuses the ambiguous mapping.
        partial_builder1.copy(
            source=host_path2,
            destination=docker_dir / "file1.txt",
            chown="${USER_NAME}:${USER_NAME}",
        )
    except ValueError:
        expected = True  # Ambiguity detected as expected.

    assert expected, "Expected COPY ambiguity error was not raised"

    # -------------------------------------------------------------------------
    # Case 2: Explicit context_root -> unambiguous COPY -> success.
    # -------------------------------------------------------------------------
    partial_builder2 = PartialDockerBuilder(context_root=host_dir)

    partial_builder2.copy(
        source=host_path1,
        destination=docker_dir / "file1.txt",
        chown="${USER_NAME}:${USER_NAME}",
    )

    # No error here: both files are now resolved relative to the same context root.
    partial_builder2.copy(
        source=host_path2,
        destination=docker_dir / "file2.txt",
        chown="${USER_NAME}:${USER_NAME}",
    )

    # Merge the valid partial builder into the main builder.
    builder |= partial_builder2

    # Finalize image: set working directory, build, and run.
    builder.workdir(path=docker_dir)
    builder.build()

    runner = builder.get_runner()
    runner.run()


if __name__ == "__main__":
    main()
