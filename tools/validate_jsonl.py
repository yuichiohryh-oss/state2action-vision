"""Validate events.jsonl or dataset.jsonl files."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from state2action_vision.config.schemas import parse_dataset_record, parse_event_record
from state2action_vision.dataset.io import validate_jsonl

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate JSONL records for events or datasets.")
    parser.add_argument(
        "--events",
        type=Path,
        help="Path to events.jsonl to validate.",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        help="Path to dataset.jsonl to validate.",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=None,
        help="Stop after this many errors (default: no limit).",
    )
    return parser


def _validate_file(path: Path, kind: str, max_errors: int | None) -> bool:
    parser = parse_event_record if kind == "events" else parse_dataset_record
    report = validate_jsonl(path, parser, max_errors=max_errors)
    for issue in report.issues:
        logger.error(
            "validation_issue",
            extra={
                "path": str(path),
                "line": issue.line_number,
                "error": issue.message,
            },
        )
    logger.info(
        "validation_summary",
        extra={
            "path": str(path),
            "kind": kind,
            "total": report.total,
            "valid": report.valid,
            "errors": len(report.issues),
        },
    )
    return len(report.issues) == 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.events is None and args.dataset is None:
        parser.error("At least one of --events or --dataset is required.")

    results = []
    if args.events is not None:
        results.append(_validate_file(args.events, "events", args.max_errors))
    if args.dataset is not None:
        results.append(_validate_file(args.dataset, "dataset", args.max_errors))

    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
