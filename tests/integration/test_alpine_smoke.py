# Copyright (C) 2025 Antonio Paolillo. All rights reserved.
# SPDX-License-Identifier: MIT
"""Integration smoke test for pythainer's DockerBuilder.

This module requires a working Docker engine. It builds a minimal Alpine-based
image and asserts that the build invocation printed by the builder includes the
expected tag flag (e.g., ``--tag=pythainer-itest:alpine``). The goal is to
verify the end-to-end wiring from high-level builder calls to the engine-facing
build command, not to validate image contents.
"""

import pytest

from pythainer.builders import DockerBuilder

pytestmark = pytest.mark.integration


def test_build_and_run_alpine_echo(capsys: pytest.CaptureFixture[str]) -> None:
    """Build a tiny Alpine image and confirm the printed build command includes the tag.

    Steps:
      1. Instantiate a ``DockerBuilder`` with a target image tag.
      2. Emit a minimal Dockerfile (``FROM alpine:3.20`` + a ``RUN echo``).
      3. Invoke ``build()`` and capture stdout.
      4. Assert that the output contains the expected ``--tag=<tag>`` fragment.

    Note:
        This checks command construction and engine invocation through stdout,
        keeping the test fast and minimally intrusive.
    """
    tag = "pythainer-itest:alpine"
    builder = DockerBuilder(tag=tag, package_manager="")
    builder.from_image(tag="alpine:3.20")
    builder.run(command="echo pythainer_ok")
    builder.build()
    out, _ = capsys.readouterr()
    assert f"--tag={tag}" in out
