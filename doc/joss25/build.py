#!/usr/bin/env python3
# Copyright (C) 2025 Antonio Paolillo. All rights reserved.
# SPDX-License-Identifier: MIT
"""
Build the JOSS25 paper using pythainer.
"""

from pythainer.runners import ConcreteDockerRunner
from pathlib import Path


def main() -> None:
    """Build the JOSS25 paper according to JOSS website instructions."""
    this_dir = Path(__file__).parent.resolve()

    runner = ConcreteDockerRunner(
        image="openjournals/inara",
        environment_variables={
            "JOURNAL": "joss",
        },
        volumes={
            f"{this_dir}": "/data",
        },
        other_options=[],
        tty=False,
        interactive=False,
    )

    runner.run()


if __name__ == "__main__":
    main()
