"""state2action_vision package."""

from state2action_vision.config.schemas import (
    DatasetRecord,
    EventRecord,
    parse_dataset_record,
    parse_event_record,
)
from state2action_vision.config.presets import (
    CandidateSlot,
    Preset,
    Rect,
    Resolution,
    load_preset,
)
from state2action_vision.dataset.io import read_jsonl, write_jsonl

__all__ = [
    "DatasetRecord",
    "EventRecord",
    "CandidateSlot",
    "Preset",
    "Rect",
    "Resolution",
    "load_preset",
    "parse_dataset_record",
    "parse_event_record",
    "read_jsonl",
    "write_jsonl",
]
