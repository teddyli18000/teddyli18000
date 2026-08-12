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
GENERATOR = ROOT / "scripts" / "generate_profile.py"
ACTIVE_REPOS_LABEL = "ACTIVE PUBLIC REPOS"


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def main() -> None:
    readme = README.read_text(encoding="utf-8")
    for marker in ("profile-live:start", "profile-live:end", "profile-footer:start", "profile-footer:end"):
        if readme.count(marker) != 1:
            fail(f"expected exactly one {marker} marker")
    if "millikan-work" in readme:
        fail("specific project imagery must not be embedded")
    if "live-signal-" in readme:
        fail("the standalone live-signal GIF must not be embedded")
    if "public builds" in readme.lower():
        fail("README must use active public repositories terminology")
    if "active public repositories" not in readme.lower():
        fail("README is missing active public repositories terminology")
    if "<script" in readme.lower() or "javascript:" in readme.lower():
        fail("README must remain script-free")

    generator = GENERATOR.read_text(encoding="utf-8")
    if ACTIVE_REPOS_LABEL not in generator:
        fail(f"generator must emit {ACTIVE_REPOS_LABEL}")
    if "PUBLIC BUILDS" in generator:
        fail("generator contains stale public builds terminology")

    local_refs = re.findall(r'(?:src|srcset)="\./([^" ]+)"', readme)
    missing = [ref for ref in local_refs if not (ROOT / ref).is_file()]
    if missing:
        fail(f"missing referenced assets: {missing}")

    expected_rasters = {
        "hero-light.gif": (960, 320),
        "hero-dark.gif": (960, 320),
        "hero-light.png": (960, 320),
        "hero-dark.png": (960, 320),
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
        svg_text = (ASSETS / name).read_text(encoding="utf-8")
        ET.parse(ASSETS / name)
        if ACTIVE_REPOS_LABEL not in svg_text:
            fail(f"{name} is missing {ACTIVE_REPOS_LABEL} metric")
        if "PUBLIC BUILDS" in svg_text:
            fail(f"{name} contains stale public builds terminology")
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
