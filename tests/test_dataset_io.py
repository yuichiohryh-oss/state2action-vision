from __future__ import annotations

import json
from pathlib import Path

import pytest

from state2action_vision.config.schemas import DatasetRecord, EventRecord, parse_dataset_record, parse_event_record
from state2action_vision.dataset.io import read_jsonl, write_jsonl


def test_parse_event_record_success() -> None:
    record = parse_event_record(
        {
            "video_id": "v001",
            "t_ms": 1200,
            "action_id": 3,
            "tap_xy_rel": [0.2, 0.8],
            "candidate_slot": 1,
        }
    )
    assert record == EventRecord(
        video_id="v001",
        t_ms=1200,
        action_id=3,
        tap_xy_rel=(0.2, 0.8),
        candidate_slot=1,
    )


def test_parse_dataset_record_success() -> None:
    record = parse_dataset_record(
        {
            "image_path": "data/derived/frames/v001/0001200.png",
            "action_id": 5,
            "tap_xy_rel": [0.1, 0.4],
            "candidate_mask": [1, 0, 1],
            "resource_gauge": 0.7,
            "time_remaining_s": 31.2,
            "grid_id": "vertical_720p:v1",
        }
    )
    assert record.image_path.endswith("0001200.png")
    assert record.candidate_mask == [1, 0, 1]


def test_parse_dataset_record_invalid_mask() -> None:
    with pytest.raises(ValueError, match="candidate_mask"):
        parse_dataset_record(
            {
                "image_path": "frame.png",
                "action_id": 2,
                "tap_xy_rel": None,
                "candidate_mask": [1, 2],
                "resource_gauge": None,
                "time_remaining_s": None,
                "grid_id": "vertical_720p:v1",
            }
        )


def test_jsonl_roundtrip(tmp_path: Path) -> None:
    records = [
        DatasetRecord(
            image_path="frame.png",
            action_id=1,
            tap_xy_rel=(0.3, 0.6),
            candidate_mask=[1, 0, 1],
            resource_gauge=0.5,
            time_remaining_s=12.3,
            grid_id="vertical_720p:v1",
        )
    ]
    path = tmp_path / "dataset.jsonl"

    write_jsonl(path, records)
    loaded = read_jsonl(path, parse_dataset_record)

    assert loaded == records
    raw = json.loads(path.read_text(encoding="utf-8").strip())
    assert raw["image_path"] == "frame.png"


def test_read_jsonl_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text("not json\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid JSON"):
        read_jsonl(path, parse_dataset_record)
