"""JSONL schema validation for events and datasets."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Mapping, Sequence

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EventRecord:
    """Single labeled event aligned to a video timestamp."""

    video_id: str
    t_ms: int
    action_id: int
    tap_xy_rel: tuple[float, float] | None
    candidate_slot: int | None


@dataclass(frozen=True)
class DatasetRecord:
    """Single training example with frame path and auxiliary features."""

    image_path: str
    action_id: int
    tap_xy_rel: tuple[float, float] | None
    candidate_mask: list[int]
    resource_gauge: float | None
    time_remaining_s: float | None
    grid_id: str


def parse_event_record(raw: Mapping[str, Any]) -> EventRecord:
    """Parse and validate a single event record."""

    video_id = _require_str(raw, "video_id")
    t_ms = _require_int(raw, "t_ms", minimum=0)
    action_id = _require_int(raw, "action_id", minimum=0)
    tap_xy_rel = _optional_xy(raw.get("tap_xy_rel"), field_name="tap_xy_rel")
    candidate_slot = _optional_int(raw.get("candidate_slot"), field_name="candidate_slot", minimum=0)

    record = EventRecord(
        video_id=video_id,
        t_ms=t_ms,
        action_id=action_id,
        tap_xy_rel=tap_xy_rel,
        candidate_slot=candidate_slot,
    )
    logger.debug("validated_event_record", extra={"video_id": video_id, "t_ms": t_ms})
    return record


def parse_dataset_record(raw: Mapping[str, Any]) -> DatasetRecord:
    """Parse and validate a single dataset record."""

    image_path = _require_str(raw, "image_path")
    action_id = _require_int(raw, "action_id", minimum=0)
    tap_xy_rel = _optional_xy(raw.get("tap_xy_rel"), field_name="tap_xy_rel")
    candidate_mask = _require_mask(raw, "candidate_mask")
    resource_gauge = _optional_float(raw.get("resource_gauge"), field_name="resource_gauge", minimum=0.0, maximum=1.0)
    time_remaining_s = _optional_float(raw.get("time_remaining_s"), field_name="time_remaining_s", minimum=0.0)
    grid_id = _require_str(raw, "grid_id")

    record = DatasetRecord(
        image_path=image_path,
        action_id=action_id,
        tap_xy_rel=tap_xy_rel,
        candidate_mask=candidate_mask,
        resource_gauge=resource_gauge,
        time_remaining_s=time_remaining_s,
        grid_id=grid_id,
    )
    logger.debug("validated_dataset_record", extra={"image_path": image_path, "grid_id": grid_id})
    return record


def _require_str(raw: Mapping[str, Any], key: str) -> str:
    if key not in raw:
        raise ValueError(f"Missing required field: {key}")
    value = raw[key]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Field '{key}' must be a non-empty string")
    return value


def _require_int(raw: Mapping[str, Any], key: str, minimum: int | None = None) -> int:
    if key not in raw:
        raise ValueError(f"Missing required field: {key}")
    value = raw[key]
    if not isinstance(value, int):
        raise ValueError(f"Field '{key}' must be an integer")
    if minimum is not None and value < minimum:
        raise ValueError(f"Field '{key}' must be >= {minimum}")
    return value


def _optional_int(value: Any, field_name: str, minimum: int | None = None) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int):
        raise ValueError(f"Field '{field_name}' must be an integer or null")
    if minimum is not None and value < minimum:
        raise ValueError(f"Field '{field_name}' must be >= {minimum}")
    return value


def _optional_float(
    value: Any,
    field_name: str,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float | None:
    if value is None:
        return None
    if not isinstance(value, (int, float)):
        raise ValueError(f"Field '{field_name}' must be a number or null")
    value = float(value)
    if minimum is not None and value < minimum:
        raise ValueError(f"Field '{field_name}' must be >= {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"Field '{field_name}' must be <= {maximum}")
    return value


def _optional_xy(value: Any, field_name: str) -> tuple[float, float] | None:
    if value is None:
        return None
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"Field '{field_name}' must be a 2-element sequence or null")
    if len(value) != 2:
        raise ValueError(f"Field '{field_name}' must have length 2")
    x, y = value
    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
        raise ValueError(f"Field '{field_name}' entries must be numeric")
    x_float = float(x)
    y_float = float(y)
    if not (0.0 <= x_float <= 1.0 and 0.0 <= y_float <= 1.0):
        raise ValueError(f"Field '{field_name}' entries must be between 0 and 1")
    return (x_float, y_float)


def _require_mask(raw: Mapping[str, Any], key: str) -> list[int]:
    if key not in raw:
        raise ValueError(f"Missing required field: {key}")
    value = raw[key]
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"Field '{key}' must be a sequence of 0/1 values")
    if not value:
        raise ValueError(f"Field '{key}' must not be empty")
    mask: list[int] = []
    for entry in value:
        if not isinstance(entry, int) or entry not in (0, 1):
            raise ValueError(f"Field '{key}' entries must be 0 or 1")
        mask.append(entry)
    return mask
