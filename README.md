# Pythainer

Pythainer is an open-source Python package designed to facilitate the creation,
management, composition and deployment of Docker containers for various use
cases, with a focus on ease of use and automation.

## Features

- **Docker Image Building**: Simplify Docker image construction with
  pre-defined Python scripts.
- **Project Examples**: Includes examples for building, installing, and
  running applications within Docker containers.
- **Extensible**: Easily extendable to include more features or adapt
  existing ones to different environments or requirements.

## Getting Started

### Prerequisites

- Python 3.10 or later
- [Docker](https://docs.docker.com/engine/install/)

### Installation

To get started with Pythainer, clone this repository and set up a virtual
environment:

```bash
git clone https://github.com/apaolillo/pythainer.git
cd pythainer
./scripts/install_venv.sh
```

### Usage

Here is a simple example of how to use Pythainer to build a Docker container:

```python3
from pythainer.examples.builders import get_user_builder
from pythainer.runners import ConcreteDockerRunner

image_name = "pythainertest"
builder = get_user_builder(image_name=image_name, base_ubuntu_image="ubuntu:22.04")
builder.root()
builder.add_packages(packages=["vim", "git", "tmux"])
builder.user("${USER_NAME}")
runner = ConcreteDockerRunner(image=image_name)

builder.build()
runner.run()
```

## High-level source organization

The source code of this repository is organized as follows:
```
pythainer
├── pythainer           Core package containing all the essential modules for the framework.
│   ├── builders        Modules responsible for building Docker images through automated scripts.
│   │   ├── cmds.py     Defines command classes that translate high-level actions into Dockerfile commands.
│   │   └── utils.py    Provides utility functions supporting Docker image construction.
│   ├── examples        Contains various examples demonstrating the use of Pythainer components.
│   │   ├── builders    Examples showcasing how to use the builders module to create Docker images.
│   │   ├── installs    Examples demonstrating how to handle software installations inside Docker containers.
│   │   └── runners     Examples illustrating how to execute and manage Docker containers for specific tasks.
│   ├── runners         Contains utilities for running Docker containers.
│   └── sysutils.py     Provides system utilities such as shell command execution and directory management.
└── scripts             Directory containing scripts that facilitate development and operational tasks.
```

## Contributing

Contributions to Pythainer are welcome! If you have suggestions for
improvements  or new features, please open an issue or submit a pull request.

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on the process.

## Roadmap

Check out the [ROADMAP.md](ROADMAP.md) file to see the plans for future
releases.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE)
file for details.

## Maintainers

For major changes and guidance, the list of active maintainers is available in
the [MAINTAINERS](MAINTAINERS) file.

## Support

For support, raise an issue in the GitHub issue tracker.
