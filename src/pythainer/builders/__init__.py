# Copyright (C) 2024 Antonio Paolillo. All rights reserved.
# SPDX-License-Identifier: MIT

"""
This module provides classes for building Docker images programmatically with customized setups,
handling commands like package installation, environment variable setting, and user management,
tailored specifically for Docker environments.
"""
import os
import tempfile
from pathlib import Path
from typing import Dict, List

from pythainer.builders.cmds import (
    AddPkgDockerBuildCommand,
    DockerBuildCommand,
    StrDockerBuildCommand,
)
from pythainer.runners import ConcreteDockerRunner
from pythainer.sysutils import (
    PathType,
    get_gid,
    get_uid,
    mkdir,
    mkdir_for_path,
    shell_out,
)


def _generate_dockerfile_content(
    package_manager: str,
    commands: List[DockerBuildCommand],
) -> str:
    """
    Generates the content of a Dockerfile from a list of Docker build commands.

    Parameters:
        package_manager (str): The package manager used in the Docker environment (e.g., 'apt',
                               'yum').
        commands (List[DockerBuildCommand]): A list of Docker build commands to be included in the
                                             Dockerfile.

    Returns:
        str: The generated Dockerfile content as a string.
    """
    joined_lines = "\n".join(
        c.get_str_for_dockerfile(pkg_manager=package_manager) for c in commands
    )
    file_content = joined_lines.strip() + "\n"
    return file_content


class PartialDockerBuilder:
    """
    A class to facilitate the building of partial Docker configurations that can be extended or
    merged.
    """

    def __init__(self) -> None:
        """
        Initializes a PartialDockerBuilder with an empty list of build commands.
        """
        self._build_commands: List[DockerBuildCommand] = []

    def __or__(self, other: "PartialDockerBuilder") -> "PartialDockerBuilder":
        """
        Merges the current builder with another PartialDockerBuilder, combining their build
        commands.

        Parameters:
            other (PartialDockerBuilder): The other builder to merge with.

        Returns:
            PartialDockerBuilder: A new builder instance with combined commands.
        """
        result_builder = PartialDockerBuilder()
        result_builder._extend(other=self)
        result_builder._extend(other=other)
        return result_builder

    def _extend(self, other: "PartialDockerBuilder") -> None:
        """
        Extends the current builder's commands with those from another builder.

        Parameters:
            other (PartialDockerBuilder): The builder whose commands are to be added.
        """
        # pylint: disable=protected-access
        self._build_commands.extend(other._build_commands)

    def space(self) -> None:
        """
        Adds a space (newline) to the Dockerfile commands.
        """
        self._build_commands.append(StrDockerBuildCommand(""))

    def desc(self, text: str) -> None:
        """
        Adds a comment description to the Dockerfile.

        Parameters:
            text (str): The comment text to add.
        """
        self._build_commands.append(StrDockerBuildCommand(f"# {text}"))

    def from_image(self, tag: str) -> None:
        """
        Sets the base image for the Dockerfile.

        Parameters:
            tag (str): The Docker image tag to use as the base.
        """
        cmd = f"FROM {tag}"
        self._build_commands.append(StrDockerBuildCommand(cmd))

    def arg(self, name: str, value: str | None = None) -> None:
        """
        Adds an ARG instruction to the Dockerfile.

        Parameters:
            name (str): The name of the argument.
            value (str, optional): The value of the argument. If None, the argument is considered
                                   unassigned.
        """
        cmd = f"ARG {name}" if value is None else f"ARG {name}={value}"
        self._build_commands.append(StrDockerBuildCommand(cmd))

    def env(self, name: str, value: str) -> None:
        """
        Sets an environment variable in the Dockerfile.

        Parameters:
            name (str): The name of the environment variable.
            value (str): The value of the environment variable.
        """
        cmd = f"ENV {name}={value}"
        self._build_commands.append(StrDockerBuildCommand(cmd))

    def run(self, command: str) -> None:
        """
        Adds a RUN instruction to the Dockerfile.

        Parameters:
            command (str): The command to run.
        """
        cmd = f"RUN {command}"
        self._build_commands.append(StrDockerBuildCommand(cmd))

    def entrypoint(self, list_command: List[str]) -> None:
        """
        Sets the ENTRYPOINT for the Docker container.

        Parameters:
            list_command (List[str]): The command list to set as the entrypoint.
        """
        head = "["
        body = ", ".join(f'"{c}"' for c in list_command)
        tail = "]"

        cmd = f"ENTRYPOINT {head}{body}{tail}"
        self._build_commands.append(StrDockerBuildCommand(cmd))

    def run_multiple(self, commands: List[str]) -> None:
        """
        Adds multiple commands to be run in a single RUN instruction in the Dockerfile.

        Parameters:
            commands (List[str]): The commands to run.
        """
        command = " && \\\n    ".join(commands)
        self.run(command=command)

    def user(self, name: str = "") -> None:
        """
        Sets the USER for subsequent commands in the Dockerfile.

        Parameters:
            name (str): The username or UID. Defaults to the environment variable USER_NAME.
        """
        if not name:
            name = "${USER_NAME}"
        cmd = f"USER {name}"
        self._build_commands.append(StrDockerBuildCommand(cmd))

    def root(self) -> None:
        """
        Sets the USER to root for subsequent commands.
        """
        self.user(name="root")

    def workdir(self, path: PathType) -> None:
        """
        Sets the working directory for subsequent commands in the Dockerfile.

        Parameters:
            path (PathType): The path to set as the working directory.
        """
        cmd = f"WORKDIR {path}"
        self._build_commands.append(StrDockerBuildCommand(cmd))

    def add_packages(self, packages: List[str]) -> None:
        """
        Adds a list of packages to install using the configured package manager.

        Parameters:
            packages (List[str]): The packages to install.
        """
        self._build_commands.append(AddPkgDockerBuildCommand(packages=packages))


class DockerBuilder(PartialDockerBuilder):
    """
    A class for (fully) building Docker images.
    Inherits from PartialDockerBuilder and allows complete Dockerfile generation and Docker image
    building.
    """

    def __init__(
        self,
        tag: str,
        package_manager: str,
        use_buildkit: bool = True,
    ) -> None:
        """
        Initializes the DockerBuilder with a tag for the image and the package manager used in the
        Docker environment.

        Parameters:
            tag (str): The tag to be used for the built Docker image.
            package_manager (str): The package manager (e.g., 'apt', 'yum') to be used within the
                                   Docker environment.
            use_buildkit (bool): Whether to use the buildkit for the Docker image build.
        """
        super().__init__()
        self._tag = tag
        self._package_manager = package_manager
        self._use_buildkit = use_buildkit

    def generate_dockerfile(self, dockerfile_paths: List[PathType]) -> None:
        """
        Generates and writes the Dockerfile to specified paths including default
        paths in the /tmp directory.

        Parameters:
            dockerfile_paths (List[PathType]): A list of paths where the Dockerfile should be saved.
        """
        dockerfile_content = _generate_dockerfile_content(
            package_manager=self._package_manager,
            commands=self._build_commands,
        )

        all_dockerfile_paths = dockerfile_paths + [
            "/tmp/Dockerfile",
            "/tmp/benchkit/docker/latest/Dockerfile",
        ]

        for dockerfile_path in all_dockerfile_paths:
            mkdir_for_path(path=dockerfile_path)
            with open(dockerfile_path, "w") as dockerfile:
                dockerfile.write(dockerfile_content)

    def get_build_environment(self) -> Dict[str, str]:
        """
        Provides the Docker build environment variables necessary for the build process.

        Returns:
            Dict[str, str]: A dictionary of environment variables for Docker build itself.
        """
        env = {"BUILDKIT_PROGRESS": "plain"} if self._use_buildkit else {"DOCKER_BUILDKIT": "0"}
        return env

    def get_build_commands(
        self,
        dockerfile_path: PathType,
        docker_build_dir: PathType,
        uid: str | None = None,
        gid: str | None = None,
    ) -> List[str]:
        """
        Constructs the docker build command using the provided Dockerfile and build directory.

        Parameters:
            dockerfile_path (PathType): The path to the Dockerfile.
            docker_build_dir (PathType): The directory where the Docker build context resides.
            uid (str): The user ID that should be passed to the Docker build context, if any.
            gid (str): The group ID that should be passed to the Docker build context, if any.

        Returns:
            List[str]: The complete Docker build command as a list of strings.
        """
        build_args = []
        if uid is not None:
            build_args.append(f"--build-arg=UID={uid}")
        if gid is not None:
            build_args.append(f"--build-arg=GID={gid}")

        command = (
            [
                "docker",
                "build",
                "--file",
                f"{dockerfile_path}",
            ]
            + build_args
            + [
                f"--tag={self._tag}",
                f"{docker_build_dir}",
            ]
        )

        return command

    def generate_build_script(
        self,
        output_path: PathType = "/tmp/benchkit/docker/latest/docker-build.sh",
    ) -> None:
        """
        Generates a shell script to execute the Docker build commands.

        Parameters:
            output_path (PathType): The path where the build script should be saved.
        """
        command = self.get_build_commands(
            dockerfile_path="Dockerfile",
            docker_build_dir=".",
            uid="$(id -u)",
            gid="$(id -g)",
        )
        command_lst = (
            [f"{command[0]} {command[1]} \\"]
            + [f"    {c} \\" for c in command[2:-1]]
            + [f"    {command[-1]}"]
        )

        env_commands = [f"export {k}={v}" for k, v in self.get_build_environment().items()]

        lines = (
            [
                "#!/bin/sh",
                "set -ex",
                "",
            ]
            + env_commands
            + [
                "",
            ]
            + command_lst
        )

        file_content = "\n".join(lines) + "\n"

        mkdir_for_path(path=output_path)
        with open(output_path, "w") as script_file:
            script_file.write(file_content)

    def build(self, dockerfile_savepath: PathType = "") -> None:
        """
        Builds the Docker image using the generated Dockerfile and specified Docker build directory.

        Parameters:
            dockerfile_savepath (PathType): Optional path to save the Dockerfile used for the build.
        """
        main_dir = Path("/tmp/benchkit/docker/")
        mkdir(main_dir)
        with tempfile.TemporaryDirectory(
            prefix="/tmp/benchkit/docker/docker-build-",
            dir=main_dir,
        ) as temp_dir:
            temp_path = Path(temp_dir)
            dockerfile_path = (temp_path / "Dockerfile").resolve()
            dockerfile_paths = [dockerfile_path] + (
                [dockerfile_savepath] if dockerfile_savepath else []
            )
            self.generate_dockerfile(dockerfile_paths=dockerfile_paths)

            command = self.get_build_commands(
                dockerfile_path=dockerfile_path,
                docker_build_dir=temp_path,
                uid=get_uid(),
                gid=get_gid(),
            )

            environment = self.get_build_environment()

            shell_out(
                command=command,
                current_dir=temp_path,
                environment=environment,
                output_is_log=True,
            )

    def get_runner(self) -> ConcreteDockerRunner:
        """
        Returns a concrete runner using the image built in the current builder.
        This runner might be immediately used.

        Returns:
            ConcreteDockerRunner: a runner using the image built in the current builder.
        """
        return ConcreteDockerRunner(
            image=self._tag,
            name=self._tag,
        )

    def __or__(
        self,
        other: "PartialDockerBuilder",
    ) -> "DockerBuilder":
        """
        Merges the current DockerBuilder with another PartialDockerBuilder to combine their
        configurations.

        Parameters:
            other (PartialDockerBuilder): Another builder to merge with.

        Returns:
            DockerBuilder: A new DockerBuilder instance with combined configurations.
        """
        result_builder = DockerBuilder(tag=self._tag, package_manager=self._package_manager)
        result_builder._extend(other=self)
        result_builder._extend(other=other)
        return result_builder


class UbuntuDockerBuilder(DockerBuilder):
    """
    A DockerBuilder subclass tailored for Ubuntu-based images, with additional methods specific to
    Ubuntu environments.
    """

    def __init__(self, tag: str, ubuntu_base_tag: str) -> None:
        """
        Initializes the UbuntuDockerBuilder with a Docker tag and the base Ubuntu image tag.

        Parameters:
            tag (str): The tag to use for the built Docker image.
            ubuntu_base_tag (str): The Ubuntu base image tag to start from.
        """
        super().__init__(tag=tag, package_manager="apt")
        self.from_image(tag=ubuntu_base_tag)

    def set_locales(self) -> None:
        """
        Sets up the locale environment variables for the Docker image.
        """
        self.env(name="LC_ALL", value="en_US.UTF-8")
        self.env(name="LANG", value="en_US.UTF-8")
        self.env(name="LANGUAGE", value="en_US.UTF-8")

    def unminimize(self) -> None:
        """
        Runs the 'unminimize' command to restore an Ubuntu image to its full version,
        undoing the 'minimize' effect.
        """
        self.run(command="yes | unminimize")

    def remove_group_if_gid_exists(self, gid: str) -> None:
        """
        Removes a system group by its GID if it exists within the Docker environment.

        Parameters:
            gid (str): The group ID to potentially remove.
        """
        self.desc(f"Remove group with gid={gid} if it already exists.")
        command = (
            f"grep :{gid}: /etc/group && \\\n"
            f"    (grep :{gid}: /etc/group | \\\n"
            f"     cut -d ':' -f 1 | \\\n"
            f"     xargs groupdel) || \\\n"
            f"    true"
        )
        self.run(command=command)

    def remove_user_if_uid_exists(
        self,
        uid: str,
        gid: str,
    ) -> None:
        """
        Removes a system user by its UID and GID if it exists within the Docker environment.

        Parameters:
            uid (str): The user ID to potentially remove.
            gid (str): The group ID associated with the user.
        """
        self.desc(f"Remove user with uid:gid={uid}:{gid} if it already exists.")
        command = (
            f"grep :{uid}:{gid}: /etc/passwd && \\\n"
            f"    (grep :{uid}:{gid}: /etc/passwd | \\\n"
            f"     cut -d ':' -f 1 | \\\n"
            f"     xargs userdel --remove) || \\\n"
            f"    true"
        )
        self.run(command=command)

    def create_user(self, username: str) -> None:
        """
        Creates a non-root user within the Docker environment with sudo privileges.

        Parameters:
            username (str): The username of the new user.
        """
        self.arg(name="USER_NAME", value=username)
        self.arg(name="UID")
        self.arg(name="GID")
        self.remove_group_if_gid_exists(gid="${GID}")
        self.remove_user_if_uid_exists(uid="${UID}", gid="${GID}")
        self.run(command="groupadd -g ${GID} ${USER_NAME}")
        self.run(
            command='adduser --disabled-password --uid $UID --gid $GID --gecos "" ${USER_NAME}'
        )
        self.run(command="adduser ${USER_NAME} sudo")
        self.run(command="echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers")
        self.run(command='echo "${USER_NAME} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/10-docker')


class DockerfileDockerBuilder(DockerBuilder):
    """
    A DockerBuilder subclass that is built not using the pythainer command but by using a given
    dockerfile. The builder will then use the given dockerfile path and the given directory to build
    the corresponding docker image in that directory.
    """

    def __init__(
        self,
        tag: str,
        dockerfile_path: PathType,
        build_dir: PathType,
        use_uid_gid: bool,
        use_buildkit: bool = True,
    ) -> None:
        super().__init__(
            tag=tag,
            package_manager="",
            use_buildkit=use_buildkit,
        )
        self._dockerfile_path = dockerfile_path
        self._build_dir = build_dir
        self._use_uid_gid = use_uid_gid

    def generate_dockerfile(self, dockerfile_paths: List[PathType]) -> None:
        raise NotImplementedError()

    def generate_build_script(
        self,
        output_path: PathType = "/tmp/benchkit/docker/latest/docker-build.sh",
    ) -> None:
        raise NotImplementedError()

    def build(self, dockerfile_savepath: PathType = "") -> None:
        if dockerfile_savepath:
            raise NotImplementedError()

        command = self.get_build_commands(
            dockerfile_path=self._dockerfile_path,
            docker_build_dir=self._build_dir,
            uid=get_uid() if self._use_uid_gid else None,
            gid=get_gid() if self._use_uid_gid else None,
        )

        environment = self.get_build_environment() | {
            "PATH": os.environ["PATH"]
        }  # to avoid git warning in docker

        shell_out(
            command=command,
            current_dir=self._build_dir,
            environment=environment,
            output_is_log=True,
        )

    def __or__(
        self,
        other: "PartialDockerBuilder",
    ) -> "DockerBuilder":
        raise NotImplementedError()
