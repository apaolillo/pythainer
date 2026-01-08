# Copyright (C) 2025 Antonio Paolillo. All rights reserved.
# SPDX-License-Identifier: MIT
"""
Build context management for Docker image construction.

This module defines the `BuildContext`, which is responsible for
constructing a Docker build context from a set of host-side files and
directories. The build context is a *materialized directory tree* that
Docker can consume during `docker build`.

This module is *host-aware* and performs filesystem operations. Dockerfile AST
nodes will further reference context-relative paths. Each context entry maps a
host path to a unique, relative path inside the build context. Context paths
are validated to prevent path traversal (`..`). Conflicting context entries
are detected and rejected.

The build context is populated explicitly via `add_context_entry` and can be
merged with other contexts via `extend`. Once fully defined, the context can be
materialized on disk using `build` (from the DockerBuilder class).
"""

import shutil
from pathlib import Path

from pythainer.sysutils import PathType


class BuildContext:
    """
    Represents a Docker build context under construction.

    A `BuildContext` maintains a mapping from *context-relative paths*
    (paths as seen by the Dockerfile) to *host filesystem paths*. It is
    responsible for materializing this mapping into a directory tree that
    can be passed to `docker build`.

    Attributes:
        _context_root:
            Optional root directory used to compute context-relative paths.
            If provided, all added host paths must be located under this root.
        _context_entries:
            Mapping from context-relative paths to host filesystem paths.
    """

    def __init__(self, context_root: PathType | None = None) -> None:
        """
        Initialize an empty build context.

        Args:
            context_root (PathType, optional):
                Optional directory that defines the root of the build context.
                If set, added host paths are made relative to this root when
                computing their context paths. If `None`, only the basename
                of each host path is used.
        """
        self._context_root = Path(context_root) if context_root else None
        self._context_entries: dict[Path, Path] = {}  # ctx_path -> host_path

    def extend(self, other: "BuildContext") -> None:
        """
        Merge another build context into this one.

        All context entries from `other` are added to this context. If a
        context-relative path already exists in both contexts and refers to
        different host paths, the merge fails.

        Args:
            other: Another `BuildContext` to merge.

        Raises:
            ValueError: If conflicting context entries are detected.
        """
        # pylint: disable=protected-access
        collision_paths = self._context_entries.keys() & other._context_entries.keys()
        diff_collision_paths = {
            str(p) for p in collision_paths if self._context_entries[p] != other._context_entries[p]
        }
        if diff_collision_paths:
            raise ValueError(
                f"Duplicate context entries detected before merging: {diff_collision_paths}"
            )

        self._context_entries.update(other._context_entries)

    def add_context_entry(self, host_path: PathType) -> Path:
        """
        Register a host file or directory in the build context.

        The host path is mapped to a context-relative path. If `context_root`
        was provided at construction time, the context path is computed as the
        path of `host_path` relative to `context_root`. Otherwise, the basename
        of `host_path` is used. This means collisions can occur when two
        different host paths share the same filename.

        Args:
            host_path: Path to a file or directory on the host filesystem.

        Returns:
            The context-relative path under which the entry will appear in the
            build context.

        Raises:
            ValueError: If a different host path is already registered under
                the same context-relative path.
        """
        host_path = Path(host_path)

        if self._context_root is not None:
            ctx_path = host_path.relative_to(self._context_root)
        else:
            ctx_path = Path(host_path.name)

        if ctx_path in self._context_entries and self._context_entries[ctx_path] != host_path:
            raise ValueError(f"Duplicate context entry: {ctx_path}")

        self._context_entries[ctx_path] = host_path
        return ctx_path

    def build(self, context_path: PathType) -> None:
        """
        Materialize the build context on disk.

        For each registered context entry `(ctx_path, host_path)`, the host
        file or directory is copied into  `<context_path>/<ctx_path>`.

        Intermediate directories are created as needed, and the relative
        hierarchy encoded in `ctx_path` is preserved.

        Args:
            context_path (PathType):
                Directory that will become the root of the Docker build context.

        Raises:
            ValueError:
                If a context path is absolute or contains path traversal
                components (`..`).
            FileNotFoundError:
                If a registered host path does not exist.
        """
        context_root = Path(context_path)
        context_root.mkdir(parents=True, exist_ok=True)

        for ctx_path, host_path in self._context_entries.items():
            ctx_path = Path(ctx_path)
            host_path = Path(host_path)

            if ctx_path.is_absolute() or ".." in ctx_path.parts:
                raise ValueError(f"Invalid context path (must be relative, no '..'): {ctx_path}")

            if not host_path.exists():
                raise FileNotFoundError(f"Host path does not exist: {host_path}")

            dst_path = context_root / ctx_path

            if host_path.is_file():
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(host_path, dst_path)
            elif host_path.is_dir():
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(host_path, dst_path, dirs_exist_ok=True)
            else:
                raise ValueError(f"Host path must be a file or directory: {host_path}")
