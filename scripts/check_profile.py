#!/usr/bin/env python3
"""Fast local release gate for the Living Editorial Field profile README."""

from __future__ import annotations

import json
import re
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

from restyle_live import main as restyle_live

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
ASSETS = ROOT / "assets"
GENERATOR = ROOT / "scripts" / "generate_profile.py"
LIVE = ROOT / "data" / "live.json"

HERO_SOURCES = (
    "hero-light.gif",
    "hero-dark.gif",
    "hero-light.png",
    "hero-dark.png",
    "hero-narrow-light.gif",
    "hero-narrow-dark.gif",
    "hero-narrow-light.png",
    "hero-narrow-dark.png",
)
MILLIKAN_SOURCES = (
    "millikan-mark-light.gif",
    "millikan-mark-dark.gif",
    "millikan-mark-light.png",
    "millikan-mark-dark.png",
)
SIDEQUEST_SOURCES = (
    "sidequest-light.gif",
    "sidequest-dark.gif",
    "sidequest-light.png",
    "sidequest-dark.png",
)
LIVE_SOURCES = ("live-light.svg", "live-dark.svg")


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def require_refs(readme: str, names: tuple[str, ...]) -> None:
    missing_refs = [name for name in names if f"./assets/{name}" not in readme]
    if missing_refs:
        fail(f"README is missing required asset references: {missing_refs}")
    missing_files = [name for name in names if not (ASSETS / name).is_file()]
    if missing_files:
        fail(f"missing referenced assets: {missing_files}")


def gif_frame_count(data: bytes, name: str) -> int:
    if len(data) < 13:
        fail(f"{name} has a truncated logical screen descriptor")
    packed = data[10]
    offset = 13
    if packed & 0x80:
        offset += 3 * (2 ** ((packed & 0x07) + 1))
    frames = 0
    while offset < len(data):
        block = data[offset]
        if block == 0x3B:
            return frames
        if block == 0x21:
            if offset + 2 > len(data):
                fail(f"{name} has a truncated extension block")
            offset += 2
        elif block == 0x2C:
            if offset + 10 > len(data):
                fail(f"{name} has a truncated image descriptor")
            local_packed = data[offset + 9]
            offset += 10
            if local_packed & 0x80:
                offset += 3 * (2 ** ((local_packed & 0x07) + 1))
            if offset >= len(data):
                fail(f"{name} is missing its LZW code size")
            offset += 1
            frames += 1
        else:
            fail(f"{name} contains an unexpected GIF block 0x{block:02x}")
        while True:
            if offset >= len(data):
                fail(f"{name} has a truncated data sub-block")
            size = data[offset]
            offset += 1
            if size == 0:
                break
            offset += size
            if offset > len(data):
                fail(f"{name} has an overlong data sub-block")
    fail(f"{name} is missing its GIF trailer")


def raster_dimensions(name: str) -> tuple[int, int, int]:
    path = ASSETS / name
    data = path.read_bytes()
    if path.suffix == ".png" and data[:8] == b"\x89PNG\r\n\x1a\n":
        width, height = struct.unpack(">II", data[16:24])
        return width, height, 1
    if path.suffix == ".gif" and data[:6] in {b"GIF87a", b"GIF89a"}:
        width, height = struct.unpack("<HH", data[6:10])
        return width, height, gif_frame_count(data, name)
    fail(f"{name} is not a readable PNG or GIF")


def check_raster(name: str, expected: tuple[int, int], min_frames: int) -> None:
    width, height, frames = raster_dimensions(name)
    if (width, height) != expected:
        fail(f"{name} is {(width, height)}, expected {expected}")
    if name.endswith(".gif") and frames < min_frames:
        fail(f"{name} has too few animation frames ({frames})")
    if (ASSETS / name).stat().st_size > 6 * 1024 * 1024:
        fail(f"{name} exceeds the 6 MiB per-asset budget")


def check_svg(name: str) -> None:
    path = ASSETS / name
    text = path.read_text(encoding="utf-8")
    root = ET.fromstring(text)
    if root.attrib.get("width") not in {"960", "960px"}:
        fail(f"{name} must be 960px wide")
    if root.attrib.get("height") not in {"220", "220px"}:
        fail(f"{name} must be 220px high")
    if "LIVE SIGNAL" in text or "FIELD 01" in text:
        fail(f"{name} contains removed pseudo-technical labels")
    if len(re.findall(r'class="value"', text)) != 3:
        fail(f"{name} must contain exactly three metric values")
    if len(re.findall(r'class="label"', text)) != 3:
        fail(f"{name} must contain exactly three metric labels")
    if "<circle" in text:
        fail(f"{name} must not contain decorative status dots")
    if path.stat().st_size > 256 * 1024:
        fail(f"{name} exceeds the 256 KiB asset budget")


def main() -> None:
    # The daily generator owns truth; this local pass owns only presentation.
    restyle_live()
    readme = README.read_text(encoding="utf-8")
    lower = readme.lower()
    for marker in ("profile-live:start", "profile-live:end", "profile-footer:start", "profile-footer:end"):
        if readme.count(marker) != 1:
            fail(f"expected exactly one {marker} marker")
    if "millikan-work" in readme or "live-signal-" in readme:
        fail("README must not embed project screenshots or the old live-signal asset")
    if "the repository is the proof surface" in lower:
        fail("Millikan copy must stay editorial, not audit-like")
    if "motion and system references" in lower or "parts-bin" in lower:
        fail("README must not expose implementation reference details")
    if "<details" in lower or "<script" in lower or "javascript:" in lower:
        fail("README must remain GitHub-native and script-free")
    if re.search(r"^\s*\|.*\|\s*$", readme, flags=re.MULTILINE):
        fail("README must use a naturally reflowing ledger, not a table")

    sections = (
        "## Selected work",
        "### Current lines of work",
        "## Open source / live",
        "## Side quests",
    )
    positions = []
    for section in sections:
        if readme.count(section) != 1:
            fail(f"expected exactly one {section}")
        positions.append(readme.index(section))
    if positions != sorted(positions):
        fail("README sections are out of Living Editorial Field order")

    current = readme.split("### Current lines of work", 1)[1].split("## Open source / live", 1)[0]
    for phrase in ("small models", "AI developer infrastructure", "robotics & perception"):
        if phrase.lower() not in current.lower():
            fail(f"Current lines is missing {phrase}")

    live = readme.split("<!-- profile-live:start -->", 1)[1].split("<!-- profile-live:end -->", 1)[0]
    if "Outside my repos" not in live:
        fail("live block must retain Outside my repos")
    if len(re.findall(r"https://github\.com/[^)\s]+/pull/\d+", live)) != 3:
        fail("live block must list exactly three upstream pull requests")
    if not re.search(r"updated \d{1,2} [A-Z][a-z]{2} · \d{2}:\d{2} SGT", live):
        fail("live block is missing its generated timestamp")

    require_refs(readme, HERO_SOURCES)
    require_refs(readme, MILLIKAN_SOURCES)
    require_refs(readme, SIDEQUEST_SOURCES)
    require_refs(readme, LIVE_SOURCES)

    for name in ("hero-light.gif", "hero-dark.gif"):
        check_raster(name, (960, 300), 8)
    for name in ("hero-light.png", "hero-dark.png"):
        check_raster(name, (960, 300), 1)
    for name in ("hero-narrow-light.gif", "hero-narrow-dark.gif"):
        check_raster(name, (420, 180), 8)
    for name in ("hero-narrow-light.png", "hero-narrow-dark.png"):
        check_raster(name, (420, 180), 1)
    for name in ("millikan-mark-light.gif", "millikan-mark-dark.gif"):
        check_raster(name, (960, 56), 8)
    for name in ("millikan-mark-light.png", "millikan-mark-dark.png"):
        check_raster(name, (960, 56), 1)
    for name in ("sidequest-light.gif", "sidequest-dark.gif"):
        check_raster(name, (960, 70), 8)
    for name in ("sidequest-light.png", "sidequest-dark.png"):
        check_raster(name, (960, 70), 1)
    for name in LIVE_SOURCES:
        check_svg(name)

    data = json.loads(LIVE.read_text(encoding="utf-8"))
    for key in ("year", "contributions", "active_public_repos", "upstream_prs", "updated_at"):
        if key not in data:
            fail(f"data/live.json is missing {key}")
    if len(data.get("selected_external", [])) != 3:
        fail("data/live.json must retain three selected upstream PRs")

    generator = GENERATOR.read_text(encoding="utf-8")
    if "LIVE SIGNAL" in generator or "FIELD 01" in generator:
        fail("generator contains removed pseudo-technical labels")

    total = sum(path.stat().st_size for path in ASSETS.iterdir())
    if total > 20 * 1024 * 1024:
        fail(f"published assets exceed 20 MiB ({total / 1024 / 1024:.2f} MiB)")
    print(f"PASS: published assets {total / 1024 / 1024:.2f} MiB; profile contract holds.")


if __name__ == "__main__":
    main()
