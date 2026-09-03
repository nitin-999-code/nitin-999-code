#!/usr/bin/env python3
"""
prep_photo.py — Prepare source-photo.jpg for ASCII portrait generation.

Steps:
  1. Remove background using rembg
  2. Convert to grayscale
  3. Enhance contrast with OpenCV CLAHE
  4. Composite onto a white background
  5. Save as source-prepped.png
"""

import sys
import os
import numpy as np
from pathlib import Path

def main():
    # ── Resolve paths ─────────────────────────────────────────────
    repo_root = Path(__file__).resolve().parent.parent
    if len(sys.argv) > 1:
        src = Path(sys.argv[1])
        if not src.is_absolute():
            src = repo_root / src
    else:
        src = repo_root / "source-photo.jpg"

    dst = repo_root / "source-prepped.png"

    if not src.exists():
        print(f"❌ Source image not found: {src}")
        sys.exit(1)

    print(f"📷 Loading {src.name} …")

    # ── Step 1: Remove background ─────────────────────────────────
    from rembg import remove
    from PIL import Image
    import io

    raw_bytes = src.read_bytes()
    print("🔪 Removing background with rembg …")
    result_bytes = remove(raw_bytes)
    img_rgba = Image.open(io.BytesIO(result_bytes)).convert("RGBA")

    # ── Step 2: Composite onto white background ───────────────────
    white_bg = Image.new("RGBA", img_rgba.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, img_rgba).convert("RGB")

    # ── Step 3: Convert to grayscale ──────────────────────────────
    gray = composited.convert("L")

    # ── Step 4: Enhance contrast with CLAHE ───────────────────────
    import cv2

    gray_np = np.array(gray)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray_np)

    # ── Step 5: Save ──────────────────────────────────────────────
    result = Image.fromarray(enhanced)
    result.save(str(dst), "PNG")
    print(f"✅ Saved {dst.name} ({dst.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
