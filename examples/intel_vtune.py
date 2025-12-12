#!/usr/bin/env python3

from pythainer.examples.builders import get_user_gui_builder, vTune_builder
from pythainer.examples.runners import gui_runner
from pythainer.runners import ConcreteDockerRunner


def main():
    image_name = "pythainertest"
    builder = get_user_gui_builder(image_name=image_name, base_ubuntu_image="ubuntu:22.04")
    builder.root()
    builder.add_packages(packages=["vim", "git", "tmux"])
    builder.user("${USER_NAME}")
    builder |= vTune_builder()
    runner = ConcreteDockerRunner(image=image_name, volumes={"/usr/src/": "/usr/src/"})
    guiRun = gui_runner()
    builder.build()
    runner |= guiRun

    runner.run()


if __name__ == "__main__":
    main()
