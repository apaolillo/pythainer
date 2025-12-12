# Copyright (C) 2024 Antonio Paolillo. All rights reserved.
# SPDX-License-Identifier: MIT

"""
This module provides various Docker runner configurations tailored for specific hardware
or user requirements, such as GUI support, camera access, GPU usage, and personal settings.
"""

import os
import shlex
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


def personal_runner(
    user_name: str = "user",
    preserve_history: bool = False,
    use_host_rc: bool = False,
) -> DockerRunner:
    """
    Create a DockerRunner configured with personal environment files, optionally preserving shell
    history and/or using the host's shell configuration.

    By default, the runner mounts personal `vimrc` and `tmux.conf` files from
    `~/git/machines-config/dotfiles/` into the container for the given user.

    Additional behavior:
        - If `preserve_history` is True:
            Creates and mounts persistent bash and zsh history files under `.pythainer/`
            so command history is preserved between container runs.
        - If `use_host_rc` is True:
            Mounts the host's `.bashrc`, `.zshrc`, and `~/dotfiles/` (including its
            subdirectories) into the container to replicate the host's shell and tool
            configuration.

    Args:
        user_name (str, optional):
            Name of the container user for which the configuration is applied.
            Defaults to "user".
        preserve_history (bool, optional):
            Whether to mount persistent shell history files into the container.
            Defaults to False.
        use_host_rc (bool, optional):
            Whether to mount the host's shell RC files and dotfiles into the container.
            Defaults to False.

    Returns:
        DockerRunner: Runner instance configured with the specified mounts.
    """

    vimrc = Path("~/git/machines-config/dotfiles/vimrc").expanduser()
    tmuxconf = Path("~/git/machines-config/dotfiles/tmux.conf").expanduser()

    volumes = {
        vimrc: f"/home/{user_name}/.vimrc",
        tmuxconf: f"/home/{user_name}/.tmux.conf",
    }

    # Create history files for shells (currently supporting bash and zsh) that are
    # mounted as volumes in the container. The histories of command are saved between
    # execution of the container.
    if preserve_history:
        histories = [Path("./.pythainer/history.bash"), Path("./.pythainer/history.zsh")]
        for history in histories:
            history.parent.mkdir(parents=True, exist_ok=True)
            if not history.exists():
                history.write_text("")
            shell_type = history.suffix.lstrip(".")
            volumes[history] = f"/home/{user_name}/.{shell_type}_history"

    dotfiles = (
        [
            Path("~/dotfiles/").expanduser(),
            Path("~/.bashrc").expanduser(),
            Path("~/.zshrc").expanduser(),
        ]
        if use_host_rc
        else []
    )
    for dotfile in dotfiles:
        if dotfile.is_dir():
            for f in dotfile.iterdir():
                if f.is_dir():
                    volumes[f.resolve()] = f"/home/{user_name}/.config/{f.name}"
        else:
            volumes[dotfile.resolve()] = f"/home/{user_name}/{dotfile.name}"

    volumes = {
        str(host_path): docker_path
        for host_path, docker_path in volumes.items()
        if host_path.exists()
    }

    return DockerRunner(
        environment_variables={},
        volumes=volumes,
        devices=[],
    )
