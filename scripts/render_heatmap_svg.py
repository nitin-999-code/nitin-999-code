#!/usr/bin/env python3
"""
render_heatmap_svg.py — Render a GitHub-style contribution heatmap SVG.

Input:  data/contributions.json
Output: contrib-heatmap.svg

Features:
  - 53 weeks × 7 days grid with rounded cells
  - Green intensity levels
  - Diagonal staggered reveal animation (plays once, freezes)
  - Less → More legend
  - Stats footer
"""

import json
import sys
from pathlib import Path

# ── Theme ─────────────────────────────────────────────────────────
BG = "#0d1117"
TEXT_COLOR = "#8b949e"
LABEL_COLOR = "#8b949e"
BORDER_COLOR = "#30363d"
FONT = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
MONO = "'Fira Code', 'Courier New', monospace"

# GitHub-ish green palette (level 0–4)
PALETTE = [
    "#161b22",   # level 0 – no contributions
    "#0e4429",   # level 1
    "#006d32",   # level 2
    "#26a641",   # level 3
    "#39d353",   # level 4
]

CELL = 13        # cell size px
GAP = 3          # gap between cells
RADIUS = 2       # corner radius
MARGIN_LEFT = 50
MARGIN_TOP = 50
ANIMATION_WAVE_DELAY = 0.012  # seconds per diagonal index


def level_for_count(count: int) -> int:
    """Map a contribution count to a 0-4 level."""
    if count == 0:
        return 0
    elif count <= 2:
        return 1
    elif count <= 5:
        return 2
    elif count <= 9:
        return 3
    else:
        return 4


def build_heatmap_svg(data: dict) -> str:
    daily = data.get("daily", [])
    stats = data.get("stats", {})

    if not daily:
        print("⚠️  No daily data in contributions.json")
        sys.exit(1)

    # ── Organize into weeks ───────────────────────────────────────
    from datetime import datetime, timedelta

    # Parse dates
    entries = {}
    for d in daily:
        entries[d["date"]] = d

    # Find the range: last 53 weeks ending on the most recent Saturday
    last_date_str = daily[-1]["date"]
    last_date = datetime.strptime(last_date_str, "%Y-%m-%d")

    # Go to end of the week (Saturday)
    end_date = last_date + timedelta(days=(5 - last_date.weekday()) % 7)
    start_date = end_date - timedelta(weeks=53) + timedelta(days=1)

    weeks = []  # list of lists, each inner list = 7 days (Sun-Sat)
    current = start_date
    # Align to Sunday
    while current.weekday() != 6:  # 6 = Sunday
        current -= timedelta(days=1)

    while current <= end_date:
        week = []
        for dow in range(7):
            d = current + timedelta(days=dow)
            date_str = d.strftime("%Y-%m-%d")
            entry = entries.get(date_str)
            count = entry["count"] if entry else 0
            level = entry.get("level", level_for_count(count)) if entry else 0
            # Ensure level is consistent
            if level == 0 and count > 0:
                level = level_for_count(count)
            week.append({"date": date_str, "count": count, "level": level})
        weeks.append(week)
        current += timedelta(days=7)

    num_weeks = len(weeks)

    # ── SVG dimensions ────────────────────────────────────────────
    grid_w = num_weeks * (CELL + GAP) - GAP
    grid_h = 7 * (CELL + GAP) - GAP
    svg_w = MARGIN_LEFT + grid_w + 40
    svg_h = MARGIN_TOP + grid_h + 80  # extra for legend + stats

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
                 f'viewBox="0 0 {svg_w} {svg_h}" '
                 f'width="{svg_w}" height="{svg_h}">')

    # ── Cells & Animations ───────────────────────────────────────
    max_diag = num_weeks + 6  # max diagonal index
    duration = 8.0
    
    parts.append("<style>")
    parts.append(f"  svg {{ background: {BG}; }}")
    parts.append(f"  text {{ font-family: {FONT}; fill: {TEXT_COLOR}; }}")
    parts.append(f"  .mono {{ font-family: {MONO}; }}")
    parts.append(f"  .label {{ font-size: 11px; fill: {LABEL_COLOR}; }}")
    parts.append(f"  .stat {{ font-size: 12px; fill: {TEXT_COLOR}; }}")
    parts.append(f"  .stat-val {{ fill: #c9d1d9; font-weight: 600; }}")
    
    # Generate per-diagonal keyframes for 8-second cycle
    for diag in range(max_diag):
        delay = diag * ANIMATION_WAVE_DELAY
        start_pct = (delay / duration) * 100
        pop1_pct = ((delay + 0.20) / duration) * 100
        pop2_pct = ((delay + 0.25) / duration) * 100
        
        parts.append(f"  @keyframes pop{diag} {{")
        parts.append(f"    0%, {start_pct:.2f}% {{ opacity: 0; transform: scale(0); }}")
        parts.append(f"    {pop1_pct:.2f}% {{ opacity: 1; transform: scale(1.1); }}")
        parts.append(f"    {pop2_pct:.2f}%, 95% {{ opacity: 1; transform: scale(1); }}")
        parts.append(f"    96%, 100% {{ opacity: 0; transform: scale(0); }}")
        parts.append(f"  }}")
        
    parts.append("</style>")

    # ── Day labels (Mon, Wed, Fri) ────────────────────────────────
    day_labels = ["", "Mon", "", "Wed", "", "Fri", ""]
    for i, label in enumerate(day_labels):
        if label:
            y = MARGIN_TOP + i * (CELL + GAP) + CELL - 2
            parts.append(f'<text class="label" x="{MARGIN_LEFT - 8}" y="{y}" text-anchor="end">{label}</text>')

    # ── Month labels ──────────────────────────────────────────────
    months_shown = set()
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for wi, week in enumerate(weeks):
        first_day = datetime.strptime(week[0]["date"], "%Y-%m-%d")
        month_key = (first_day.year, first_day.month)
        if month_key not in months_shown and first_day.day <= 7:
            months_shown.add(month_key)
            x = MARGIN_LEFT + wi * (CELL + GAP)
            parts.append(f'<text class="label" x="{x}" y="{MARGIN_TOP - 10}">'
                         f'{month_names[first_day.month - 1]}</text>')

    # ── Cells ─────────────────────────────────────────────────────
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            x = MARGIN_LEFT + wi * (CELL + GAP)
            y = MARGIN_TOP + di * (CELL + GAP)
            color = PALETTE[min(day["level"], len(PALETTE) - 1)]
            diag = wi + di

            parts.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'rx="{RADIUS}" ry="{RADIUS}" fill="{color}" '
                f'opacity="0" style="animation: pop{diag} {duration}s ease-out infinite; '
                f'transform-origin: {x + CELL/2}px {y + CELL/2}px;">'
                f'<title>{day["date"]}: {day["count"]} contribution{"s" if day["count"] != 1 else ""}</title>'
                f'</rect>'
            )

    # ── Legend ────────────────────────────────────────────────────
    legend_y = MARGIN_TOP + grid_h + 20
    legend_x = svg_w - 200

    parts.append(f'<text class="label" x="{legend_x}" y="{legend_y + CELL - 2}">Less</text>')
    lx = legend_x + 30
    for li, c in enumerate(PALETTE):
        parts.append(
            f'<rect x="{lx + li * (CELL + 2)}" y="{legend_y}" '
            f'width="{CELL}" height="{CELL}" rx="{RADIUS}" fill="{c}" />'
        )
    parts.append(f'<text class="label" x="{lx + len(PALETTE) * (CELL + 2) + 4}" y="{legend_y + CELL - 2}">More</text>')

    # ── Stats footer ──────────────────────────────────────────────
    stats_y = legend_y + 30
    total = stats.get("total_contributions", sum(d["count"] for d in daily))
    streak = stats.get("current_streak", 0)
    longest = stats.get("longest_streak", 0)

    parts.append(f'<text class="stat mono" x="{MARGIN_LEFT}" y="{stats_y}">'
                 f'<tspan class="stat-val">{total:,}</tspan> contributions  ·  '
                 f'<tspan class="stat-val">{streak}</tspan> day streak  ·  '
                 f'<tspan class="stat-val">{longest}</tspan> longest streak'
                 f'</text>')

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    repo_root = Path(__file__).resolve().parent.parent
    src = repo_root / "data" / "contributions.json"
    dst = repo_root / "contrib-heatmap.svg"

    if not src.exists():
        print(f"❌ {src} not found. Run fetch_contributions.py first.")
        sys.exit(1)

    print(f"📊 Loading contribution data from {src.name} …")
    data = json.loads(src.read_text(encoding="utf-8"))
    svg_content = build_heatmap_svg(data)
    dst.write_text(svg_content, encoding="utf-8")
    print(f"✅ Saved {dst.name} ({dst.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
