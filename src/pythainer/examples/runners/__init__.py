# Copyright (C) 2024 Antonio Paolillo. All rights reserved.
# SPDX-License-Identifier: MIT

"""
This module provides various Docker runner configurations tailored for specific hardware
or user requirements, such as GUI support, camera access, GPU usage, and personal settings.
"""

import os
import shlex
from pathlib import Path
from turtle import dot

from pythainer.runners import DockerRunner


def gui_runner(mount_input_events: bool = True) -> DockerRunner:
    """
    Configures a Docker runner to enable GUI applications by setting up necessary environment
    variables and volumes.
pip install basedpyright
    Parameters:
        mount_input_events (bool): If True, mounts all input event devices to the container.
                                   Defaults to True.

    Returns:
        DockerRunner: Configured DockerRunner instance with necessary settings for GUI support.
    """

    environment_variables = {}
    volumes = {}

    if display := os.environ.get("DISPLAY"):
        environment_variables["DISPLAY"] = f"{display}"

    if (tmp_x11_path := Path("/tmp/.X11-unix")).is_dir():
        tmp_x11_path_str = f"{tmp_x11_path}"
        volumes[tmp_x11_path_str] = tmp_x11_path_str

    if xauthority := os.environ.get("XAUTHORITY"):
        environment_variables[f"{xauthority}"] = "/root/.Xauthority"

    devices = []

    if mount_input_events:
        input_devices = [
            f"/dev/input/{d}" for d in os.listdir("/dev/input") if d.startswith("event")
        ]
        print(input_devices)
        devices.extend(input_devices)

    return DockerRunner(
        environment_variables=environment_variables,
        volumes=volumes,
        devices=devices,
    )


def camera_runner() -> DockerRunner:
    """
    Creates a Docker runner configured to access camera and media devices.

    Returns:
        DockerRunner: A DockerRunner configured with access to video and media device paths.
    """
    options = '--privileged --device-cgroup-rule="c 81:* rmw" --device-cgroup-rule="c 189:* rmw"'
    options_split = shlex.split(options)

    return DockerRunner(
        environment_variables={},
        volumes={},
        devices=["/dev"],
        other_options=options_split,
    )


def gpu_runner() -> DockerRunner:
    """
    Configures a Docker runner to use the GPU.

    Returns:
        DockerRunner: A DockerRunner instance configured with NVIDIA runtime and GPU access.
    """

    return DockerRunner(
        other_options=[
            "--runtime=nvidia",
            "--gpus=all",
        ]
    )


def personal_runner(user_name: str = "user", preserve_history: bool = False) -> DockerRunner:
    """
    Sets up a Docker runner with personal configuration files for vim and tmux from a given user's
    repository.

    Parameters:
        user_name (str): The name of the (container) user for whom the environment is configured.
                         Defaults to "user".

    Returns:
        DockerRunner: A DockerRunner configured with personal environment settings.
    """
     
    vimrc = Path("~/git/machines-config/dotfiles/vimrc").expanduser()
    tmuxconf = Path("~/git/machines-config/dotfiles/tmux.conf").expanduser()
    
    volumes={
        f"{vimrc}": f"/home/{user_name}/.vimrc",
        f"{tmuxconf}": f"/home/{user_name}/.tmux.conf",
    }

    dotfiles = [Path("~/dotfiles/").expanduser()]
    
    dotfiles.append(Path("~/.bashrc").expanduser())
    dotfiles.append(Path("~/.zshrc").expanduser())
    
    # Create history files for shells (currently supporting bash and zsh) that are
    # mounted as volumes in the container. The histories of command are saved between
    # execution of the container
    if preserve_history:
        histories = [Path("./.pythainer_history.bash"), Path("./.pythainer_history.zsh")]
        for history in histories: 
            if not history.exists():
                with open(history, 'w') as file:
                    file.write("")
            shell_type = history.name.split(".")[-1]
            volumes[f"{history}"] = f"/home/{user_name}/.{shell_type}_history"
    
    for dotfile in dotfiles:
        if dotfile.exists():
            if dotfile.is_dir():
                for f in dotfile.iterdir():
                    if f.is_dir():
                        volumes[f"{f.absolute()}"] = f"/home/{user_name}/.config/{f.name}"
            else:
                volumes[f"{dotfile.absolute()}"] = f"/home/{user_name}/{dotfile.name}"

    return DockerRunner(
        environment_variables={},
        volumes=volumes,
        devices=[],
    )
