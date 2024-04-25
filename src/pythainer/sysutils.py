# Copyright (C) 2024 Antonio Paolillo. All rights reserved.
# SPDX-License-Identifier: MIT

"""
This module provides system-level utilities for the pythainer package.
It includes functions for executing shell commands, handling directories, and retrieving system user
and group IDs.
These utilities are essential for the operation of Docker containers and other system-level
operations.
"""

import os
import shlex
import subprocess
from pathlib import Path
from typing import Dict, List

PathType = str | Path
Environment = Dict[str, str] | None


def _print_cmd(
    command: List[str],
    environment: Environment,
) -> None:
    """
    Helper function to print the command line statement that will be executed, including the
    environment variables.

    Parameters:
        command (List[str]): The command to be executed as a list of strings.
        environment (Environment): A dictionary of environment variables to be set before executing
                                   the command.
    """
    if environment:
        printed_env = " ".join([f"{k}={v}" for k, v in environment.items()]) + " "
    else:
        printed_env = ""
    printed_cmd = " ".join(command)
    full_printed_cmd = printed_env + printed_cmd
    print(f"[{full_printed_cmd}]")


def shell_out(
    command: List[str] | str,
    current_dir: PathType | None = None,
    environment: Environment = None,
    output_is_log: bool = False,
) -> str:
    """
    Executes a shell command and optionally logs the output.
    Returns the output from the command if not logging.

    Parameters:
        command (List[str] | str): The command to execute, either as a string or a list of strings.
        current_dir (PathType | None): The directory in which to execute the command.
        environment (Environment): Environment variables to set for the command.
        output_is_log (bool): If True, logs the output to the console and returns an empty string.

    Returns:
        str: The output from the command execution if output_is_log is False;
             otherwise, an empty string.
    """
    if isinstance(command, str):
        command = shlex.split(command)
    _print_cmd(command=command, environment=environment)
    if output_is_log:
        subprocess.check_call(command, text=True, cwd=current_dir, env=environment)
        result = ""
    else:
        output = subprocess.check_output(command, text=True, cwd=current_dir, env=environment)
        result = output.strip()
    return result


def mkdir(path: PathType) -> None:
    """
    Creates a directory at the specified path if it does not already exist.

    Parameters:
        path (PathType): The path where the directory should be created.
    """
    if not os.path.exists(path):
        os.makedirs(path)


def get_uid() -> str:
    """
    Retrieves the user ID of the current user by executing the 'id -u' command.

    Returns:
        str: The user ID as a string.
    """
    return shell_out("id -u")


def get_gid() -> str:
    """
    Retrieves the group ID of the current user by executing the 'id -g' command.

    Returns:
        str: The group ID as a string.
    """
    return shell_out("id -g")


def mkdir_for_path(path: PathType) -> None:
    """
    Ensures that the parent directory for a given path exists, creating it if necessary.

    Parameters:
        path (PathType): The path for which the parent directory needs verification or creation.

    Raises:
        ValueError: If the parent path exists and is not a directory.
    """
    path = Path(path)
    if path.is_dir():
        return

    parent_path = path.parent
    if parent_path.is_dir():
        return
    if parent_path.is_file():
        raise ValueError(f'Error, parent path is not a directory: "{parent_path}"')

    mkdir(path=parent_path)
