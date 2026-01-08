# Changelog

All notable changes to pythainer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.6] - 2026-01-08

### Added

- Docker build enhancements:
  - Proper `COPY` support via a staged build context (`builder.copy()`).
  - Support for `RUN --mount` clauses (BuildKit), including SSH agent forwarding.
- Pythainer examples:
  - QEMU example updated with `libslirp` dependency for reliable networking.
  - Minimal integration of Intel VTune within containers.
- Nix support, enabling reproducible builds and development environments.

### Changed

- User handling during Docker builds:
  - More robust deletion of users by UID instead of UID:GID.
  - Avoid passing UID/GID equal to 0 to Docker builds.
- Documentation:
  - Significant README improvements following JOSS review feedback.
  - Added JOSS paper sources under `doc/joss25/`.

## [0.0.5] - 2025-09-15

### Added

- CLI: new `pythainer` command with:
  - `run` to compose builders/runners and execute directly.
  - `scaffold` to generate a build+run Python script (formatted with black/isort).
- Builders:
  - New QEMU builder.
  - New Rust builder (with optional `nightly=True`).
  - NVIDIA Nsight install helper.
  - Package installer helpers: .deb, TensorRT, cuDNN.
  - Support for `unminimize` on Ubuntu 24.
  - Configurable local path for `git clone`.
- Composition:
  - In-place OR operator `|=` to compose partial builders.
- Runners:
  - Personal runner improvements (dotfiles, optional shell history preservation).
  - Ability to run shell commands before entering the interactive session.
- QEMU builder:
  - Customizable configure flags via `enables`/`disables`.
  - Default user-mode networking enabled (`--enable-slirp`).
- CI/CD:
  - New `tests.yml` workflow (Python matrix) and Docker-gated integration job.
  - Separate lint/check workflow (codefmt).
  - Added Ruff and mypy into checks; extras `[test]` and `[dev]` for local/CI parity.
- Tests:
  - Typed unit tests for deterministic Dockerfile rendering and CLI behavior.
  - Integration smoke test building a tiny Alpine image.
  - Additional LLVM container test.
- Docs:
  - README overhaul (motivation, installation, examples, runners, CLI, badges).
  - ROADMAP updated.
  - Moved runnable example scripts into `examples/` (LLVM/MLIR, QEMU).

### Changed

- Public API: expose Click command group as `cli` (keep `main` as entry-point alias).
- Builders/utils: more generic CMake handling and extra CMake options for example installers.
- Linting/formatting: address warnings and formatting issues across the codebase.

### Fixed

- macOS: detect Docker path reliably when `docker` is not in the default PATH.
- Builders: fix bug in `unminimize`.
- Examples: realSense build/container fixes.
- Dockerfile COPY: minor follow-up fixes after introducing COPY support.

## [0.0.4] - 2024-07-30

- Add example libs: librealsense and OpenCV

## [0.0.3] - 2024-06-15

- Option in docker builders to use or not the docker buildkit;
- Optional passing of UID/GID for the docker user;
- Method to get a concrete docker runner from docker builder;
- DockerfileDockerBuilder: new kind of docker builder that builds the image from a given dockerfile.

## [0.0.2] - 2024-04-25

Updated example in README.

## [0.0.1] - 2024-04-25

Initial release.
