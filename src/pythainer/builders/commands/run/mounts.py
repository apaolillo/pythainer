# Copyright (C) 2025 Antonio Paolillo. All rights reserved.
# SPDX-License-Identifier: MIT
"""
Utilities for expressing `RUN --mount` clauses in a Dockerfile.

This module provides the `RunMount` dataclass, which models a single mount
specification to be used with Docker BuildKit's extended syntax:

    RUN --mount=type=...,option=value,... <command>

Each mount corresponds to a named mount type (`bind`, `cache`, `tmpfs`,
`secret`, `ssh`) and a mapping of mount-specific options.

The convenience class methods (`cache`, `bind`, `tmpfs`, `secret`, `ssh`) provide
typed constructors that mirror Docker's documented mount options and generate a
`RunMount` instance ready for serialization via `to_flag()`.

The output of `to_flag()` is intended to be consumed by the Dockerfile builder,
which concatenates several mounts and produces a full instruction like:

    RUN --mount=type=cache,target=/root/.cache/go-build go build ...

The `RunMount` objects themselves are purely declarative and contain no
Docker-specific logic beyond formatting.
"""

from dataclasses import dataclass, field
from typing import Dict, Union

Scalar = Union[str, int, bool]


@dataclass
class RunMount:
    """
    Represents a single Docker BuildKit mount clause for a `RUN` instruction.

    A `RunMount` encapsulates both the mount type (e.g., `"cache"`, `"bind"`,
    `"secret"`) and the dictionary of mount-specific options. The instance can
    be converted to a valid Docker CLI flag using `to_flag()`, producing:

        --mount=type=<mount_type>,key=value,key2=value2,...

    The class also provides convenience constructors (for example, `cache()`,
    `secret()`, `ssh()`) that populate the correct option fields for the
    respective mount types and mirror the documented BuildKit semantics.

    Attributes:
        mount_type (str):
            The Docker mount type (for example, `"cache"`, `"bind"`, `"tmpfs"`,
            `"secret"`, `"ssh"`).

        options (dict[str, Scalar]):
            Dictionary of mount options. Keys correspond to BuildKit option
            names such as `target`, `sharing`, `mode`, `uid`, etc. Values may be
            strings, integers, or booleans. Boolean values follow BuildKit
            semantics: a key is emitted without a value if it is `True`, and
            omitted entirely if `False`.
    """

    mount_type: str
    options: Dict[str, Scalar] = field(default_factory=dict)

    def to_flag(self) -> str:
        """
        Convert this mount specification into a Docker `--mount=` flag.

        Returns:
            str: The full `--mount=...` expression. Example:

                "--mount=type=cache,target=/root/.cache/go-build,sharing=locked"

        Notes:
            * Boolean options encode to flags without a value (e.g. `rw`, `readonly`).
            * Options set to `False` are omitted entirely.
        """
        parts: list[str] = [f"type={self.mount_type}"]
        for key, value in self.options.items():
            if isinstance(value, bool):
                # BuildKit behavior: boolean=True means emit bare key.
                if value:
                    parts.append(key)
            else:
                parts.append(f"{key}={value}")
        return "--mount=" + ",".join(parts)

    # Convenience constructors

    @classmethod
    def cache(
        cls,
        target: str,
        *,
        id_: str | None = None,
        ro: bool | None = None,
        readonly: bool | None = None,
        sharing: str | None = None,
        source: str | None = None,
        from_: str | None = None,
        mode: int | None = None,
        uid: int | None = None,
        gid: int | None = None,
    ) -> "RunMount":
        """
        Create a `type=cache` mount.

        Args:
            target (str):
                Target path inside the build container.

            id_ (str | None):
                Optional cache identifier. Defaults to the value of `target`
                when omitted.

            ro (bool | None):
                Whether the cache is mounted read-only. If True, emits `ro`.

            readonly (bool | None):
                Alternative read-only flag (BuildKit synonym for `ro`).

            sharing (str | None):
                One of `"shared"`, `"private"`, or `"locked"`.

            source (str | None):
                Subpath within the `from_` mount source.

            from_ (str | None):
                Build stage, context, or image name providing the cache base.

            mode (int | None):
                Filesystem mode applied to newly created cache directories.

            uid (int | None):
                User ID assigned to newly created directories.

            gid (int | None):
                Group ID assigned to newly created directories.

        Returns:
            RunMount: A mount specification for caching compiler/package-manager
            artifacts.

        Notes:
            Cache mounts persist between BuildKit invocations and should not
            affect build correctness.
        """
        opts: Dict[str, Scalar] = {"target": target}
        if id_ is not None:
            opts["id"] = id_
        if ro is not None:
            opts["ro"] = ro
        if readonly is not None:
            opts["readonly"] = readonly
        if sharing is not None:
            opts["sharing"] = sharing
        if source is not None:
            opts["source"] = source
        if from_ is not None:
            opts["from"] = from_
        if mode is not None:
            opts["mode"] = mode
        if uid is not None:
            opts["uid"] = uid
        if gid is not None:
            opts["gid"] = gid
        return cls("cache", opts)

    @classmethod
    def bind(
        cls,
        target: str,
        *,
        source: str | None = None,
        from_: str | None = None,
        rw: bool | None = None,
        readwrite: bool | None = None,
    ) -> "RunMount":
        """
        Create a `type=bind` mount.

        Args:
            target (str):
                Destination path inside the build container.

            source (str | None):
                Host or build-context path to bind-mount.

            from_ (str | None):
                Build stage/context/image providing the source root.

            rw (bool | None):
                Allows write access if True (default is read-only).

            readwrite (bool | None):
                Synonym for `rw`.

        Returns:
            RunMount: A bind mount specification.

        Notes:
            This mount type is read-only unless either `rw=True` or
            `readwrite=True` is provided.
        """
        opts: Dict[str, Scalar] = {"target": target}
        if source is not None:
            opts["source"] = source
        if from_ is not None:
            opts["from"] = from_
        if rw is not None:
            opts["rw"] = rw
        if readwrite is not None:
            opts["readwrite"] = readwrite
        return cls("bind", opts)

    @classmethod
    def tmpfs(cls, target: str, *, size: str | None = None) -> "RunMount":
        """
        Create a `type=tmpfs` in-memory mount.

        Args:
            target (str):
                Target path inside the build container.

            size (str | None):
                Optional size limit (e.g., `"100m"`).

        Returns:
            RunMount: A tmpfs mount specification.
        """
        opts: Dict[str, Scalar] = {"target": target}
        if size is not None:
            opts["size"] = size
        return cls("tmpfs", opts)

    @classmethod
    def secret(
        cls,
        *,
        id_: str,
        target: str | None = None,
        env: str | None = None,
        required: bool | None = None,
        mode: int | None = None,
        uid: int | None = None,
        gid: int | None = None,
    ) -> "RunMount":
        """
        Create a `type=secret` mount for accessing build-time secrets.

        Args:
            id_ (str):
                Identifier of the secret, matching the identifier passed via the
                Docker `--secret` build option.

            target (str | None):
                Filesystem path at which to mount the secret file. Defaults to
                `/run/secrets/<id>` if not provided.

            env (str | None):
                Environment variable name to expose the secret as (optional).

            required (bool | None):
                If True, the build fails when the secret is unavailable.

            mode (int | None):
                File mode to assign to the mounted secret file.

            uid (int | None):
                User ID for the mounted secret.

            gid (int | None):
                Group ID for the mounted secret.

        Returns:
            RunMount: A secret mount specification.

        Notes:
            Secrets do not end up in the final image and are only accessible
            during the build step that mounts them.
        """
        opts: Dict[str, Scalar] = {"id": id_}
        if target is not None:
            opts["target"] = target
        if env is not None:
            opts["env"] = env
        if required is not None:
            opts["required"] = required
        if mode is not None:
            opts["mode"] = mode
        if uid is not None:
            opts["uid"] = uid
        if gid is not None:
            opts["gid"] = gid
        return cls("secret", opts)

    @classmethod
    def ssh(
        cls,
        *,
        id_: str | None = None,
        target: str | None = None,
        required: bool | None = None,
        mode: int | None = None,
        uid: int | str | None = None,
        gid: int | str | None = None,
    ) -> "RunMount":
        """
        Create a `type=ssh` mount, enabling BuildKit to forward SSH agent
        credentials into the build.

        Args:
            id_ (str | None):
                Identifier of the SSH agent socket or key. Defaults to `"default"`
                if omitted, matching the standard `--ssh default=$SSH_AUTH_SOCK`
                invocation.

            target (str | None):
                Path inside the container where the SSH agent socket should be
                mounted. Defaults to `/run/buildkit/ssh_agent.<n>` if unset.

            required (bool | None):
                If True, raises a build error when the SSH agent/key is not
                provided by the client.

            mode (int | None):
                File mode assigned to the mounted socket.

            uid (int | str | None):
                User ID assigned to the socket.

            gid (int | str | None):
                Group ID assigned to the socket.

        Returns:
            RunMount: An SSH mount specification.

        Notes:
            SSH mounts enable secure checkout of private Git repositories during
            the build step. They do *not* persist into the final image.
        """
        opts: Dict[str, Scalar] = {}
        if id_ is not None:
            opts["id"] = id_
        if target is not None:
            opts["target"] = target
        if required is not None:
            opts["required"] = required
        if mode is not None:
            opts["mode"] = mode
        if uid is not None:
            opts["uid"] = uid
        if gid is not None:
            opts["gid"] = gid
        return cls("ssh", opts)
