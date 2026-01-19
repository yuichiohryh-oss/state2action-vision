"""Generate an SVG overlay to inspect preset ROI definitions."""

from __future__ import annotations

import argparse
import base64
import logging
from pathlib import Path

from state2action_vision.config.presets import Preset, Rect, load_preset

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render preset ROI overlays as an SVG file.")
    parser.add_argument(
        "--preset",
        type=Path,
        required=True,
        help="Path to the preset YAML/JSON file.",
    )
    parser.add_argument(
        "--image",
        type=Path,
        help="Optional background image path to embed in the SVG.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Output SVG file path. If omitted, SVG is printed to stdout.",
    )
    return parser


def _rect_to_svg(rect: Rect, width: int, height: int) -> tuple[float, float, float, float]:
    return (
        rect.x * width,
        rect.y * height,
        rect.w * width,
        rect.h * height,
    )


def _format_rect_elements(
    label: str,
    rect: Rect,
    width: int,
    height: int,
    stroke: str,
) -> str:
    x, y, w, h = _rect_to_svg(rect, width, height)
    text_x = max(0.0, x + 4.0)
    text_y = max(0.0, y + 16.0)
    return "\n".join(
        [
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'style="fill:none;stroke:{stroke};stroke-width:2" />',
            f'<text x="{text_x:.1f}" y="{text_y:.1f}" '
            f'style="fill:{stroke};font-size:14px;font-family:Arial">{label}</text>',
        ]
    )


def _encode_image(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower().lstrip(".")
    if suffix in {"jpg", "jpeg"}:
        mime = "image/jpeg"
    elif suffix == "png":
        mime = "image/png"
    else:
        raise ValueError("Supported image formats are .png or .jpg/.jpeg")
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return mime, data


def _render_svg(preset: Preset, image_path: Path | None) -> str:
    width = preset.resolution.width
    height = preset.resolution.height
    elements: list[str] = []

    if image_path is not None:
        mime, data = _encode_image(image_path)
        elements.append(
            "\n".join(
                [
                    f'<image href="data:{mime};base64,{data}" x="0" y="0" '
                    f'width="{width}" height="{height}" />',
                ]
            )
        )

    elements.append(_format_rect_elements("board", preset.board_roi, width, height, stroke="#00B3E6"))

    if preset.resource_gauge_roi is not None:
        elements.append(
            _format_rect_elements(
                "resource_gauge",
                preset.resource_gauge_roi,
                width,
                height,
                stroke="#6A5ACD",
            )
        )

    if preset.time_ui_roi is not None:
        elements.append(
            _format_rect_elements(
                "time_ui",
                preset.time_ui_roi,
                width,
                height,
                stroke="#FF8C00",
            )
        )

    for slot in preset.candidate_slots:
        elements.append(
            _format_rect_elements(
                f"slot_{slot.slot_id}",
                slot.rect,
                width,
                height,
                stroke="#00A389",
            )
        )

    body = "\n".join(elements)
    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">',
            body,
            "</svg>",
        ]
    )


def _log_rect_summary(preset: Preset) -> None:
    def _log_item(label: str, rect: Rect) -> None:
        logger.info(
            "roi_rect",
            extra={
                "label": label,
                "x": rect.x,
                "y": rect.y,
                "w": rect.w,
                "h": rect.h,
            },
        )

    _log_item("board", preset.board_roi)
    if preset.resource_gauge_roi is not None:
        _log_item("resource_gauge", preset.resource_gauge_roi)
    if preset.time_ui_roi is not None:
        _log_item("time_ui", preset.time_ui_roi)
    for slot in preset.candidate_slots:
        _log_item(f"slot_{slot.slot_id}", slot.rect)


def _write_output(svg: str, output_path: Path | None) -> None:
    if output_path is None:
        print(svg)
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        preset = load_preset(args.preset)
    except (ValueError, RuntimeError) as exc:
        logger.error("load_preset_failed", extra={"path": str(args.preset), "error": str(exc)})
        return 1

    if args.image is not None and not args.image.exists():
        logger.error("image_not_found", extra={"path": str(args.image)})
        return 1

    try:
        svg = _render_svg(preset, args.image)
    except ValueError as exc:
        logger.error("render_failed", extra={"error": str(exc)})
        return 1

    _write_output(svg, args.out)
    _log_rect_summary(preset)
    logger.info(
        "inspect_roi_complete",
        extra={"preset_id": preset.preset_id, "output": str(args.out) if args.out else "stdout"},
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
