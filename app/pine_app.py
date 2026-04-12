#!/usr/bin/env python3
"""Pine app scaffold for building toward a hobby OS project."""

from __future__ import annotations

import argparse
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
        print(package_hint(Path(args.config), args.format))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
