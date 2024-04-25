# Copyright (C) 2024 Antonio Paolillo. All rights reserved.
# SPDX-License-Identifier: MIT

"""
This module provides various Docker runner configurations tailored for specific hardware
or user requirements, such as GUI support, camera access, GPU usage, and personal settings.
"""

import os
from pathlib import Path

from pythainer.runners import DockerRunner


def gui_runner(mount_input_events: bool = True) -> DockerRunner:
    """
    Configures a Docker runner to enable GUI applications by setting up necessary environment
    variables and volumes.

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

    all_devices = os.listdir("/dev")
    devices = ["/dev/bus/usb", "/dev/dri"]
    devices += [f"/dev/{f}" for f in all_devices if f.startswith("video") or f.startswith("media")]

    return DockerRunner(
        environment_variables={},
        volumes={},
        devices=devices,
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


def personal_runner(user_name: str = "user") -> DockerRunner:
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

    return DockerRunner(
        environment_variables={},
        volumes={
            f"{vimrc}": f"/home/{user_name}/.vimrc",
            f"{tmuxconf}": f"/home/{user_name}/.tmux.conf",
        },
        devices=[],
    )
