"""Validate events.jsonl or dataset.jsonl files."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from state2action_vision.config.schemas import get_json_schema, parse_dataset_record, parse_event_record
from state2action_vision.dataset.io import read_jsonl

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
        "--schema",
        choices=["events", "dataset"],
        help="Print the JSON schema for the selected kind and exit.",
    )
    parser.add_argument(
        "--schema-out",
        type=Path,
        help="Write the JSON schema to a file (requires --schema).",
    )
    return parser


def _validate_file(path: Path, kind: str) -> bool:
    parser = parse_event_record if kind == "events" else parse_dataset_record
    try:
        read_jsonl(path, parser)
    except ValueError as exc:
        logger.error("validation_failed", extra={"path": str(path), "error": str(exc)})
        return False
    logger.info("validation_success", extra={"path": str(path), "kind": kind})
    return True


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.schema_out is not None and args.schema is None:
        parser.error("--schema-out requires --schema.")

    if args.schema is not None:
        schema = get_json_schema(args.schema)
        schema_payload = json.dumps(schema, ensure_ascii=False, indent=2)
        if args.schema_out is not None:
            args.schema_out.parent.mkdir(parents=True, exist_ok=True)
            args.schema_out.write_text(schema_payload + "\n", encoding="utf-8")
            logger.info("schema_written", extra={"path": str(args.schema_out), "kind": args.schema})
        else:
            print(schema_payload)
        if args.events is None and args.dataset is None:
            return 0

    if args.events is None and args.dataset is None:
        parser.error("At least one of --events or --dataset is required.")

    results = []
    if args.events is not None:
        results.append(_validate_file(args.events, "events"))
    if args.dataset is not None:
        results.append(_validate_file(args.dataset, "dataset"))

    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
