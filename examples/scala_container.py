#!/usr/bin/env python3
# Copyright (C) 2025 Antonio Paolillo. All rights reserved.
# SPDX-License-Identifier: MIT

"""
SCALA Docker Image Builder Script.

This script uses the `pythainer` framework to build a Docker image containing
a specified version of SCALA installed from binaries. It creates a development
environment with a custom non-root user, installs necessary dependencies

Example:
    $ python3 scala_container.py

Main Steps:
    1. Create a base image with required dependencies.
    2. Add a non-root user and configure the workspace.
    3. Download and install Java 11
    4. Download and install Scala
    5. Build the Docker image
    6. Run the Docker image
"""

from pythainer.builders import PartialDockerBuilder, UserManager
from pythainer.examples.builders import get_user_builder


def java_builder(version: str | None, user_manager: UserManager) -> PartialDockerBuilder:
    """
    Builds a partial container to extend a base container with Java

    Parameters:
        version (str): The Java version to install
        user_manager (UserManager): The docker image user_manager

    Returns:
        PartialDockerBuilder: A partial builder to extend a docker image with Java
    """
    builder = PartialDockerBuilder()
    builder.user_manager = user_manager

    # run the commands in the context as root
    with builder.as_root() as root_builder:
        root_builder.add_packages(
            packages=[f"openjdk-{version}-jre" if version != None else "default-jre"]
        )

        version = "21" if version == None else version
        root_builder.env(name="JAVA_HOME", value=f"/usr/lib/jvm/java-{version}-openjdk-amd64")
    # go back to user before becoming root

    return builder


def scala_builder(user: str, user_manager: UserManager) -> PartialDockerBuilder:
    """
    Scala container builder

    Parameters:
        user (str): The user for whom to install Scala
        user_manager (UserManager): The docker image user_manager

    Returns:
        PartialDockerBuilder: A partial builder to extend a docker image with Java
    """

    builder = PartialDockerBuilder()
    builder.user_manager = user_manager

    with builder.as_user(username=user):
        # the java builder should be called outside but, this is a great example to show that the
        # execution will be returned to the user space after exiting the user context
        builder |= java_builder(version="11", user_manager=user_manager)

        archive_base = "cs-x86_64-pc-linux"
        archive = f"{archive_base}.gz"

        # this is dependent on the home existing
        builder.run(
            "cd ~;"
            f"curl -fL https://github.com/coursier/coursier/releases/latest/download/{archive} -o {archive};"
            f"gunzip {archive};"
            f"chmod +x {archive_base};"
            f"./{archive_base} setup -y"
        )

        builder.env(name="PATH", value=f"$PATH:/home/{user}/.local/share/coursier/bin")

    return builder


def main():
    """
    Build and run a Docker image containing Java and Scala.

    Steps:
        1. Create a base image with required dependencies.
        2. Add a non-root user and configure the workspace.
        3. Download and install Java 11
        4. Download and install Scala
        5. Build the Docker image
        6. Run the Docker image
    """
    user_name = "user"
    docker_workdir = f"/home/{user_name}/workspace"

    builder = get_user_builder(
        image_name="scala_container",
        base_ubuntu_image="ubuntu:24.04",
        user_name=user_name,
    )

    builder.workdir(path=docker_workdir)

    builder |= scala_builder(user=user_name, user_manager=builder.user_manager)

    builder.build()

    runner = builder.get_runner()

    cmd = runner.get_command()
    print(" ".join(cmd))
    runner.generate_script()

    runner.run()


if __name__ == "__main__":
    main()
