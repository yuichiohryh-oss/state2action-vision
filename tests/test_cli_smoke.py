from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


def _run_validate(args: list[str]) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src")
    return subprocess.run(
        [sys.executable, str(repo_root / "tools" / "validate_jsonl.py"), *args],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_validate_events_ok(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    record = {"video_id": "v001", "t_ms": 0, "action_id": 1, "tap_xy_rel": [0.1, 0.2], "candidate_slot": 0}
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    result = _run_validate(["--events", str(path)])

    assert result.returncode == 0


def test_validate_dataset_fail(tmp_path: Path) -> None:
    path = tmp_path / "dataset.jsonl"
    record = {
        "image_path": "frame.png",
        "action_id": 1,
        "tap_xy_rel": [0.1, 1.2],
        "candidate_mask": [1, 0, 1],
        "resource_gauge": 0.5,
        "time_remaining_s": 12.0,
        "grid_id": "vertical_720p:v1",
    }
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    result = _run_validate(["--dataset", str(path)])

    assert result.returncode == 1
    assert "validation_failed" in result.stderr


def test_schema_output() -> None:
    result = _run_validate(["--schema", "events"])

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["title"] == "events.jsonl"


def test_schema_out_requires_schema() -> None:
    result = _run_validate(["--schema-out", "schema.json"])

    assert result.returncode != 0
    assert "requires --schema" in result.stderr


def test_schema_output_written(tmp_path: Path) -> None:
    output_path = tmp_path / "schema.json"

    result = _run_validate(["--schema", "dataset", "--schema-out", str(output_path)])

    assert result.returncode == 0
    assert output_path.exists()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["title"] == "dataset.jsonl"
