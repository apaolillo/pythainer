#!/usr/bin/env python3
"""
Build and run a reproducible Ubuntu-based image using pythainer.

Steps:
1) Create the base builder.
2) Apply builder steps.
3) Build the image.
4) Configure the runner and run the container.
"""

from pythainer.builders import UbuntuDockerBuilder
from pythainer.examples.builders import get_user_gui_builder, rust_builder
from pythainer.examples.runners import gpu_runner, gui_runner
from pythainer.runners import ConcreteDockerRunner

IMAGE = "testimg"
CONTAINER = "testimg"
LIB_DIR = "/home/${USER_NAME}/workspace/libraries"


def main() -> None:
    """Build the Docker image and run it with configured capabilities."""
    builder: UbuntuDockerBuilder = get_user_gui_builder(
        image_name=IMAGE,
        base_ubuntu_image="ubuntu:24.04",
    )
    builder.space()

    builder.desc("Build rust")
    builder.workdir(path=LIB_DIR)
    builder |= rust_builder()
    builder.space()

    builder.user()
    builder.workdir(path="/home/${USER_NAME}/workspace")

    builder.build()

    runner = ConcreteDockerRunner(image=IMAGE, name=CONTAINER)
    runner |= gpu_runner()
    runner |= gui_runner()

    runner.run()


if __name__ == "__main__":
    main()
