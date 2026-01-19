from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def _run_inspect(args: list[str]) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src")
    return subprocess.run(
        [sys.executable, str(repo_root / "tools" / "inspect_roi.py"), *args],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_inspect_roi_writes_svg(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    preset_path = repo_root / "configs" / "presets" / "vertical_720p.yaml"
    output_path = tmp_path / "overlay.svg"

    result = _run_inspect(["--preset", str(preset_path), "--out", str(output_path)])

    assert result.returncode == 0
    assert output_path.exists()
    svg = output_path.read_text(encoding="utf-8")
    assert "<svg" in svg
    assert "slot_0" in svg
