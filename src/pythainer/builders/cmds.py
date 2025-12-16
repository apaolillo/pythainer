# Copyright (C) 2024 Antonio Paolillo. All rights reserved.
# SPDX-License-Identifier: MIT

"""
This module defines classes that represent individual Docker build commands.
These classes are used to abstract the creation of Dockerfile command strings that configure the
environment, install packages, and set up Docker images during the build process.
The module facilitates the dynamic generation of Dockerfile content based on different requirements
and package managers.
"""

import shutil
from pathlib import Path
from typing import List

from pythainer.sysutils import mkdir


class DockerBuildCommand:
    """
    Abstract base class for Docker build commands.
    Each command type inheriting from this should implement a method to generate a string
    appropriate for including in a Dockerfile.
    """

    def __init__(self) -> None:
        """
        Initializes the DockerBuildCommand object.
        """

    def get_str_for_dockerfile(
        self,
        *args,
        **kwargs,
    ) -> str:
        """
        Abstract method to return a string for a Dockerfile based on the command's internal
        configuration.

        Raises:
            NotImplementedError: If the method is not implemented by the subclass.
        """
        raise NotImplementedError


class StrDockerBuildCommand(DockerBuildCommand):
    """
    Represents a simple string command in a Dockerfile, such as a comment or other directive that
    does not involve complex logic or conditional behavior.
    """

    def __init__(self, s: str) -> None:
        """
        Initializes the StrDockerBuildCommand with a string.

        Parameters:
            s (str): The string that represents this Dockerfile command.
        """
        super().__init__()
        self._str = s

    def get_str_for_dockerfile(
        self,
        *args,
        **kwargs,
    ) -> str:
        """
        Returns the string that was initialized at the creation of the object.

        Returns:
            str: The command string.
        """
        return str(self._str)


class CopyDockerBuildCommand(DockerBuildCommand):
    """
    Represents the command string to copy data from the host system to
    the docker container at build time.
    """

    def __init__(self, source_path: Path, destination_path: Path) -> None:
        """
        Initializes the CopyDockerBuildCommand with a a source and destination path.

        Parameters:
            source_path (Path): Path of folder or file to copy to container
            destination_path (Path): Path to copy the file or folder to
        """
        super().__init__()
        self._source_path = source_path.resolve()
        self._destination_path = destination_path

    # pylint: disable=arguments-differ
    def get_str_for_dockerfile(
        self,
        *args,
        **kwargs,
    ) -> str:
        """
        Generates a Dockerfile string to move files and folders.

        Returns:
            str: A Dockerfile command string for moving files and folders.
        """

        data_path = Path("/tmp/pythainer/docker/data")
        resulting_path = data_path / self._source_path.relative_to("/")
        relative_path = Path("data") / self._source_path.relative_to("/")
        mkdir(data_path)

        print(data_path)

        if self._source_path.is_file():
            mkdir(resulting_path.parent)
            shutil.copyfile(self._source_path, resulting_path)
        elif self._source_path.is_dir():
            shutil.copytree(self._source_path, resulting_path, dirs_exist_ok=True)
        else:
            raise FileExistsError(
                f"{self._source_path} is not a valid target to copy into the docker container"
            )

        cmd = f"COPY --chown=${{USER_NAME}} {relative_path} {self._destination_path}"

        return cmd


class AddPkgDockerBuildCommand(DockerBuildCommand):
    """
    Represents a Docker build command that installs packages using a specific package manager.
    """

    def __init__(
        self,
        packages: List[str],
    ) -> None:
        """
        Initializes the AddPkgDockerBuildCommand with a list of package names.

        Parameters:
            packages (List[str]): A list of package names to be installed.
        """
        super().__init__()
        self._packages = []
        self._packages.extend(packages)

    # pylint: disable=arguments-differ
    def get_str_for_dockerfile(
        self,
        pkg_manager: str,
        *args,
        **kwargs,
    ) -> str:
        """
        Generates a Dockerfile string to install packages using the specified package manager.

        Parameters:
            pkg_manager (str): The package manager to use (e.g., 'apt').

        Returns:
            str: A Dockerfile command string for installing the specified packages.

        Raises:
            ValueError: If an unsupported package manager is specified.
        """
        match pkg_manager:
            case "apt":
                return _add_pkg_apt(packages=self._packages)
            case _:
                raise ValueError(f"Unsupported package manager: {pkg_manager}")


def _add_pkg_apt(packages: List[str]) -> str:
    """
    Helper function to format an apt-get command to install specified packages.

    Parameters:
        packages (List[str]): A list of package names to be installed.

    Returns:
        str: A Dockerfile RUN command to update, install, and clean up apt packages.
    """
    fmt_packages = "".join([f"        {p} \\\n" for p in sorted(packages)])
    cmd = (
        f"apt-get update && apt-get install -y --no-install-recommends \\\n{fmt_packages}"
        f"    && rm -rf /var/lib/apt/lists/*"
    )
    return f"RUN {cmd}"
