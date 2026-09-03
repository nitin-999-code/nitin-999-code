#!/usr/bin/env python3
"""
fetch_contributions.py — Fetch real public GitHub contribution data.

Scrapes https://github.com/users/nitin-999-code/contributions
using requests + BeautifulSoup. No GitHub token required.

Outputs: data/contributions.json
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = "nitin-999-code"
URL = f"https://github.com/users/{USERNAME}/contributions"


def fetch_contribution_data() -> list[dict]:
    """Scrape GitHub contribution calendar and return daily records."""
    print(f"🌐 Fetching contributions from {URL} …")

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; GitHubProfileReadme/1.0)",
        "Accept": "text/html",
    }
    resp = requests.get(URL, headers=headers, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # GitHub renders contribution cells as <td> elements with data-date and data-level
    cells = soup.select("td.ContributionCalendar-day")

    if not cells:
        # Fallback: try tool-tip / table cell approach
        cells = soup.select("table.ContributionCalendar-grid td[data-date]")

    if not cells:
        print("⚠️  Could not find contribution cells in GitHub HTML.")
        print("    GitHub may have changed its markup. Dumping first 2000 chars:")
        print(resp.text[:2000])
        sys.exit(1)

    daily = []
    for cell in cells:
        date_str = cell.get("data-date")
        if not date_str:
            continue

        # Contribution level (0-4)
        level = int(cell.get("data-level", 0))

        # Try to get count from tool-tip child or aria-label or inner span
        count = 0
        # Check for a <tool-tip> or <span> child with text like "5 contributions…"
        tip = cell.find("tool-tip") or cell.find("span", class_="sr-only")
        if tip:
            text = tip.get_text(strip=True)
            # Parse "5 contributions on …" or "No contributions on …"
            if text.lower().startswith("no "):
                count = 0
            else:
                try:
                    count = int(text.split()[0].replace(",", ""))
                except (ValueError, IndexError):
                    count = level  # fallback

        # If count is still 0 but level > 0, use level as proxy
        if count == 0 and level > 0:
            count = level

        daily.append({
            "date": date_str,
            "count": count,
            "level": level,
        })

    # Sort by date
    daily.sort(key=lambda d: d["date"])
    return daily


def compute_stats(daily: list[dict]) -> dict:
    """Derive useful statistics from daily contribution data."""
    if not daily:
        return {}

    total = sum(d["count"] for d in daily)
    counts = [d["count"] for d in daily]
    dates = [d["date"] for d in daily]

    # Best day
    best_idx = max(range(len(counts)), key=lambda i: counts[i])
    best_day = {"date": dates[best_idx], "count": counts[best_idx]}

    # Streaks
    current_streak = 0
    longest_streak = 0
    streak = 0
    for d in daily:
        if d["count"] > 0:
            streak += 1
            longest_streak = max(longest_streak, streak)
        else:
            streak = 0

    # Current streak (count backwards from most recent)
    for d in reversed(daily):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    # Monthly totals
    monthly = {}
    for d in daily:
        month = d["date"][:7]  # YYYY-MM
        monthly[month] = monthly.get(month, 0) + d["count"]

    # Average per day (non-zero days)
    active_days = sum(1 for c in counts if c > 0)
    avg_per_active_day = round(total / active_days, 2) if active_days else 0

    return {
        "total_contributions": total,
        "days_tracked": len(daily),
        "active_days": active_days,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "avg_per_active_day": avg_per_active_day,
        "monthly_totals": monthly,
    }


def main():
    repo_root = Path(__file__).resolve().parent.parent
    data_dir = repo_root / "data"
    data_dir.mkdir(exist_ok=True)
    dst = data_dir / "contributions.json"

    daily = fetch_contribution_data()

    if not daily:
        print("❌ No contribution data found. Aborting.")
        sys.exit(1)

    stats = compute_stats(daily)

    payload = {
        "username": USERNAME,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "stats": stats,
        "daily": daily,
    }

    dst.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"✅ Saved {dst.name} ({len(daily)} days, {stats.get('total_contributions', '?')} total contributions)")
    print(f"   Current streak: {stats.get('current_streak', 0)} days")
    print(f"   Longest streak: {stats.get('longest_streak', 0)} days")
    print(f"   Best day: {stats.get('best_day', {}).get('date', '?')} ({stats.get('best_day', {}).get('count', 0)} contributions)")


if __name__ == "__main__":
    main()
