#!/usr/bin/env python3

from pythainer.builders import UbuntuDockerBuilder
from pythainer.examples.builders import (
    get_user_builder,
    qemu_builder,
    qemu_dependencies,
)


def get_qemu_builder(
    image_name: str,
    user_name: str,
    work_dir: str,
    base_ubuntu_image: str = "ubuntu:24.04",
    qemu_version: str = "10.0.2",
) -> UbuntuDockerBuilder:
    qemu_packages = qemu_dependencies()

    builder = get_user_builder(
        image_name=image_name,
        base_ubuntu_image=base_ubuntu_image,
        user_name=user_name,
        lib_dir=f"{work_dir}/libraries",
        packages=qemu_packages,
    )

    builder.user()
    builder.workdir(path=work_dir)
    builder.space()

    builder.desc(f"Build & Install QEMU v{qemu_version} from source")
    builder |= qemu_builder(version=qemu_version, cleanup=False)

    builder.space()
    builder.workdir(path=work_dir)

    return builder


def main():
    user_name = "user"
    dock_work_dir = f"/home/{user_name}/workspace"

    builder = get_qemu_builder(
        image_name="qemuer",
        user_name="user",
        work_dir=dock_work_dir,
    )
    builder.build()

    runner = builder.get_runner()

    cmd = runner.get_command()
    print(" ".join(cmd))
    runner.generate_script()

    runner.run()


if __name__ == "__main__":
    main()
