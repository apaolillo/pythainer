# Copyright (C) 2025 Antonio Paolillo. All rights reserved.
# SPDX-License-Identifier: MIT
"""CLI-level tests for pythainer.

This module verifies:
1) The root CLI (`pythainer`) exposes `--help` and exits with code 0.
2) The `scaffold` subcommand generates a script identical to a golden reference.
"""

from pathlib import Path

from click.testing import CliRunner

from pythainer.cli import cli, scaffold


def test_cli_help() -> None:
    """`pythainer --help` exits successfully and shows a Usage section."""
    r = CliRunner().invoke(cli, ["--help"])
    assert r.exit_code == 0
    assert "Usage:" in r.output


def test_cli_scaffold(tmp_path: Path) -> None:
    """`pythainer scaffold` writes the expected script and stdout message.

    Uses pytest's tmp_path to avoid filesystem collisions and to keep tests parallel-safe.
    """
    actual_scaffolded_path = tmp_path / "scaffold.py"
    expected_scaffolded_path = Path(__file__).parent.parent / "golden" / "scaffold.py"

    r = CliRunner().invoke(
        scaffold,
        args=[
            "--image",
            "testimg",
            "--builders=rust",
            "--runners=gpu,gui",
            f"--output={actual_scaffolded_path}",
        ],
    )
    assert r.exit_code == 0
    assert f"Scaffold written to {actual_scaffolded_path}\n" == r.output
    assert actual_scaffolded_path.exists()

    actual_scaffolded = actual_scaffolded_path.read_text()
    expected_scaffolded = expected_scaffolded_path.read_text()
    assert expected_scaffolded == actual_scaffolded
