#!/usr/bin/env python3
"""
make_ascii_svg.py — Convert source-prepped.png into an animated ASCII portrait SVG.

The portrait reveals row-by-row with a typing effect and then freezes.
"""

import sys
from pathlib import Path
from PIL import Image
import html

# ── Configuration ─────────────────────────────────────────────────
COLS = 90          # character columns
ROWS = 50          # character rows (auto-adjusted for aspect ratio)
DENSITY_RAMP = " .`:-=+*cs#%@"
FONT_SIZE = 10     # px
LINE_HEIGHT = 1.15
CHAR_WIDTH = 6.02  # approximate width of a monospace char at this font size
BG_COLOR = "#0d1117"
FG_COLOR = "#c9d1d9"
ANIMATION_ROW_DELAY = 0.04  # seconds between rows


def image_to_ascii_grid(img_path: Path) -> list[str]:
    """Convert a grayscale image to a grid of ASCII characters."""
    img = Image.open(img_path).convert("L")

    # Compute rows to preserve aspect ratio (chars are ~2x taller than wide)
    aspect = img.height / img.width
    rows = int(COLS * aspect * 0.45)
    rows = max(20, min(rows, 70))

    img_resized = img.resize((COLS, rows), Image.LANCZOS)
    pixels = img_resized.load()

    ramp_len = len(DENSITY_RAMP)
    grid = []
    for y in range(rows):
        row_chars = []
        for x in range(COLS):
            brightness = pixels[x, y]  # 0=black, 255=white
            idx = int(brightness / 256 * ramp_len)
            idx = max(0, min(idx, ramp_len - 1))
            row_chars.append(DENSITY_RAMP[idx])
        grid.append("".join(row_chars))
    return grid


def build_svg(grid: list[str]) -> str:
    """Build an SVG string with row-by-row reveal animation."""
    num_rows = len(grid)
    line_h = FONT_SIZE * LINE_HEIGHT
    svg_width = int(COLS * CHAR_WIDTH) + 20
    svg_height = int(num_rows * line_h) + 20
    total_anim_time = num_rows * ANIMATION_ROW_DELAY + 0.5

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
                 f'viewBox="0 0 {svg_width} {svg_height}" '
                 f'width="{svg_width}" height="{svg_height}">')

    # Styles
    lines.append("<style>")
    lines.append(f"  svg {{ background: {BG_COLOR}; }}")
    lines.append(f"  text {{")
    lines.append(f"    font-family: 'Courier New', 'Fira Code', monospace;")
    lines.append(f"    font-size: {FONT_SIZE}px;")
    lines.append(f"    fill: {FG_COLOR};")
    lines.append(f"    white-space: pre;")
    lines.append(f"    dominant-baseline: text-before-edge;")
    lines.append(f"  }}")
    # Row animation keyframes
    lines.append(f"  @keyframes reveal {{")
    lines.append(f"    0%   {{ opacity: 0; }}") 
    lines.append(f"    100% {{ opacity: 1; }}")
    lines.append(f"  }}")
    # Cursor blink (plays during reveal, then vanishes)
    lines.append(f"  @keyframes cursorFade {{")
    lines.append(f"    0%, 50% {{ opacity: 1; }}")
    lines.append(f"    51%, 100% {{ opacity: 0; }}")
    lines.append(f"  }}")
    # Per-row animation classes
    for i in range(num_rows):
        delay = i * ANIMATION_ROW_DELAY
        lines.append(f"  .r{i} {{ opacity: 0; animation: reveal 0.15s ease-out {delay:.3f}s forwards; }}")
    lines.append("</style>")

    # Render each row as a <text> element
    for i, row_text in enumerate(grid):
        y = 10 + i * line_h
        escaped = html.escape(row_text, quote=True)
        lines.append(f'<text x="10" y="{y:.1f}" class="r{i}">{escaped}</text>')

    # Terminal cursor that follows the last revealed row
    cursor_x = 10
    cursor_y = 10 + (num_rows - 1) * line_h
    cursor_appear = (num_rows - 1) * ANIMATION_ROW_DELAY
    lines.append(f'<rect x="{cursor_x}" y="{cursor_y:.1f}" width="{CHAR_WIDTH}" height="{FONT_SIZE}" '
                 f'fill="#58a6ff" opacity="0">')
    lines.append(f'  <animate attributeName="opacity" values="0;1;1;0" '
                 f'keyTimes="0;0.01;0.5;1" dur="1s" begin="{cursor_appear:.2f}s" '
                 f'fill="freeze" />')
    lines.append(f'</rect>')

    lines.append("</svg>")
    return "\n".join(lines)


def main():
    repo_root = Path(__file__).resolve().parent.parent
    src = repo_root / "source-prepped.png"
    dst = repo_root / "avi-ascii.svg"

    if not src.exists():
        print(f"❌ {src.name} not found. Run prep_photo.py first.")
        sys.exit(1)

    print(f"🎨 Generating ASCII portrait from {src.name} …")
    grid = image_to_ascii_grid(src)
    svg_content = build_svg(grid)

    dst.write_text(svg_content, encoding="utf-8")
    print(f"✅ Saved {dst.name} ({dst.stat().st_size:,} bytes, {len(grid)} rows)")


if __name__ == "__main__":
    main()
