from __future__ import annotations

from pathlib import Path

import pytest

from state2action_vision.config.presets import load_preset


def test_load_preset_from_repo_config() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    preset_path = repo_root / "configs" / "presets" / "vertical_720p.yaml"

    preset = load_preset(preset_path)

    assert preset.preset_id == "vertical_720p:v1"
    assert preset.resolution.width == 720
    assert len(preset.candidate_slots) == 3


def test_load_preset_rejects_out_of_bounds_rect(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(
        "\n".join(
            [
                "{",
                '  "preset_id": "bad",',
                '  "grid_id": "bad",',
                '  "resolution": {"width": 720, "height": 1280},',
                '  "roi": {',
                '    "board": {"x": 1.2, "y": 0.1, "w": 0.3, "h": 0.2},',
                '    "candidate_slots": [',
                '      {"slot_id": 0, "rect": {"x": 0.1, "y": 0.8, "w": 0.2, "h": 0.1}}',
                "    ]",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="roi.board.x"):
        load_preset(path)
