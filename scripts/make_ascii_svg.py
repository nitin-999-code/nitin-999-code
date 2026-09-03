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
    
    # Terminal UI Constants
    PADDING = 24
    TITLE_BAR_H = 36
    CARD_W = int(COLS * CHAR_WIDTH) + PADDING * 2
    content_h = int(num_rows * line_h)
    svg_height = TITLE_BAR_H + PADDING * 2 + content_h
    
    total_anim_time = num_rows * ANIMATION_ROW_DELAY + 0.5

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
                 f'viewBox="0 0 {CARD_W} {svg_height}" '
                 f'width="{CARD_W}" height="{svg_height}">')

    # Styles
    lines.append("<style>")
    lines.append(f"  svg {{ background: transparent; }}")
    lines.append(f"  .card-bg {{ fill: {BG_COLOR}; stroke: #30363d; stroke-width: 1; rx: 10; }}")
    lines.append(f"  text {{")
    lines.append(f"    font-family: 'Courier New', 'Fira Code', monospace;")
    lines.append(f"    font-size: {FONT_SIZE}px;")
    lines.append(f"    fill: {FG_COLOR};")
    lines.append(f"    white-space: pre;")
    lines.append(f"    dominant-baseline: text-before-edge;")
    lines.append(f"  }}")
    lines.append(f"  .title {{ fill: #58a6ff; font-size: 12px; font-family: 'Fira Code', 'Courier New', monospace; }}")
    duration = 8.0
    for i in range(num_rows):
        delay = i * ANIMATION_ROW_DELAY
        start_pct = (delay / duration) * 100
        end_pct = ((delay + 0.15) / duration) * 100
        lines.append(f"  @keyframes rAnim{i} {{")
        lines.append(f"    0%, {start_pct:.2f}% {{ opacity: 0; }}")
        lines.append(f"    {end_pct:.2f}%, 95% {{ opacity: 1; }}")
        lines.append(f"    96%, 100% {{ opacity: 0; }}")
        lines.append(f"  }}")
        lines.append(f"  .r{i} {{ opacity: 0; animation: rAnim{i} {duration}s ease-out infinite; }}")
        
    cursor_appear = (num_rows - 1) * ANIMATION_ROW_DELAY
    c_start = (cursor_appear / duration) * 100
    c_b1 = min(c_start + 2, 95)
    c_b2 = min(c_start + 4, 95)
    c_b3 = min(c_start + 6, 95)
    c_b4 = min(c_start + 8, 95)
    lines.append(f"  @keyframes cursorAnim {{")
    lines.append(f"    0%, {c_start:.2f}% {{ opacity: 0; }}")
    lines.append(f"    {c_start:.2f}%, {c_b1:.2f}% {{ opacity: 1; }}")
    lines.append(f"    {c_b1:.2f}%, {c_b2:.2f}% {{ opacity: 0; }}")
    lines.append(f"    {c_b2:.2f}%, {c_b3:.2f}% {{ opacity: 1; }}")
    lines.append(f"    {c_b3:.2f}%, {c_b4:.2f}% {{ opacity: 0; }}")
    lines.append(f"    {c_b4:.2f}%, 95% {{ opacity: 1; }}")
    lines.append(f"    96%, 100% {{ opacity: 0; }}")
    lines.append(f"  }}")
    lines.append(f"  .cursor {{ opacity: 0; animation: cursorAnim {duration}s infinite; }}")
    lines.append("</style>")

    # Card background
    lines.append(f'<rect class="card-bg" x="1" y="1" width="{CARD_W - 2}" height="{svg_height - 2}" />')

    # Title bar dots
    dot_y = 16
    lines.append(f'<circle cx="18" cy="{dot_y}" r="6" fill="#ff5f56" />')
    lines.append(f'<circle cx="38" cy="{dot_y}" r="6" fill="#ffbd2e" />')
    lines.append(f'<circle cx="58" cy="{dot_y}" r="6" fill="#27c93f" />')
    lines.append(f'<text class="title" x="{CARD_W // 2}" y="10" text-anchor="middle">portrait — bash</text>')

    # Render each row as a <text> element
    content_y_start = TITLE_BAR_H + PADDING
    for i, row_text in enumerate(grid):
        y = content_y_start + i * line_h
        escaped = html.escape(row_text, quote=True)
        lines.append(f'<text x="{PADDING}" y="{y:.1f}" class="r{i}">{escaped}</text>')

    # Terminal cursor that follows the last revealed row
    cursor_x = PADDING
    cursor_y = content_y_start + (num_rows - 1) * line_h
    cursor_appear = (num_rows - 1) * ANIMATION_ROW_DELAY
    lines.append(f'<rect class="cursor" x="{cursor_x}" y="{cursor_y:.1f}" '
                 f'width="{CHAR_WIDTH}" height="{FONT_SIZE}" fill="#58a6ff"></rect>')

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
