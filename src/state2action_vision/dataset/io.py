"""JSONL IO utilities for datasets."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
import json
import logging
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass(frozen=True)
class JsonlValidationIssue:
    line_number: int
    message: str


@dataclass(frozen=True)
class JsonlValidationReport:
    total: int
    valid: int
    issues: list[JsonlValidationIssue]


def read_jsonl(path: str | Path, parser: Callable[[Mapping[str, Any]], T]) -> list[T]:
    """Read a jsonl file and parse each line with the provided parser."""

    file_path = Path(path)
    records: list[T] = []
    with file_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} in {file_path}") from exc
            if not isinstance(payload, Mapping):
                raise ValueError(f"Line {line_number} in {file_path} must be a JSON object")
            try:
                records.append(parser(payload))
            except ValueError as exc:
                raise ValueError(
                    f"Invalid record on line {line_number} in {file_path}: {exc}"
                ) from exc
    logger.info("read_jsonl", extra={"path": str(file_path), "count": len(records)})
    return records


def validate_jsonl(
    path: str | Path,
    parser: Callable[[Mapping[str, Any]], T],
    max_errors: int | None = None,
) -> JsonlValidationReport:
    """Validate JSONL records and collect errors without raising."""

    file_path = Path(path)
    total = 0
    valid = 0
    issues: list[JsonlValidationIssue] = []
    with file_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            total += 1
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                issues.append(JsonlValidationIssue(line_number=line_number, message=str(exc)))
            else:
                if not isinstance(payload, Mapping):
                    issues.append(
                        JsonlValidationIssue(
                            line_number=line_number,
                            message="JSON value must be an object",
                        )
                    )
                else:
                    try:
                        parser(payload)
                    except ValueError as exc:
                        issues.append(JsonlValidationIssue(line_number=line_number, message=str(exc)))
                    else:
                        valid += 1
            if max_errors is not None and len(issues) >= max_errors:
                break
    logger.info(
        "validate_jsonl",
        extra={"path": str(file_path), "total": total, "valid": valid, "errors": len(issues)},
    )
    return JsonlValidationReport(total=total, valid=valid, issues=issues)


def write_jsonl(path: str | Path, records: Iterable[Any]) -> None:
    """Write iterable of mappings or dataclasses to a jsonl file."""

    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with file_path.open("w", encoding="utf-8") as handle:
        for record in records:
            payload = _coerce_record(record)
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
            count += 1
    logger.info("write_jsonl", extra={"path": str(file_path), "count": count})


def _coerce_record(record: Any) -> Mapping[str, Any]:
    if is_dataclass(record):
        return asdict(record)
    if isinstance(record, Mapping):
        return record
    raise ValueError("Record must be a dataclass instance or a mapping")
