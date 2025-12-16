# Copyright (C) 2024 Antonio Paolillo. All rights reserved.
# SPDX-License-Identifier: MIT

"""
This module defines classes that represent individual Docker build commands.
These classes are used to abstract the creation of Dockerfile command strings that configure the
environment, install packages, and set up Docker images during the build process.
The module facilitates the dynamic generation of Dockerfile content based on different requirements
and package managers.
"""

from pathlib import Path


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
    Represents a Dockerfile COPY instruction.

    Notes:
        - Sources are paths *inside the build context* (relative).
        - Destination is a path *inside the image* (absolute or relative).
        - If multiple sources are provided, destination must be treated as a directory.
    """

    def __init__(
        self,
        sources: list[Path],
        destination: Path,
        chown: str | None = None,
        chmod: str | None = None,
    ) -> None:
        """
        Initializes the COPY command.

        Parameters:
            sources: One or more source paths. These should refer to paths within the
                build context. These are the staged paths.
            destination: Destination path in the image (container filesystem).
            chown: Optional ownership for copied files (Dockerfile: COPY --chown=...).
            chmod: Optional mode for copied files (Dockerfile: COPY --chmod=...).

        Raises:
            ValueError: If sources is empty.
        """
        super().__init__()

        srcs = tuple(Path(s) for s in sources)
        if not srcs:
            raise ValueError("COPY requires at least one source path")

        self._sources: tuple[Path, ...] = srcs
        self._destination: Path = Path(destination)

        self._chown = chown
        self._chmod = chmod

    def get_str_for_dockerfile(
        self,
        *args,
        **kwargs,
    ) -> str:
        """
        Generate the Dockerfile `COPY` instruction string.

        This method is pure: it does not read from or write to the host filesystem,
        and it does not perform any staging. All sources must already refer to
        paths *inside the build context* (i.e., context-relative paths prepared
        by the builder).

        Returns:
            str: A Dockerfile `COPY` command line.
        """
        flags: list[str] = []
        if self._chown is not None:
            flags.append(f"--chown={self._chown}")
        if self._chmod is not None:
            flags.append(f"--chmod={self._chmod}")

        flags_str = (" " + " ".join(flags)) if flags else ""
        sources_str = " ".join(str(s) for s in self._sources)

        result = f"COPY{flags_str} {sources_str} {self._destination}"
        return result


class AddPkgDockerBuildCommand(DockerBuildCommand):
    """
    Represents a Docker build command that installs packages using a specific package manager.
    """

    def __init__(
        self,
        packages: list[str],
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


def _add_pkg_apt(packages: list[str]) -> str:
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
