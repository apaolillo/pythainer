# Copyright (C) 2024 Antonio Paolillo. All rights reserved.
# SPDX-License-Identifier: MIT

"""
This module defines DockerRunner and ConcreteDockerRunner classes which are used to manage and run
Docker containers with specific configurations, such as environmental variables, mounted volumes,
device access, and other Docker options.
"""

from pathlib import Path
from typing import Dict, List

from pythainer.sysutils import Environment, PathType, get_gid, get_uid, shell_out


class DockerRunner:
    """
    A class to abstract the configuration of Docker containers with flexible setups through
    environment variables, volumes, devices, and other Docker-specific options.
    """

    def __init__(
        self,
        environment_variables: Environment = None,
        volumes: Dict[str, str] | None = None,
        devices: List[str] | None = None,
        other_options: List[str] | None = None,
    ) -> None:
        """
        Initializes a DockerRunner with the given configuration.

        Parameters:
            environment_variables (Environment): Environment variables to pass to the container.
            volumes (Dict[str, str]): A dictionary mapping host paths to mount to container paths.
            devices (List[str]): A list of device paths to make available inside the container.
            other_options (List[str]): Additional Docker command line options.
        """

        self._environment_variables = environment_variables if environment_variables else {}
        self._volumes = volumes if volumes else {}
        self._devices = devices if devices else []
        self._other_options = other_options if other_options else []

    def __or__(self, other: "DockerRunner") -> "DockerRunner":
        """
        Combines the configuration of this DockerRunner with another, returning a new DockerRunner
        instance with merged settings.

        Parameters:
            other (DockerRunner): Another DockerRunner instance to merge with.

        Returns:
            DockerRunner: A new DockerRunner instance with combined settings.
        """

        if not isinstance(other, DockerRunner):
            return NotImplemented
        return DockerRunner(
            environment_variables=self._environment_variables | other._environment_variables,
            volumes=self._volumes | other._volumes,
            devices=self._devices + other._devices,
            other_options=self._other_options + other._other_options,
        )

    def concretize(
        self,
        image: str,
        tty: bool,
        interactive: bool,
        name: str | None = None,
        network: str | None = None,
        workdir: PathType | None = None,
        root: bool = False,
    ) -> "ConcreteDockerRunner":
        """
        Transforms this abstract DockerRunner configuration into a ConcreteDockerRunner that is
        ready to run.

        Parameters:
            image (str): The Docker image to use for the container to run.
            tty (bool): Whether to allocate a TTY.
            interactive (bool): Whether to make the container interactive.
            name (str): Optional name for the Docker container.
            network (str): Optional Docker network mode for the container.
            workdir (PathType): Optional working directory inside the container.
            root (bool): Whether to run the container as root.

        Returns:
            ConcreteDockerRunner: A ConcreteDockerRunner instance with the specified settings.
        """
        return ConcreteDockerRunner(
            image=image,
            name=name,
            environment_variables=self._environment_variables,
            volumes=self._volumes,
            devices=self._devices,
            other_options=self._other_options,
            network=network,
            workdir=workdir,
            root=root,
            tty=tty,
            interactive=interactive,
        )


class ConcreteDockerRunner(DockerRunner):
    """
    A subclass of DockerRunner that provides specific functionality to construct and execute Docker
    run commands based on the configured settings.
    """

    def __init__(
        self,
        image: str,
        name: str | None = None,
        environment_variables: Environment = None,
        volumes: Dict[str, str] | None = None,
        devices: List[str] | None = None,
        other_options: List[str] | None = None,
        network: str | None = None,
        workdir: PathType | None = None,
        root: bool = False,
        tty: bool = True,
        interactive: bool = True,
    ) -> None:
        """
        Initializes a ConcreteDockerRunner with detailed configuration options.

        Parameters:
            image (str): The Docker image to use for the container to run.
            name (str): Optional name for the Docker container.
            environment_variables (Environment): Environment variables to pass to the container.
            volumes (Dict[str, str]): A dictionary mapping host paths to mount to container paths.
            devices (List[str]): A list of device paths to make available inside the container.
            other_options (List[str]): Additional Docker command line options.
            network (str): Optional Docker network mode for the container.
            workdir (PathType): Optional working directory inside the container.
            root (bool): Whether to run the container as root.
            tty (bool): Whether to allocate a TTY.
            interactive (bool): Whether to make the container interactive.
        """
        super().__init__(
            environment_variables=environment_variables,
            volumes=volumes,
            devices=devices,
            other_options=other_options,
        )
        self._image = image
        self._name = name
        self._network = network
        self._workdir = workdir
        self._root = root
        self._tty = tty
        self._interactive = interactive

        self._cached_command = None

    def __or__(self, other: DockerRunner) -> "ConcreteDockerRunner":
        if isinstance(other, ConcreteDockerRunner):
            return NotImplemented
        abstract_runner = super().__or__(other=other)
        return abstract_runner.concretize(
            image=self._image,
            name=self._name,
            network=self._network,
            workdir=self._workdir,
            root=self._root,
            tty=self._tty,
            interactive=self._interactive,
        )

    def get_command(self) -> List[str]:
        """
        Constructs the Docker command based on the current configuration.

        Returns:
            List[str]: The Docker command as a list of arguments.
        """

        if self._cached_command:
            return self._cached_command

        image = self._image

        header = ["docker", "run", "--rm"]
        tty = ["--tty"] if self._tty else []
        interactive = ["--interactive"] if self._interactive else []
        env = [f"--env={k}={v}" for k, v in self._environment_variables.items()]
        vol = [f"--volume={k}:{v}" for k, v in self._volumes.items()]
        dev = [f"--device={d}" for d in self._devices if Path(d).exists()]
        opt = [f"{o}" for o in self._other_options]
        # TODO gpus
        name = [f"--name={self._name}"] if self._name else []
        host = [f"--hostname={image}"]
        net = (
            [f"--network={self._network}"] + [f"--add-host={image}:127.0.1.1"]
            if self._network
            else []
        )
        wd = [f"--workdir={self._workdir}"] if self._workdir else []
        use = [] if self._root else [f"--user={get_uid()}:{get_gid()}"]

        command = (
            header
            + tty
            + interactive
            + env
            + vol
            + dev
            + opt
            + name
            + host
            + net
            + wd
            + use
            + [image]
            + ["$@"]
        )
        self._cached_command = command
        return command

    def get_str_command(self) -> str:
        """
        Constructs the Docker command as a single string.

        Returns:
            str: The Docker command.
        """
        cmd = self.get_command()
        result = " ".join(cmd)
        return result

    def run(self) -> None:
        """
        Executes the constructed Docker command.
        """
        command = self.get_command()
        if "$@" == command[-1]:
            command = command[:-1]
        shell_out(
            command=command,
            output_is_log=True,
        )

    def exec(
        self,
        command: str,
        output_is_log: bool = False,
    ) -> None:
        """
        Executes a command within an already running Docker container.

        Parameters:
            command (str): The command to execute inside the container.
            output_is_log (bool): If True, logs the output of the command.
        """
        shell_out(
            command=f"docker exec -ti {self._name} {command}",
            output_is_log=output_is_log,
        )

    def generate_script(
        self,
        output_path: PathType = "/tmp/benchkit/docker/latest/docker-run.sh",
    ):
        """
        Generates a script file to run the Docker container with the current configuration.

        Parameters:
            output_path (PathType): Path to save the generated script file.
        """
        command = self.get_command()

        head = command[:2]
        body = command[2:-1]
        tail = command[-1:]

        first_line = [" ".join(head) + " \\\n"]
        other_lines = [f"    {c} \\\n" for c in body]
        last_line = [f"    {c}" for c in tail]

        with open(output_path, "w") as script:
            script.writelines(
                [
                    "#!/bin/sh\n",
                    "set -ex\n",
                    "\n",
                ]
                + first_line
                + other_lines
                + last_line
                + ["\n"]
            )
