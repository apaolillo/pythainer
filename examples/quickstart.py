#!/usr/bin/env python3
# Copyright (C) 2025 Antonio Paolillo. All rights reserved.
# SPDX-License-Identifier: MIT

# pylint: disable=missing-module-docstring, invalid-name

from pythainer.examples.builders import get_user_builder
from pythainer.runners import ConcreteDockerRunner

image = "pythainer-quickstart"
builder = get_user_builder(image_name=image, base_ubuntu_image="ubuntu:24.04")
builder.root()
builder.add_packages(["vim", "git", "tmux"])
builder.user("${USER_NAME}")  # switch back to non-root
builder.workdir(path="/home/${USER_NAME}/workspace")
builder.build()

runner = ConcreteDockerRunner(image=image, name="pythainer-quickstart")
runner.run()
