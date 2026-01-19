"""JSONL IO utilities for datasets."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import json
import logging
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Mapping, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def read_jsonl(path: str | Path, parser: Callable[[Mapping[str, Any]], T]) -> list[T]:
    """Read a jsonl file and parse each line with the provided parser."""

    records = list(iter_jsonl(path, parser))
    logger.info("read_jsonl", extra={"path": str(Path(path)), "count": len(records)})
    return records


def iter_jsonl(path: str | Path, parser: Callable[[Mapping[str, Any]], T]) -> Iterator[T]:
    """Iterate over a jsonl file and parse each line with the provided parser."""

    file_path = Path(path)

    def _iterator() -> Iterator[T]:
        count = 0
        success = False
        try:
            with file_path.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ValueError(
                            f"Invalid JSON on line {line_number} in {file_path}"
                        ) from exc
                    if not isinstance(payload, Mapping):
                        raise ValueError(f"Line {line_number} in {file_path} must be a JSON object")
                    try:
                        record = parser(payload)
                    except ValueError as exc:
                        raise ValueError(
                            f"Invalid record on line {line_number} in {file_path}: {exc}"
                        ) from exc
                    count += 1
                    yield record
            success = True
        finally:
            if success:
                logger.info("iter_jsonl", extra={"path": str(file_path), "count": count})

    return _iterator()


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
