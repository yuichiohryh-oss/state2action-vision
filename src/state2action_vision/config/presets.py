"""Preset loading utilities for ROI and grid definitions."""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    yaml = None

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Resolution:
    """Resolution metadata for presets."""

    width: int
    height: int


@dataclass(frozen=True)
class Rect:
    """Normalized rectangle definition."""

    x: float
    y: float
    w: float
    h: float


@dataclass(frozen=True)
class CandidateSlot:
    """Candidate UI slot description."""

    slot_id: int
    rect: Rect


@dataclass(frozen=True)
class Preset:
    """ROI preset describing grid and UI regions."""

    preset_id: str
    grid_id: str
    resolution: Resolution
    board_roi: Rect
    candidate_slots: list[CandidateSlot]
    resource_gauge_roi: Rect | None
    time_ui_roi: Rect | None


def load_preset(path: str | Path) -> Preset:
    """Load and validate a preset YAML file."""

    preset_path = Path(path)
    payload = _load_yaml(preset_path)
    if not isinstance(payload, Mapping):
        raise ValueError("Preset YAML must contain a mapping at the root")

    preset_id = _require_str(payload, "preset_id")
    grid_id = _require_str(payload, "grid_id")
    resolution_raw = _require_mapping(payload, "resolution")
    resolution = Resolution(
        width=_require_int(resolution_raw, "width", minimum=1),
        height=_require_int(resolution_raw, "height", minimum=1),
    )

    roi = _require_mapping(payload, "roi")
    board_roi = _parse_rect(_require_mapping(roi, "board"), field_name="roi.board")
    candidate_slots = _parse_candidate_slots(_require_sequence(roi, "candidate_slots"))
    resource_gauge_roi = _optional_rect(roi.get("resource_gauge"), field_name="roi.resource_gauge")
    time_ui_roi = _optional_rect(roi.get("time_ui"), field_name="roi.time_ui")

    preset = Preset(
        preset_id=preset_id,
        grid_id=grid_id,
        resolution=resolution,
        board_roi=board_roi,
        candidate_slots=candidate_slots,
        resource_gauge_roi=resource_gauge_roi,
        time_ui_roi=time_ui_roi,
    )
    logger.info(
        "loaded_preset",
        extra={"preset_id": preset_id, "path": str(preset_path), "slots": len(candidate_slots)},
    )
    return preset


def _load_yaml(path: Path) -> Any:
    raw_text = path.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(raw_text)
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as exc:  # pragma: no cover - best effort fallback
        raise RuntimeError(
            "PyYAML is required to parse non-JSON presets. Install PyYAML or use JSON syntax."
        ) from exc


def _require_mapping(raw: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    if key not in raw:
        raise ValueError(f"Missing required field: {key}")
    value = raw[key]
    if not isinstance(value, Mapping):
        raise ValueError(f"Field '{key}' must be a mapping")
    return value


def _require_sequence(raw: Mapping[str, Any], key: str) -> Sequence[Any]:
    if key not in raw:
        raise ValueError(f"Missing required field: {key}")
    value = raw[key]
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"Field '{key}' must be a sequence")
    return value


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


def _require_float(raw: Mapping[str, Any], key: str) -> float:
    if key not in raw:
        raise ValueError(f"Missing required field: {key}")
    value = raw[key]
    if not isinstance(value, (int, float)):
        raise ValueError(f"Field '{key}' must be a number")
    return float(value)


def _parse_rect(raw: Mapping[str, Any], field_name: str) -> Rect:
    x = _require_float(raw, "x")
    y = _require_float(raw, "y")
    w = _require_float(raw, "w")
    h = _require_float(raw, "h")
    for value, axis in ((x, "x"), (y, "y"), (w, "w"), (h, "h")):
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{field_name}.{axis} must be between 0 and 1")
    if w <= 0.0 or h <= 0.0:
        raise ValueError(f"{field_name}.w and {field_name}.h must be positive")
    if x + w > 1.0 or y + h > 1.0:
        raise ValueError(f"{field_name} must fit inside normalized bounds")
    return Rect(x=x, y=y, w=w, h=h)


def _optional_rect(value: Any, field_name: str) -> Rect | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping or null")
    return _parse_rect(value, field_name=field_name)


def _parse_candidate_slots(raw_slots: Sequence[Any]) -> list[CandidateSlot]:
    slots: list[CandidateSlot] = []
    seen: set[int] = set()
    for index, entry in enumerate(raw_slots):
        if not isinstance(entry, Mapping):
            raise ValueError("candidate_slots entries must be mappings")
        slot_id = _require_int(entry, "slot_id", minimum=0)
        if slot_id in seen:
            raise ValueError(f"candidate_slots slot_id duplicated: {slot_id}")
        seen.add(slot_id)
        rect = _parse_rect(_require_mapping(entry, "rect"), field_name=f"candidate_slots[{index}].rect")
        slots.append(CandidateSlot(slot_id=slot_id, rect=rect))
    if not slots:
        raise ValueError("candidate_slots must not be empty")
    return slots
