---
title: "pythainer: composable and reusable Docker builders and runners for reproducible research"
tags:
  - Python
  - Docker
  - reproducibility
  - software engineering
  - research tooling
  - system software
authors:
  - name: Antonio Paolillo
    orcid: 0000-0001-6608-6562
    # affiliation: 1
affiliations:
  - name: Software Languages Lab, Vrije Universiteit Brussel (VUB), Belgium
    # index: 1
    ror: 006e5kg04
date: 16 September 2025
bibliography: paper.bib
---

# Summary

Software experiments today often depend on complex Linux environments that
combine several toolchains, devices, and graphical interfaces. Many research
projects [@nvblox; @robotcore], for instance, need to
compose ROS 2 [@macenski2022ros2] with CUDA [@nvidiaCudaPg13], require non-root
users, provide GPU and GUI access, and must be reproducible across time and
machines. Docker [@docker] is a widely adopted substrate for packaging and
running such environments, and is widely used to improve reproducibility in
research software [@tani2020reproducible]. However, writing and maintaining
Dockerfiles and project-specific `docker run` scripts becomes a burden as
requirements grow.

`pythainer` raises the level of abstraction while remaining Docker-native. It
lets users describe images as small, testable Python *builders* that can be
composed (e.g., ROS 2 + CUDA ) and executed with reusable *runners* that capture
runtime policy (GPU, GUI, users, mounts). `pythainer` renders deterministic
Dockerfiles, builds standard images, and centralizes run
configuration—improving reuse and reducing duplication across repositories.

# Statement of need

Plain Dockerfiles are intentionally minimal: they offer sequential shell steps
but no first-class functions, loops, or composition. This is adequate for simple
images, yet it complicates reuse in research settings where environments must be
combined and parameterized. In particular, merging two existing images (e.g.,
community ROS 2 and NVIDIA CUDA) is not first-class; multi-stage builds help
trim artifacts but require intimate knowledge of which files, environment
variables, and paths must be copied and preserved. On the runtime side, real
projects often need non-root users, persistent volumes, access to GPUs and GUIs
(X11/Wayland), and device mappings. These concerns are typically maintained as
long shell scripts that are copy-pasted and diverge across projects.

`pythainer` addresses these pain points by adding a programmable front-end for
image construction and a reusable abstraction for execution policy. Builders are
Python objects and functions that support ordinary programming constructs
(conditionals, loops, parameters) and can be composed with a simple operator.
Runners encapsulate repeatable `docker run` policy, so launching a container is
a matter of selecting presets rather than rewriting long commands. The target
audience includes research groups and labs (robotics, vision, ML systems,
compilers, systems), instructors who need reliable student environments, and
continuous integration (CI) maintainers who prefer deterministic builds and
centralized run policy over ad-hoc scripts.

# Functionality

`pythainer` is a lightweight Python package and CLI that provides a
programmable front-end to Docker. Instead of writing raw Dockerfiles and shell
scripts, users compose images with builders and control runtime behavior with
runners. The library integrates naturally into Python workflows but remains
Docker-native: it renders deterministic Dockerfiles, builds them with the
Docker engine, and executes containers with reproducible runtime settings.
`pythainer` provides:

- **Builders (image construction).** A small API exposes common steps (e.g.,
  FROM/RUN/ENV/WORKDIR, package installs). Builders can be composed via an
  in-place operator to form larger images (e.g., ROS 2 + CUDA). Output
  rendering is deterministic, which simplifies testing and review. The tool
  remains Docker-native: it emits standard Dockerfiles and uses the Docker
  engine to build images [@docker].

- **Runners (execution policy).** A runner object assembles `docker run` flags
  for typical research needs: non-root user mapping, volumes, devices, GPUs, and
  GUI/X11 forwarding. Presets capture best practices (e.g., mapping the X socket
  and `DISPLAY`, requesting `--gpus all` with the expected environment
  variables), reducing duplication across repositories.

- **CLI.** A command-line interface provides two convenience commands:
  `scaffold` generates a starter Python script (builders + runners) and `run`
  composes and executes directly for one-offs.

- **Examples and tests.** The package ships small composition recipes (e.g.,
  LLVM/MLIR, QEMU, Rust) [@llvm; @mlir; @qemu]. Unit tests lock down Dockerfile
  rendering and CLI behavior; an opt-in integration test builds a tiny image to
  validate the end-to-end flow. Continuous integration runs tests and linters.

`pythainer` is designed to be naturally extensible: users can easily define
their own builders or runners, or build on top of those provided in the
library.

# Research applications

We have used `pythainer` to assemble environments for
(i) robotics experiments combining ROS 2 with CUDA toolchains [@shen2025sentryrt1; @itf24safebot];
(ii) compiler research that requires pinned LLVM toolchains [@degreef2025macros];
(iii) systems evaluations using QEMU built from source; and
(iv) GPU scheduling experiments where deterministic containerized environments
are required [@discepoli2025computeKernels].

In each case, the same small recipes are reused and composed across projects,
which shortens setup time and reduces configuration drift. Because `pythainer`
emits human-readable Dockerfiles, the resulting images remain transparent and
easy to audit, and the approach integrates well with existing Docker-centric CI.

# Relation to other work

`pythainer` complements the Docker ecosystem by adding a programmable composition
model on top of Dockerfiles. Unlike Docker Compose or the Docker SDK for Python,
which focus on orchestrating multi-service deployments or driving the daemon
[@docker_compose; @docker_sdk_python], `pythainer` focuses on single-image
construction and single-container execution policy. This makes it especially
suited for research projects where the goal is to provide a *single reproducible
environment* for experiments rather than a full service-oriented stack.

Compared with editor-centric templates such as VS Code devcontainers
[@devcontainers] or domain-specific generators such as repo2docker [@repo2docker],
`pythainer` treats environment recipes as code with tests and deterministic
rendering. Functional package managers such as Nix and Guix offer deep
system-level reproducibility but require adopting a different stack
[@nix04lisa; @courtes2013guix]; `pythainer` stays Docker-native for easier
adoption in labs and CI. Pragmatically, many third-party packages (e.g., CUDA and
ROS 2) are primarily supported on Ubuntu, so staying Docker-native with
Ubuntu-based images eases reproduction without changing the base distribution.

# Acknowledgements

We thank contributors for feedback and patches that improved early designs and
examples, including Attilio Discepoli, Yuwen Shen, Aaron Bogaert, and Samuel
Beesoon.

# References
