# Copyright (C) 2024 Antonio Paolillo. All rights reserved.
# SPDX-License-Identifier: MIT

"""
This utility module provides a set of functions to assist in the process of building Docker images
for projects. It includes functions for setting up Docker builders, handling project-specific
configurations, and ensuring clean installations of software components like CMake, as well as
managing the cloning and building of projects from Git repositories.
"""

from pathlib import Path
from typing import Dict, List

from pythainer.builders import DockerBuilder, PartialDockerBuilder
from pythainer.sysutils import PathType


def _project_cleanup_commands(
    path: PathType,
    cleanup: bool,
) -> List[str]:
    """
    Generates commands for cleaning up a project directory after build operations.

    Parameters:
        path (PathType): The path to the project directory to clean up.
        cleanup (bool): Whether to perform cleanup operations.

    Returns:
        List[str]: A list of shell commands for cleaning up the project directory.
    """
    if not cleanup:
        return []

    username_tag = "${USER_NAME}:${USER_NAME}"
    commands = [
        f"(rm -rf {path} || true)",
        f"(sudo chown -f --recursive {username_tag} {path} || true)",
        f"rm -rf {path}",
    ]

    return commands


def cmake_build_install(
    builder: DockerBuilder,
    version: str,
    workdir: PathType,
    cleanup: bool = True,
) -> None:
    """
    Configures and builds CMake from source, then installs it using the provided DockerBuilder.

    Parameters:
        builder (DockerBuilder): The DockerBuilder instance to use for commands.
        version (str): The version of CMake to install.
        workdir (PathType): The working directory inside the Docker image.
        cleanup (bool): Whether to clean up the build artifacts. Defaults to True.
    """
    version_str = "${cmake_version}"
    pkg_name = f"cmake-{version_str}.tar.gz"
    url = f"https://github.com/Kitware/CMake/releases/download/v{version_str}/{pkg_name}"

    cmake_dirname = "cmake-${cmake_version}"
    cmake_pathname = Path(workdir) / cmake_dirname

    builder.workdir(path=workdir)
    builder.arg(name="cmake_version", value=version)
    builder.run(command=f"wget --quiet {url}")
    builder.run(command=f"tar -xf {pkg_name}")
    builder.workdir(path=cmake_dirname)
    builder.run_multiple(
        commands=[
            "./bootstrap --parallel=$(nproc)",
            "make -j $(nproc)",
            "sudo make install",
        ]
        + _project_cleanup_commands(
            path=cmake_pathname,
            cleanup=cleanup,
        )
    )


def project_git_clone(
    builder: PartialDockerBuilder,
    workdir: PathType,
    git_url: str,
    commit: str,
    submodule_init_recursive: bool = False,
    single_run_command: bool = False,
) -> str:
    """
    Clones a Git repository at a specified commit into a Docker environment, optionally initializing
    submodules.

    Parameters:
        builder (PartialDockerBuilder): The Docker builder to execute the commands.
        workdir (PathType): The working directory in the Docker environment.
        git_url (str): The URL of the Git repository to clone.
        commit (str): The specific commit to check out.
        submodule_init_recursive (bool): Whether to recursively initialize submodules.

    Returns:
        str: The name of the repository directory.
    """
    repo_name = git_url.split("/")[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]

    if single_run_command:
        commands = [
            f"cd {workdir}",
            f"git clone {git_url}",
            f"cd {repo_name}",
            f"git checkout {commit}",
        ] + (["git submodule update --init --recursive"] if submodule_init_recursive else [])

        builder.run_multiple(commands=commands)
    else:
        builder.workdir(path=workdir)
        builder.run(command=f"git clone {git_url}")
        builder.workdir(path=repo_name)
        builder.run(command=f"git checkout {commit}")
        if submodule_init_recursive:
            builder.run(command="git submodule update --init --recursive")

    return repo_name


def project_cmake_build_install(
    builder: PartialDockerBuilder,
    workdir: PathType,
    repo_name: str,
    generator: str = "",
    cmake_options: Dict[str, str] | None = None,
    install: bool = True,
    cleanup: bool = True,
) -> None:
    """
    Configures, builds, and optionally installs a project using CMake within a Docker environment.

    Parameters:
        builder (PartialDockerBuilder): The builder to use for Docker commands.
        workdir (PathType): The base directory for the project within the Docker environment.
        repo_name (str): The name of the repository containing the source code.
        generator (str): The make system generator to use (e.g., 'ninja', 'make').
        cmake_options (Dict[str, str]): Options to pass to the cmake command.
        install (bool): Whether to run the 'make install' or equivalent command.
        cleanup (bool): Whether to clean up build artifacts and temporary files after installation.
                        Defaults to True.
    """
    project_path = Path(workdir) / repo_name

    if generator or cmake_options:
        list_options = []
        if generator:
            list_options += [f"-G {generator}"]
        if cmake_options:
            list_options += [f"-D{k}={v}" for k, v in cmake_options.items()]

        spaces = " " * 8
        list_options_fmt = [f"{spaces}{o} \\\n" for o in list_options]
        cmake_cmd = "cmake \\\n" + "".join(list_options_fmt) + f"{spaces}.."
    else:
        cmake_cmd = "cmake .."
    if not generator:
        generator = "make"

    generator_command = generator.lower()

    build_command = f"{generator_command}" if generator else "make"

    commands = [
        "mkdir build",
        "cd build",
        cmake_cmd,
        f"{build_command} -j $(nproc)",
    ]
    if install:
        commands.append(f"sudo {generator_command} install")
    commands += _project_cleanup_commands(
        path=project_path,
        cleanup=cleanup,
    )

    builder.run_multiple(commands=commands)


def project_git_cmake_build_install(
    builder: DockerBuilder,
    workdir: PathType,
    git_url: str,
    commit: str,
    patch_commands: List[str] = (),
    submodule_init_recursive: bool = False,
    cmake_options: Dict[str, str] | None = None,
    cleanup: bool = True,
) -> None:
    """
    Clones a project from a Git repository, applies optional patches, and builds it using CMake in
    a Docker environment.

    Parameters:
        builder (DockerBuilder): The Docker builder to execute the commands.
        workdir (PathType): The directory within the Docker environment where the project will be
                            built.
        git_url (str): The URL of the Git repository to clone.
        commit (str): The commit hash to checkout.
        patch_commands (List[str]): A list of shell commands to apply patches or other pre-build
                                    modifications.
        submodule_init_recursive (bool): Whether to recursively initialize Git submodules.
        cmake_options (Dict[str, str]): A dictionary of CMake options to pass to the cmake command.
        cleanup (bool): Whether to clean up after building. Defaults to True.
    """
    repo_name = project_git_clone(
        builder=builder,
        workdir=workdir,
        git_url=git_url,
        commit=commit,
        submodule_init_recursive=submodule_init_recursive,
    )

    for patch_command in patch_commands:
        builder.run(command=patch_command)

    project_cmake_build_install(
        builder=builder,
        workdir=workdir,
        repo_name=repo_name,
        cmake_options=cmake_options,
        cleanup=cleanup,
    )
