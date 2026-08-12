#!/usr/bin/env python3
"""Fast local release gate for the GitHub profile README."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
ASSETS = ROOT / "assets"


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def main() -> None:
    readme = README.read_text(encoding="utf-8")
    for marker in ("profile-live:start", "profile-live:end", "profile-footer:start", "profile-footer:end"):
        if readme.count(marker) != 1:
            fail(f"expected exactly one {marker} marker")
    if "millikan-work" in readme:
        fail("specific project imagery must not be embedded")
    if "<script" in readme.lower() or "javascript:" in readme.lower():
        fail("README must remain script-free")

    local_refs = re.findall(r'(?:src|srcset)="\./([^" ]+)"', readme)
    missing = [ref for ref in local_refs if not (ROOT / ref).is_file()]
    if missing:
        fail(f"missing referenced assets: {missing}")

    expected_rasters = {
        "hero-light.gif": (960, 420),
        "hero-dark.gif": (960, 420),
        "hero-light.png": (960, 420),
        "hero-dark.png": (960, 420),
        "live-signal-light.gif": (960, 150),
        "live-signal-dark.gif": (960, 150),
        "sidequest-light.gif": (960, 150),
        "sidequest-dark.gif": (960, 150),
    }
    for name, dimensions in expected_rasters.items():
        path = ASSETS / name
        with Image.open(path) as image:
            if image.size != dimensions:
                fail(f"{name} is {image.size}, expected {dimensions}")
            if path.suffix == ".gif" and getattr(image, "n_frames", 1) < 16:
                fail(f"{name} has too few animation frames")
        if path.stat().st_size > 6 * 1024 * 1024:
            fail(f"{name} exceeds the 6 MiB per-asset budget")

    for name in ("live-light.svg", "live-dark.svg"):
        ET.parse(ASSETS / name)
    published = [path for path in ASSETS.iterdir() if not path.name.startswith("millikan-work-")]
    total = sum(path.stat().st_size for path in published)
    if total > 16 * 1024 * 1024:
        fail(f"published assets exceed 16 MiB ({total / 1024 / 1024:.2f} MiB)")
    print(
        f"PASS: {len(local_refs)} local references resolve; "
        f"published assets {total / 1024 / 1024:.2f} MiB; README is GitHub-native."
    )


if __name__ == "__main__":
    main()

