# Copyright (C) 2024 Antonio Paolillo. All rights reserved.
# SPDX-License-Identifier: MIT
"""Example workflow described in the JOSS paper."""

from pythainer.builders import DockerBuilder
from pythainer.examples.runners import gui_runner

builder = DockerBuilder(tag="pythainer-example", package_manager="apt")
builder.from_image(tag="ubuntu:24.04")
builder.root()
builder.add_packages(["git", "ca-certificates", "x11-apps"])
builder.arg(name="USER_NAME", value="tony")
builder.run(command="useradd -m -s /bin/bash ${USER_NAME}")
builder.space()
builder.user(name="${USER_NAME}")
builder.run(command="mkdir -p /home/${USER_NAME}/workspace")
builder.workdir(path="/home/${USER_NAME}/workspace")
builder.desc("Last command:")
builder.run(command='echo "ready" > READY.txt')

builder.build()  # Render the Dockerfile and build the image

runner = builder.get_runner()  # Generate a runner
runner |= gui_runner()  # Mount GUI-related resources
runner.run()  # Run the container in the current terminal
