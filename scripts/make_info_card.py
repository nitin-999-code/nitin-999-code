#!/usr/bin/env python3
"""
make_info_card.py — Generate a dark terminal / neofetch-style info card SVG.

Set STATIC=1 to generate without animation:
    STATIC=1 python scripts/make_info_card.py
"""

import os
from pathlib import Path

# ══════════════════════════════════════════════════════════════════
# ✏️  EDIT YOUR PERSONAL INFORMATION HERE
# ══════════════════════════════════════════════════════════════════
NAME        = "Nitin Sahu"
USERNAME    = "nitin-999-code"
ROLE        = "Software Developer"
FOCUS       = "AI + Full Stack Development"
STACK       = "Python · JavaScript · React · Node.js"
PROJECTS    = "Building things that matter"
LEARNING    = "System Design · Cloud · AI/ML"
STATUS      = "🟢 Building"
PRONOUNS    = "he/him"
LOCATION    = "India"
# ══════════════════════════════════════════════════════════════════

STATIC = os.environ.get("STATIC", "0") == "1"

# ── Theme ─────────────────────────────────────────────────────────
BG           = "#0d1117"
BORDER       = "#30363d"
TITLE_COLOR  = "#58a6ff"
KEY_COLOR    = "#8b949e"
VAL_COLOR    = "#c9d1d9"
ACCENT       = "#39d353"
PROMPT_COLOR = "#39d353"
DOT_RED      = "#ff5f56"
DOT_YELLOW   = "#ffbd2e"
DOT_GREEN    = "#27c93f"
FONT         = "'Fira Code', 'Courier New', 'Consolas', monospace"
FONT_SIZE    = 14
LINE_H       = 24
PADDING      = 24
CARD_W       = 480
RADIUS       = 10


def build_info_card() -> str:
    # Build info lines
    info_lines = [
        ("", f"{USERNAME}@github:~$ whoami", "prompt"),
        ("", "", "blank"),
        ("Name",     NAME),
        ("User",     f"@{USERNAME}"),
        ("Role",     ROLE),
        ("Focus",    FOCUS),
        ("Stack",    STACK),
        ("Projects", PROJECTS),
        ("Learning", LEARNING),
        ("Location", LOCATION),
        ("Status",   STATUS),
        ("", "", "blank"),
        ("", "────────────────────────────────", "separator"),
        ("", f"{USERNAME}@github:~$ █", "prompt"),
    ]

    num_lines = len(info_lines)
    content_h = num_lines * LINE_H + PADDING * 2 + 36  # 36 for title bar
    svg_h = content_h + 4  # border offset

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
                 f'viewBox="0 0 {CARD_W} {svg_h}" '
                 f'width="{CARD_W}" height="{svg_h}">')

    # Styles
    parts.append("<style>")
    parts.append(f"  svg {{ background: transparent; }}")
    parts.append(f"  .card-bg {{ fill: {BG}; stroke: {BORDER}; stroke-width: 1; rx: {RADIUS}; }}")
    parts.append(f"  text {{ font-family: {FONT}; font-size: {FONT_SIZE}px; dominant-baseline: text-before-edge; }}")
    parts.append(f"  .key {{ fill: {KEY_COLOR}; }}")
    parts.append(f"  .val {{ fill: {VAL_COLOR}; }}")
    parts.append(f"  .prompt {{ fill: {PROMPT_COLOR}; }}")
    parts.append(f"  .sep {{ fill: {BORDER}; }}")
    parts.append(f"  .title {{ fill: {TITLE_COLOR}; font-size: 12px; }}")

    if not STATIC:
        duration = 8.0
        for i in range(num_lines):
            delay = 0.3 + i * 0.12
            start_pct = (delay / duration) * 100
            end_pct = ((delay + 0.3) / duration) * 100
            parts.append(f"  @keyframes lnAnim{i} {{")
            parts.append(f"    0%, {start_pct:.2f}% {{ opacity: 0; transform: translateY(6px); }}")
            parts.append(f"    {end_pct:.2f}%, 95% {{ opacity: 1; transform: translateY(0); }}")
            parts.append(f"    96%, 100% {{ opacity: 0; transform: translateY(6px); }}")
            parts.append(f"  }}")
            parts.append(f"  .ln{i} {{ opacity: 0; animation: lnAnim{i} {duration}s ease-out infinite; }}")
    else:
        for i in range(num_lines):
            parts.append(f"  .ln{i} {{ opacity: 1; }}")

    parts.append("</style>")

    # Card background
    parts.append(f'<rect class="card-bg" x="1" y="1" width="{CARD_W - 2}" height="{svg_h - 2}" />')

    # Title bar dots
    dot_y = 16
    parts.append(f'<circle cx="18" cy="{dot_y}" r="6" fill="{DOT_RED}" />')
    parts.append(f'<circle cx="38" cy="{dot_y}" r="6" fill="{DOT_YELLOW}" />')
    parts.append(f'<circle cx="58" cy="{dot_y}" r="6" fill="{DOT_GREEN}" />')
    parts.append(f'<text class="title" x="{CARD_W // 2}" y="10" text-anchor="middle">{USERNAME} — bash</text>')

    # Content lines
    content_y_start = 36 + PADDING
    for i, line in enumerate(info_lines):
        y = content_y_start + i * LINE_H

        if len(line) == 3:
            kind = line[2]
            if kind == "prompt":
                parts.append(f'<text class="prompt ln{i}" x="{PADDING}" y="{y}">{line[1]}</text>')
            elif kind == "separator":
                parts.append(f'<text class="sep ln{i}" x="{PADDING}" y="{y}">{line[1]}</text>')
            elif kind == "blank":
                pass  # empty line, just takes space
        else:
            key, val = line[0], line[1]
            padded_key = key.ljust(10)
            # Render key : value
            parts.append(
                f'<text class="ln{i}" x="{PADDING}" y="{y}">'
                f'<tspan class="key">{padded_key}</tspan>'
                f'<tspan class="val"> : {val}</tspan>'
                f'</text>'
            )

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    repo_root = Path(__file__).resolve().parent.parent
    dst = repo_root / "info-card.svg"

    mode = "static" if STATIC else "animated"
    print(f"🖥️  Generating info card ({mode}) …")

    svg_content = build_info_card()
    dst.write_text(svg_content, encoding="utf-8")
    print(f"✅ Saved {dst.name} ({dst.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
