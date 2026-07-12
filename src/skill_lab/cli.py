"""Command-line entry point for Skill Lab."""

import argparse
from collections.abc import Sequence
from typing import NoReturn

from skill_lab import __version__
from skill_lab.app import SkillLabApp


def run(argv: Sequence[str] | None = None) -> int:
    """Run Skill Lab with explicit non-interactive diagnostic modes."""
    parser = argparse.ArgumentParser(prog="skilllab")
    parser.add_argument("--version", action="store_true")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args(argv)

    if args.version:
        print(f"skilllab {__version__}")
        return 0

    if args.smoke_test:
        SkillLabApp()
        print("Skill Lab app constructed successfully")
        return 0

    SkillLabApp().run()
    return 0


def main() -> NoReturn:
    """Console script entry point."""
    raise SystemExit(run())
