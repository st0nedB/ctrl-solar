from __future__ import annotations

import argparse
import logging

from ctrlsolar.app import run


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(prog="ctrlsolar")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument(
        "--config",
        default="example/config.yaml",
        help="Path to YAML config file",
    )

    args = parser.parse_args(argv)
    if args.command == "run":
        run(args.config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
