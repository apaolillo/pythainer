#!/usr/bin/env python3
# Copyright (C) 2025 Aaron Bogaert. All rights reserved.
# SPDX-License-Identifier: MIT


"""
Intel VTune Docker Builder.

Minimal working version of getting the Intel VTune profiler into the docker container.
This does not yet include the sampler as there is some gcc clash.
This means that a large part of the tools are not yet available.

To run the GUI version of the tool in the container use:
/opt/intel/oneapi/vtune/latest/bin64/vtune-gui
"""

from pythainer.examples.builders import get_user_gui_builder, vtune_builder
from pythainer.examples.runners import gui_runner
from pythainer.runners import ConcreteDockerRunner


def main():
    """
    Main entry point: builds and runs the VTune Docker container.
    """
    image_name = "pythainertest"
    builder = get_user_gui_builder(image_name=image_name, base_ubuntu_image="ubuntu:24.04")
    builder.root()
    builder.add_packages(packages=["vim", "git", "tmux"])
    builder.user("${USER_NAME}")
    builder |= vtune_builder()
    runner = ConcreteDockerRunner(image=image_name, volumes={"/usr/src/": "/usr/src/"})
    gui_run = gui_runner()
    builder.build()
    runner |= gui_run

    runner.run()


if __name__ == "__main__":
    main()
