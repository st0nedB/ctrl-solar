from __future__ import annotations

import argparse
import logging

from rich.logging import RichHandler

from ctrlsolar.app import run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ctrlsolar")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run the controller loop")
    run_parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to the application config file.",
    )
    return parser


def configure_logging() -> None:
    logging.basicConfig(
        level="INFO",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(show_time=True, show_level=True, show_path=False)],
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging()

    if args.command is None:
        run("config.yaml")
        return 0

    if args.command == "run":
        run(args.config)
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2
