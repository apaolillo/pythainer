#!/usr/bin/env python3
# Copyright (C) 2025 Antonio Paolillo. All rights reserved.
# SPDX-License-Identifier: MIT

# pylint: disable=missing-module-docstring, invalid-name

from pathlib import Path

from pythainer.builders import PartialDockerBuilder
from pythainer.examples.builders import get_user_builder
from pythainer.examples.runners import gpu_runner, gui_runner
from pythainer.runners import ConcreteDockerRunner, DockerRunner


def hello_builder() -> PartialDockerBuilder:
    """
    A minimal partial builder that adds a single RUN step.

    Returns:
        PartialDockerBuilder: Docker builder fragment adding a "hello world".
    """
    b = PartialDockerBuilder()
    b.run("echo 'hello world!'")
    return b


# This builder does not define a base image or users by itself; it only contributes
# one Dockerfile instruction. It can be **composed** into a larger image:


image = "hello-example"
builder = get_user_builder(
    image_name=image,
    base_ubuntu_image="ubuntu:24.04",
)

builder |= hello_builder()
builder.build()

# Here is a minimal "hello runner" that forwards an environment variable and
# mounts a host directory into the container:


def hello_runner() -> DockerRunner:
    """
    A minimal runner that demonstrates a custom runtime policy.

    Returns:
        DockerRunner: Runner fragment (env + volume mount).
    """
    return DockerRunner(
        environment_variables={"PYTHAINER_HELLO": "1"},
        volumes={str(Path(".").resolve()): "/workspace"},
        devices=[],
        other_options=[],
    )


# You can compose it exactly like the built-in GPU/GUI runners:

runner = ConcreteDockerRunner(image=image, name=image, workdir="/workspace")

runner |= gpu_runner()
runner |= gui_runner()
runner |= hello_runner()

runner.run()
