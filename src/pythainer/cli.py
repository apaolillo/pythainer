# Copyright (C) 2025 Antonio Paolillo. All rights reserved.
# SPDX-License-Identifier: MIT
"""
CLI interface for Pythainer.

This module provides a command-line interface to build and run Docker images
using Pythainer builders and runners. It exposes two subcommands:

- `run`: always rebuilds the Docker image with the specified builders and then
  runs the container with the specified runners.
- `scaffold`: generates a starter Python script that reproduces the chosen
  builders and runners, so the user can customize it further.

Builders and runners are dynamically discovered from
`pythainer.examples.builders` and `pythainer.examples.runners`.
"""

import sys
from pathlib import Path
from typing import Callable, List, Optional

import black
import click
import isort

import pythainer.examples.builders as ex_builders
import pythainer.examples.runners as ex_runners
from pythainer.builders import PartialDockerBuilder, UbuntuDockerBuilder
from pythainer.runners import ConcreteDockerRunner, DockerRunner

BuilderFunc = Callable[..., PartialDockerBuilder]
RunnerFunc = Callable[..., DockerRunner]

WS_DIR = "/home/${USER_NAME}/workspace"
LIB_DIR = "/home/${USER_NAME}/workspace/libraries"

# Make "-h" behave like "--help"
CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


def get_all_builders() -> list[str]:
    """
    Return a list of all available builder names discovered from
    `pythainer.examples.builders`.

    Returns:
        A list of builder names without the `_builder` suffix.
    """
    return [b[:-8] for b in dir(ex_builders) if b.endswith("_builder") and "get_user" not in b]


def get_all_runners() -> list[str]:
    """
    Return a list of all available runner names discovered from
    `pythainer.examples.runners`.

    Returns:
        A list of runner names without the `_runner` suffix.
    """
    return [r[:-7] for r in dir(ex_runners) if r.endswith("_runner")]


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(
    package_name="pythainer",
    prog_name="pythainer",
    message="%(prog)s %(version)s",
)
def cli() -> None:
    """Pythainer: build and run reproducible containers with Python builders/runners."""


@cli.command()
@click.option(
    "--image",
    default="pythainercli",
    help="Docker image name (defaults to 'pythainercli')",
)
@click.option("--container", help="Container name (defaults to image)")
@click.option("--builders", default="", help="Comma-separated builder names")
@click.option("--runners", default="", help="Comma-separated runner names")
@click.option("--list", "list_only", is_flag=True, help="List available builders and runners")
def run(
    image: str,
    container: str | None,
    builders: str,
    runners: str,
    list_only: bool,
) -> None:
    """
    Build and run a container.

    This command always rebuilds the image with the selected builders,
    then runs the container with the selected runners.
    """
    click.echo(
        f"Launching Pythainer: building image '{image}', with builders: {builders}; "
        f"then running with runners: {runners}"
    )

    available_builders = get_all_builders()
    available_runners = get_all_runners()

    if list_only:
        click.echo("Available builders:")
        for b in available_builders:
            click.echo(f"  {b}")
        click.echo("Available runners:")
        for r in available_runners:
            click.echo(f"  {r}")
        sys.exit(0)

    container_name: str = container or image

    selected_builders: List[str] = [b.strip() for b in builders.split(",") if b.strip()]
    selected_runners: List[str] = [r.strip() for r in runners.split(",") if r.strip()]

    # validate builders
    for b in selected_builders:
        if b not in available_builders:
            raise click.ClickException(
                f"Unknown builder '{b}'. Available: {', '.join(available_builders)}"
            )

    # validate runners
    for r in selected_runners:
        if r not in available_runners:
            raise click.ClickException(
                f"Unknown runner '{r}'. Available: {', '.join(available_runners)}"
            )

    # apply builders (always rebuild philosophy)
    builder: UbuntuDockerBuilder = ex_builders.get_user_gui_builder(
        image_name=image,
        base_ubuntu_image="ubuntu:24.04",
    )
    builder.space()

    for builder_name in selected_builders:
        next_builder: BuilderFunc = getattr(ex_builders, f"{builder_name}_builder")
        builder.desc(f"Build {builder_name}")
        builder.workdir(path=LIB_DIR)
        builder |= next_builder()
        builder.space()

    builder.user()
    builder.workdir(path=WS_DIR)

    runner = ConcreteDockerRunner(image=image, name=container_name)
    for runner_name in selected_runners:
        next_runner: RunnerFunc = getattr(ex_runners, f"{runner_name}_runner")
        runner |= next_runner()

    click.echo("→ Building image...")
    builder.build()

    runner.run()


@cli.command()
@click.option(
    "--image",
    default="pythainercli",
    help="Docker image name (defaults to 'pythainercli')",
)
@click.option("--container", help="Container name (defaults to image)")
@click.option("--builders", default="", help="Comma-separated builder names")
@click.option("--runners", default="", help="Comma-separated runner names")
@click.option("--output", type=click.Path(), help="Write scaffold to file (stdout if omitted)")
def scaffold(
    image: str,
    container: str | None,
    builders: str,
    runners: str,
    output: Optional[str],
) -> None:
    """
    Generate a starter Pythainer script instead of running.

    The generated script includes the selected builders and runners,
    always rebuilds the image, and runs the container. It can be saved
    to a file (via --output) or printed to stdout.
    """
    container_name: str = container or image
    selected_builders: List[str] = [b.strip() for b in builders.split(",") if b.strip()]
    selected_runners: List[str] = [r.strip() for r in runners.split(",") if r.strip()]

    builders_str = ", ".join(sorted(f"{b}_builder" for b in selected_builders))
    runners_str = ", ".join(sorted(f"{r}_runner" for r in selected_runners))

    lines: List[str] = [
        "#!/usr/bin/env python3",
        '"""',
        "Build and run a reproducible Ubuntu-based image using pythainer.",
        "",
        "Steps:",
        "1) Create the base builder.",
        "2) Apply builder steps.",
        "3) Build the image.",
        "4) Configure the runner and run the container.",
        '"""',
        "",
        f"from pythainer.examples.builders import get_user_gui_builder, {builders_str}",
        f"from pythainer.examples.runners import {runners_str}",
        "from pythainer.builders import UbuntuDockerBuilder",
        "from pythainer.runners import ConcreteDockerRunner",
        "",
        f'IMAGE = "{image}"',
        f'CONTAINER = "{container_name}"',
        f'LIB_DIR = "{LIB_DIR}"',
        "",
        "def main() -> None:",
        '    """Build the Docker image and run it with configured capabilities."""',
        "    builder: UbuntuDockerBuilder = get_user_gui_builder(",
        "        image_name=IMAGE,",
        '        base_ubuntu_image="ubuntu:24.04",',
        "    )",
        "    builder.space()",
        "",
    ]

    for b in selected_builders:
        lines.append(f'    builder.desc("Build {b}")')
        lines.append("    builder.workdir(path=LIB_DIR)")
        lines.append(f"    builder |= {b}_builder()")
        lines.append("    builder.space()")
        lines.append("")

    lines.append("    builder.user()")
    lines.append(f'    builder.workdir(path="{WS_DIR}")')
    lines.append("")
    lines.append("    builder.build()")
    lines.append("")
    lines.append("    runner = ConcreteDockerRunner(image=IMAGE, name=CONTAINER)")
    lines.extend(f"    runner |= {r}_runner()" for r in selected_runners)
    lines.append("")
    lines.append("    runner.run()")
    lines.append("")
    lines.append('if __name__ == "__main__":')
    lines.append("    main()")

    content: str = "\n".join(lines) + "\n"

    content = isort.code(content, config=isort.Config(profile="black", line_length=100))
    content = black.format_str(
        content,
        mode=black.Mode(line_length=100, target_versions={black.TargetVersion.PY310}),
    )

    if output:
        Path(output).write_text(content)
        click.echo(f"Scaffold written to {output}")
    else:
        click.echo(content)


def main() -> None:
    """Entry point for the Pythainer CLI when installed as a script."""
    cli()


if __name__ == "__main__":
    main()
