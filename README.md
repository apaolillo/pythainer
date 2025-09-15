# Pythainer: programmable, composable Docker builders and runners

[![PyPI - Version](https://img.shields.io/pypi/v/pythainer)](https://pypi.org/project/pythainer)
![Python >=3.10](https://img.shields.io/badge/python-%E2%89%A53.10-blue)
[![Wheel](https://img.shields.io/pypi/wheel/pythainer)](https://pypi.org/project/pythainer)
[![License](https://img.shields.io/github/license/apaolillo/pythainer)](LICENSE)

[![Lint](https://github.com/apaolillo/pythainer/actions/workflows/codefmt.yml/badge.svg)](https://github.com/apaolillo/pythainer/actions/workflows/codefmt.yml)
[![Tests](https://github.com/apaolillo/pythainer/actions/workflows/tests.yml/badge.svg)](https://github.com/apaolillo/pythainer/actions/workflows/tests.yml)

[![Downloads](https://static.pepy.tech/badge/pythainer)](https://pepy.tech/project/pythainer)
[![GitHub stars](https://img.shields.io/github/stars/apaolillo/pythainer)](https://github.com/apaolillo/pythainer/stargazers)

[![Formatter: black](https://img.shields.io/badge/formatter-black-000000)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/imports-isort-ef8336)](https://pycqa.github.io/isort/)
[![Lint: flake8](https://img.shields.io/badge/lint-flake8-2b8cbe)](https://flake8.pycqa.org/)
[![Lint: pylint](https://img.shields.io/badge/lint-pylint-4E9A06)](https://pylint.readthedocs.io/)
[![Lint: ruff](https://img.shields.io/badge/lint-ruff-46a2f1)](https://github.com/astral-sh/ruff)

Pythainer is an open-source Python package designed to facilitate the creation,
management, composition, and deployment of Docker containers for various use
cases, with a focus on ease of use and automation.

Pythainer lets you describe Docker images as small, testable Python "builders"
you can compose like Lego bricks. That means you can factor common recipes
(e.g., toolchains, ROS 2, CUDA, QEMU, Rust) and reuse them across projects
while keeping your runtime concerns (GPU access, GUI forwarding, volumes) out
of your application code.

---

## Why Pythainer?

Docker is an excellent packaging and distribution format, but its build
language is deliberately minimal. A Dockerfile is a linear script: no
functions, no loops, no conditionals beyond shell tricks. That’s fine for
small images, yet it becomes a constraint when you’re trying to assemble
**reusable, research-grade environments** that must be composed, parameterized,
and maintained over time.

Two issues follow from this. First, **composition is not a first-class idea**
in Docker. You cannot "merge" two existing images—say, the community ROS 2
image and an NVIDIA CUDA image—and get a combined environment. The usual
workaround is to start from one base and then partially re-implement the other,
or attempt a multi-stage build that requires you to know exactly which files to
copy, where they live, which runtime artifacts are safe to omit, and the
precise environment variables they rely on (e.g., `PATH`, `LD_LIBRARY_PATH`,
`PKG_CONFIG_PATH`, `ROS_DISTRO`, `CUDA_HOME`). This quickly erodes reuse:
every project rediscovers the same steps, and any fix must be repeated in many
places.

Second, **runtime concerns** are often entangled with application code and
shell scripts. Real projects need non-root users, persistent mounts, access to
GPUs, GUI forwarding (X11/Wayland), devices, and project-specific environment
variables. The resulting `docker run` commands grow long and fragile, are
copied across repositories, and drift as requirements change. In fast-moving
research, this duplication is costly.

**Pythainer** raises the level of abstraction while still targeting Docker as
the execution engine. Instead of hand-authoring Dockerfiles, you describe
images with small, testable **builders**: Python classes and functions that can
use conditionals, loops, parameters, and ordinary refactoring. Builders can be
**composed** into larger units (e.g., ROS 2 + CUDA + QEMU), encouraging teams
to factor out common recipes for important toolchains (e.g., LLVM, Vulkan,
OpenCL, OpenCV, ...) and reuse them across projects. Pythainer then renders
deterministic Dockerfiles and builds the resulting images, so what you ship is
transparent and reproducible.

On the runtime side, **runners** capture operational policy—users and groups,
mounts, GPU and GUI setup, device access—so that launching a container is a
matter of selecting the right presets rather than rewriting long shell
commands. This keeps project code clean and centralizes changes: update a
runner once, and every consumer benefits.

In short, Docker gives you the substrate; **Pythainer gives you the
programming model**. By separating environment construction (builders) from
execution policy (runners), and by making composition a first-class capability,
it becomes practical to define stable, shareable environments for experiments
and to reproduce them reliably across machines, projects, and time.

---

## In short

Writing and maintaining Dockerfiles for research projects gets messy fast:
repeated steps, hard-to-parameterize files, copy-pasted base images, and
bespoke run scripts for GPUs/GUI. Pythainer gives you:

- **Programmable builders**: define images in Python (with types & tests), not
  ad-hoc Dockerfiles.
- **Composable recipes**: reuse and combine partial builders into
  project-specific images.
- **Deterministic output**: stable Dockerfile rendering for reproducibility.
- **Clean runtime**: reusable runners for GPU (`--gpus`), GUI (X11), volumes,
  users, etc.
- **CLI scaffold**: generate a ready-to-run build+run script from a couple of
  flags.

---

## Installation

**Requirements**
- Python **3.10+**
- Docker Engine (BuildKit recommended)
- *(Optional, for GPU)* NVIDIA driver + **nvidia-container-toolkit**

**Install Docker**

Follow the official instructions:
<https://docs.docker.com/engine/install/>

**Install NVIDIA container toolkit (optional)**

Follow NVIDIA’s guide:
<https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html>

**Install the pythainer package**

From PyPI:
```bash
pip3 install pythainer
```

From source (editable, in a venv):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install --upgrade pip
git clone https://github.com/apaolillo/pythainer.git
pip3 install -e pythainer/
```

---

## Quick start

In `quickstart.py`, build a small Ubuntu-based image pre-configured with a
user, add some packages, and run it:

```python
from pythainer.examples.builders import get_user_builder
from pythainer.runners import ConcreteDockerRunner

image = "pythainer-quickstart"
builder = get_user_builder(image_name=image, base_ubuntu_image="ubuntu:24.04")
builder.root()
builder.add_packages(["vim", "git", "tmux"])
builder.user("${USER_NAME}")  # switch back to non-root
builder.workdir(path="/home/${USER_NAME}/workspace")
builder.build()

runner = ConcreteDockerRunner(image=image, name="pythainer-quickstart")
runner.run()
```

Run it:

```bash
python quickstart.py
```

You should see a user-space Ubuntu terminal with the desired packages. You can
inspect the generated Dockerfile at `/tmp/Dockerfile` (default path).

---

## Composable recipes

A core idea is that **partial builders** can be combined with `|=` to make
bigger images.

For example, you can combine existing building blocks (QEMU + Rust), or your
own:

```python
from pythainer.examples.builders import get_user_builder, rust_builder, qemu_builder

image = "devtools"
b = get_user_builder(image_name=image, base_ubuntu_image="ubuntu:24.04")
b |= rust_builder()  # add a Rust toolchain
b |= qemu_builder(version="10.0.2", cleanup=False)  # add QEMU from source
b.build()
```

Starting a runner from this builder will give a container environment where
both Rust and QEMU v10.0.2 are installed.

You can apply the same pattern to, for example, **ROS 2** and **CUDA**: write
(or reuse) two small recipes `ros2_builder()` and `cuda_builder()`, then
compose:

```python
# These recipes are not (yet) provided by Pythainer; example only.
from my_recipes import ros2_builder, cuda_builder

image = "ros2-cuda"
b = get_user_builder(image_name=image, base_ubuntu_image="ubuntu:24.04")
b |= ros2_builder(distro="humble")   # set up ROS 2 repos + packages
b |= cuda_builder(cuda="12.4")       # pin CUDA toolkit/driver userspace
b.build()
```

This keeps each concern small, testable, and reusable.

---

## Clean runtime: GPUs, GUIs, volumes

Stop rewriting `docker run` flags in every project—use **runners**:

```python
from pythainer.examples.runners import gpu_runner, gui_runner
from pythainer.runners import ConcreteDockerRunner

runner = ConcreteDockerRunner(image="ros2-cuda", name="ros2-cuda-dev")

# Add GPU support (maps to --gpus=all + needed env/devices)
runner |= gpu_runner()

# Add GUI/X11 support (mounts X socket, passes DISPLAY)
runner |= gui_runner()

runner.run()
```

> GPU support requires NVIDIA drivers + `nvidia-container-toolkit` on the host.
> Try `xeyes` (GUI) and `nvidia-smi` (GPU) from inside the container.

---

## CLI scaffold (generate a script)

Prefer a quick script to start from? Use the CLI **scaffold**:

```bash
pythainer scaffold \
  --image devtools \
  --builders=rust,qemu \
  --runners=gpu,gui \
  --output ./scaffold.py

python ./scaffold.py
```

The generated script includes clean docstrings, type hints, and the composition
you requested. It’s a good starting point to develop a Pythainer environment
for a new project.

---

## CLI run (build & run directly)

If you don’t need a script yet, use the **`run`** subcommand to compose
builders/runners and execute immediately. It builds the image and starts the
container with the requested capabilities.

```bash
pythainer run \
  --image devtools \
  --builders=rust,qemu \
  --runners=gpu,gui
```

Notes:

* **GPU** requires NVIDIA drivers + `nvidia-container-toolkit` on the host.
* **GUI** runner mounts the X socket and forwards `DISPLAY`.
* Prefer `scaffold` if you want a versioned script you can commit and tweak
  over time; use `run` for quick, one-shot environments.

---

## Examples

Browse the examples and adapt them:

* **Full examples**: [`examples/`](examples/)

  * QEMU from source: [`examples/qemu_container.py`](examples/qemu_container.py)
  * LLVM/MLIR toolchain: [`examples/llvm_container.py`](examples/llvm_container.py)
* **Builders**: see [`src/pythainer/examples/builders/`](src/pythainer/examples/builders/)
* **Runners**: see [`src/pythainer/examples/runners/`](src/pythainer/examples/runners/)

---

## High-level source organization

The source code of this repository is organized as follows:

```
pythainer/
├── examples                Standalone runnable examples (e.g., llvm_container.py, qemu_container.py).
├── scripts                 Directory containing scripts that facilitate development and operational tasks.
├── src
│   └── pythainer           Core package containing all the essential modules for the framework.
│       ├── builders        Modules responsible for building Docker images through automated scripts.
│       │   ├── cmds.py     Defines command classes that translate high-level actions into Dockerfile commands.
│       │   └── utils.py    Provides utility functions supporting Docker image construction.
│       ├── cli.py          Click-based CLI entry point (group `pythainer`); subcommands like `scaffold` and `run`.
│       ├── examples        Contains various examples demonstrating the use of Pythainer components.
│       │   ├── builders    Examples showcasing how to use the builders module to create Docker images.
│       │   ├── installs    Examples demonstrating how to handle software installations inside Docker containers.
│       │   └── runners     Examples illustrating how to execute and manage Docker containers for specific tasks.
│       ├── runners         Contains utilities for running Docker containers; composition-ready presets (GPU/GUI/volumes).
│       └── sysutils.py     Provides system utilities such as shell command execution and directory management.
└── tests
    ├── golden              Snapshot/expected outputs used by unit tests (e.g., scaffold.py).
    ├── integration         Docker-gated tests (require engine); opt-in via `-m integration`.
    └── unit                Fast deterministic tests (no Docker); rendering and CLI behavior.
```

---

## Testing

Run locally:

```bash
pip install -e ".[test]"
pytest -q -m "not integration"
# Optional, requires Docker:
PYTHAINER_INTEGRATION=1 pytest -q -m integration
```

Or run all tests:

```bash
pytest .
```

---

## Contributing

Contributions are welcome! If you have suggestions for improvements or new
features, please open an issue or submit a pull request.

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on the process. By
contributing, you agree to the MIT license.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE)
file for details.

---

## Maintainers

For major changes and guidance, the list of active maintainers is available in
the [MAINTAINERS](MAINTAINERS) file.

---

## Support

For support, raise an issue in the GitHub issue tracker.
