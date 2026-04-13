#!/usr/bin/env python3
"""Pine app scaffold for building toward a hobby OS project."""

from __future__ import annotations

import argparse

import gzip
import io
import json
import tarfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

import json
from dataclasses import asdict, dataclass

from pathlib import Path


SUPPORTED_TARGETS = {
    "desktop": "General x86_64 development target",
    "rpi5": "Raspberry Pi 5 target (experimental starter profile)",
}


@dataclass
class ProjectConfig:
    name: str
    target: str
    app_version: str = "0.1.0"
    next_steps: tuple[str, ...] = (
        "Build user-facing app features first",
        "Add update mechanism",
        "Prepare hardware abstraction layer",
        "Split branches for target-specific support (desktop, rpi5)",
    )

    @classmethod
    def from_path(cls, path: Path) -> "ProjectConfig":
        payload = json.loads(path.read_text())
        payload["next_steps"] = tuple(payload.get("next_steps", ()))
        return cls(**payload)

    def to_json(self) -> str:
        body = asdict(self)
        body["next_steps"] = list(self.next_steps)
        return json.dumps(body, indent=2)


def _pad_4(data: bytes) -> bytes:
    pad = (4 - (len(data) % 4)) % 4
    return data + (b"\x00" * pad)


def _cpio_header(name: bytes, mode: int, size: int, mtime: int) -> bytes:
    namesize = len(name) + 1
    fields = [
        "070701",
        f"{0:08x}",
        f"{mode:08x}",
        f"{0:08x}",
        f"{0:08x}",
        f"{1:08x}",
        f"{mtime:08x}",
        f"{size:08x}",
        f"{0:08x}",
        f"{0:08x}",
        f"{0:08x}",
        f"{0:08x}",
        f"{namesize:08x}",
        f"{0:08x}",
    ]
    return "".join(fields).encode("ascii")


def _build_cpio_newc(files: dict[str, tuple[bytes, bool]]) -> bytes:
    blob = io.BytesIO()
    mtime = int(datetime.now(tz=timezone.utc).timestamp())

    for path, (payload, executable) in files.items():
        mode = 0o100755 if executable else 0o100644
        name = path.encode("utf-8")
        blob.write(_cpio_header(name, mode, len(payload), mtime))
        blob.write(_pad_4(name + b"\x00"))
        blob.write(_pad_4(payload))

    trailer = b"TRAILER!!!"
    blob.write(_cpio_header(trailer, 0, 0, mtime))
    blob.write(_pad_4(trailer + b"\x00"))
    return blob.getvalue()


def _write_ar_archive(output: Path, members: list[tuple[str, bytes]]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as fp:
        fp.write(b"!<arch>\n")
        now = int(datetime.now(tz=timezone.utc).timestamp())
        for name, payload in members:
            member_name = f"{name}/".encode("utf-8")
            header = (
                member_name.ljust(16, b" ")
                + str(now).encode().ljust(12, b" ")
                + b"0".ljust(6, b" ")
                + b"0".ljust(6, b" ")
                + b"100644".ljust(8, b" ")
                + str(len(payload)).encode().ljust(10, b" ")
                + b"`\n"
            )
            fp.write(header)
            fp.write(payload)
            if len(payload) % 2:
                fp.write(b"\n")


def _build_tar_gz(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for name, payload in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            info.mtime = int(datetime.now(tz=timezone.utc).timestamp())
            info.mode = 0o644
            tar.addfile(info, io.BytesIO(payload))
    return buffer.getvalue()


def create_deb_package(config: ProjectConfig, output_dir: Path) -> Path:
    deb_name = f"{config.name}_{config.app_version}_all.deb"
    out_path = output_dir / deb_name

    control = (
        f"Package: {config.name}\n"
        f"Version: {config.app_version}\n"
        "Section: utils\n"
        "Priority: optional\n"
        "Architecture: all\n"
        "Maintainer: Pine OS Team <pine@example.com>\n"
        f"Description: {config.name} app-first release artifact\n"
    ).encode("utf-8")

    control_tar = _build_tar_gz({"./control": control})

    app_readme = (
        f"{config.name}\n"
        f"Target: {config.target}\n"
        "This package is the app layer release while OS image support evolves.\n"
    ).encode("utf-8")
    data_tar = _build_tar_gz({f"./usr/share/{config.name}/README.txt": app_readme})

    members = [
        ("debian-binary", b"2.0\n"),
        ("control.tar.gz", control_tar),
        ("data.tar.gz", data_tar),
    ]
    _write_ar_archive(out_path, members)
    return out_path


def create_rpi5_bootkit(config: ProjectConfig, output_dir: Path) -> Path:
    stamp = f"{config.name}-{config.app_version}-rpi5-bootkit"
    root = output_dir / stamp
    boot = root / "boot"
    rootfs = root / "rootfs"
    root.mkdir(parents=True, exist_ok=True)
    boot.mkdir(parents=True, exist_ok=True)
    rootfs.mkdir(parents=True, exist_ok=True)

    (boot / "config.txt").write_text(
        "arm_64bit=1\n"
        "kernel=kernel_2712.img\n"
        "enable_uart=1\n"
        "uart_2ndstage=1\n"
    )
    (boot / "cmdline.txt").write_text(
        "console=serial0,115200 console=tty1 root=/dev/ram0 rw rdinit=/init\n"
    )
    (boot / "kernel_2712.img").write_text(
        "Placeholder kernel image. Replace with real AArch64 kernel for boot testing.\n"
    )

    init_script = (
        "#!/bin/sh\n"
        "mount -t proc proc /proc\n"
        "mount -t sysfs sys /sys\n"
        "echo 'Pine OS initramfs boot milestone reached on serial console.'\n"
        "exec sh\n"
    ).encode("utf-8")
    release_txt = (
        f"NAME={config.name}\nVERSION={config.app_version}\nTARGET=rpi5\n"
    ).encode("utf-8")

    cpio = _build_cpio_newc(
        {
            "init": (init_script, True),
            "etc/pine-release": (release_txt, False),
        }
    )
    with gzip.open(boot / "initramfs.cpio.gz", "wb") as gz:
        gz.write(cpio)

    (root / "FLASH_INSTRUCTIONS.txt").write_text(
        "1. Copy boot/* onto the Pi boot partition (FAT32).\n"
        "2. Ensure kernel_2712.img is replaced with a real RPi5-compatible kernel.\n"
        "3. Use serial console at 115200 baud to observe boot logs.\n"
        "4. This milestone validates boot plumbing; full Pine OS userspace is next.\n"
    )

    return root


def create_rpi5_image_bundle(config: ProjectConfig, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle = output_dir / f"{config.name}-{config.app_version}-rpi5.img"

    readme = (
        "Pine OS Raspberry Pi 5 image scaffold\n"
        "----------------------------------\n"
        "This is a starter image placeholder for early bring-up.\n"
        "It is not yet a fully bootable operating system image.\n"
        "Use this artifact to verify release plumbing and SD-card workflow.\n"
    ).encode("utf-8")

    with bundle.open("wb") as fp:
        fp.write(readme)
        fp.write(b"\n")
        fp.write(json.dumps(asdict(config), indent=2).encode("utf-8"))
    return bundle



def create_project(name: str, target: str, directory: Path) -> Path:
    if target not in SUPPORTED_TARGETS:
        raise ValueError(f"Unsupported target '{target}'.")

    directory.mkdir(parents=True, exist_ok=True)
    config_path = directory / "pine.json"

    config = ProjectConfig(name=name, target=target)
    config_path.write_text(config.to_json() + "\n")

    readme = directory / "README.md"
    readme.write_text(
        f"# {name}\n\n"
        f"Target: **{target}** ({SUPPORTED_TARGETS[target]})\n\n"
        "## Purpose\n"
        "Build the application layer first, then expand into low-level OS support.\n"
    )

    return config_path


def status(config_path: Path) -> str:
    config = ProjectConfig.from_path(config_path)
    header = f"Project '{config.name}' [{config.app_version}] targeting: {config.target}"
    steps = "\n".join(f"  {i + 1}. {step}" for i, step in enumerate(config.next_steps))
    return f"{header}\nRoadmap:\n{steps}"


def package_hint(config_path: Path, package_format: str, output_dir: Path) -> str:
    config = ProjectConfig.from_path(config_path)

    if package_format == "exe":
        out = output_dir / f"{config.name}-{config.app_version}-windows.exe"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            "Windows .exe artifacts are built in GitHub Actions release workflow.\n"
            "This local file is a marker so you can verify release asset naming.\n"
        )
        return f"Created release marker: {out}"

    if package_format == "deb":
        path = create_deb_package(config, output_dir)
        return f"Created Debian package: {path}"

def package_hint(config_path: Path, package_format: str) -> str:
    config = ProjectConfig.from_path(config_path)

    if package_format == "exe":
        return (
            f"{config.name}: prepare a Windows installer (.exe) for your app layer now.\n"
            "Tip: Use PyInstaller + Inno Setup for distribution."
        )

    if package_format == "deb":
        return (
            f"{config.name}: prepare a Debian package (.deb) for your app layer now.\n"
            "Tip: Add debian/control and build with dpkg-deb or debuild."
        )


    raise ValueError("Format must be 'exe' or 'deb'.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pine app starter CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    new_cmd = sub.add_parser("new", help="Create a new app-first project")
    new_cmd.add_argument("name", help="Project name")
    new_cmd.add_argument("--target", default="desktop", choices=tuple(SUPPORTED_TARGETS))
    new_cmd.add_argument("--dir", default=".", help="Directory to create project in")

    status_cmd = sub.add_parser("status", help="Show project roadmap")
    status_cmd.add_argument("--config", default="pine.json", help="Path to pine.json")


    pack_cmd = sub.add_parser("package", help="Create release artifacts")
    pack_cmd.add_argument("--config", default="pine.json", help="Path to pine.json")
    pack_cmd.add_argument("--format", choices=("exe", "deb"), required=True)
    pack_cmd.add_argument("--out", default="dist", help="Output directory")

    rpi_cmd = sub.add_parser("rpi5-image", help="Create RPi5 image scaffold artifact")
    rpi_cmd.add_argument("--config", default="pine.json", help="Path to pine.json")
    rpi_cmd.add_argument("--out", default="dist", help="Output directory")

    bootkit_cmd = sub.add_parser("rpi5-bootkit", help="Create RPi5 boot milestone assets")
    bootkit_cmd.add_argument("--config", default="pine.json", help="Path to pine.json")
    bootkit_cmd.add_argument("--out", default="dist", help="Output directory")

    pack_cmd = sub.add_parser("package", help="Show packaging hints")
    pack_cmd.add_argument("--config", default="pine.json", help="Path to pine.json")
    pack_cmd.add_argument("--format", choices=("exe", "deb"), required=True)


    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "new":
        root = Path(args.dir).resolve() / args.name
        config_path = create_project(args.name, args.target, root)
        print(f"Created {config_path}")
        return 0

    if args.command == "status":
        print(status(Path(args.config)))
        return 0

    if args.command == "package":

        print(package_hint(Path(args.config), args.format, Path(args.out)))
        return 0

    if args.command == "rpi5-image":
        config = ProjectConfig.from_path(Path(args.config))
        image = create_rpi5_image_bundle(config, Path(args.out))
        print(f"Created RPi5 image scaffold: {image}")
        return 0

    if args.command == "rpi5-bootkit":
        config = ProjectConfig.from_path(Path(args.config))
        root = create_rpi5_bootkit(config, Path(args.out))
        print(f"Created RPi5 bootkit scaffold: {root}")

        print(package_hint(Path(args.config), args.format))

        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
