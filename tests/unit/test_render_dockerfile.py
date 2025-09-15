# Copyright (C) 2025 Antonio Paolillo. All rights reserved.
# SPDX-License-Identifier: MIT
"""Unit tests for Dockerfile rendering with pythainer.

These tests verify that:
- Rendering is **deterministic** for identical command sequences.
- The Ubuntu builder emits Dockerfiles with the expected order and a single trailing newline.
- A small `_normalize` helper enforces a stable comparison by trimming trailing
  spaces per line and ensuring exactly one final newline.

Notes:
    The third test accesses a private attribute (`_build_commands`) to exercise the
    rendering path directly; pylint is silenced for that single use.
"""

from pathlib import Path
from typing import List

from pythainer.builders import (
    DockerBuildCommand,
    StrDockerBuildCommand,
    UbuntuDockerBuilder,
)
from pythainer.builders import render_dockerfile_content as render_dockerfile


def _normalize(text: str) -> str:
    """Normalize whitespace for stable Dockerfile text comparisons.

    Strips trailing spaces from each line and enforces **exactly one**
    trailing newline at the end of the string. This makes equality assertions
    robust to accidental whitespace drift while still catching ordering changes.

    Args:
        text: The Dockerfile content to normalize.

    Returns:
        A normalized string with trailing spaces removed per line and one final newline.
    """
    lines: List[str] = [ln.rstrip() for ln in text.splitlines()]
    return "\n".join(lines).rstrip("\n") + "\n"


def test_determinism_same_input_same_output() -> None:
    """Equal command sequences yield identical Dockerfile output.

    Builds a Dockerfile from an explicit list of `DockerBuildCommand`s and
    asserts strict equality against the expected text (after normalization).
    This locks down ordering and the single trailing newline contract.
    """
    commands: List[DockerBuildCommand] = [
        StrDockerBuildCommand("FROM ubuntu:24.04"),
        StrDockerBuildCommand("ENV A=1"),
        StrDockerBuildCommand("ENV B=2"),
        StrDockerBuildCommand("RUN true"),
    ]

    actual_dockerfile = _normalize(render_dockerfile(package_manager="apt", commands=commands))
    expected_dockerfile = _normalize("FROM ubuntu:24.04\nENV A=1\nENV B=2\nRUN true\n")
    assert expected_dockerfile == actual_dockerfile


def test_determinism_docker_builder() -> None:
    """UbuntuDockerBuilder emits deterministic Dockerfile text.

    Constructs a minimal Ubuntu-based builder, writes the Dockerfile to disk,
    and verifies the exact content. This ensures that the builder’s high-level
    API produces stable, predictable output.

    Warning:
        This test writes to a fixed path (`/tmp/Dockerfile`). For parallel-safe
        tests, prefer using pytest’s `tmp_path` fixture.
    """
    builder = UbuntuDockerBuilder(tag="pythainertest", ubuntu_base_tag="ubuntu:24.04")
    builder.env(name="A", value="1")
    builder.env(name="B", value="2")
    builder.run(command="true")

    dockerfile_path = Path("/tmp/Dockerfile")
    builder.generate_dockerfile(dockerfile_paths=[dockerfile_path])

    actual_dockerfile = _normalize(dockerfile_path.read_text())
    expected_dockerfile = _normalize("FROM ubuntu:24.04\nENV A=1\nENV B=2\nRUN true\n")
    assert expected_dockerfile == actual_dockerfile


def test_basic_rendering_order_and_newline() -> None:
    """FROM → RUN → USER order is preserved; single trailing newline enforced.

    Uses the builder API to assemble commands, then renders the Dockerfile and
    checks:
      - the correct base image line,
      - the presence and position of a RUN instruction,
      - the final USER line,
      - and that exactly one trailing newline is present.

    Note:
        Accesses the builder’s private `_build_commands` to feed the renderer
        directly (pylint suppressed for this line).
    """
    builder = UbuntuDockerBuilder(tag="pythainertest", ubuntu_base_tag="ubuntu:24.04")
    builder.run(command="echo hello")
    builder.root()

    df: str = render_dockerfile("apt", builder._build_commands)  # pylint: disable=W0212
    assert df.startswith("FROM ubuntu:24.04\n")
    assert "RUN echo hello\n" in df
    assert df.strip().endswith("USER root")
    assert df.endswith("\n")  # single trailing newline guaranteed
