# Copyright (C) 2025 Antonio Paolillo. All rights reserved.
# SPDX-License-Identifier: MIT
"""
 Pytest configuration for pythainer tests.

Registers custom markers:
- integration: requires Docker engine
- slow: long build/pull
"""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers so --strict-markers doesn’t error."""
    config.addinivalue_line("markers", "integration: requires Docker engine")
    config.addinivalue_line("markers", "slow: long build/pull")
