#!/usr/bin/env python3
"""Release gate for the text-first GitHub profile."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
GENERATOR = ROOT / "scripts" / "generate_profile.py"
LIVE = ROOT / "data" / "live.json"

APPROVED_IMAGE_PREFIXES = (
    "https://user-images.githubusercontent.com/",
    "https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/",
)


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def main() -> None:
    readme = README.read_text(encoding="utf-8")
    lower = readme.lower()
    if "profile-readme:v5" not in readme:
        fail("README version marker is not v5")
    for marker in ("profile-live:start", "profile-live:end", "profile-footer:start", "profile-footer:end"):
        if readme.count(marker) != 1:
            fail(f"expected exactly one {marker}")
    sections = ("## ↗ Open source / live", "## ✦ Selected work", "### 🧭 Current lines", "## 🛸 Side quests")
    positions = []
    for section in sections:
        if readme.count(section) != 1:
            fail(f"expected exactly one {section}")
        positions.append(readme.index(section))
    if positions != sorted(positions):
        fail("README section order changed")
    banned = ("./assets/", "github-readme-stats", "typing-svg", "shields.io", "profile-trophy", "hero-field-source", "liquid glass", "live signal", "field 01", "gradient-svg-generator")
    for token in banned:
        if token in lower:
            fail(f"README contains banned visual/template token: {token}")
    live = readme.split("<!-- profile-live:start -->", 1)[1].split("<!-- profile-live:end -->", 1)[0]
    if len(re.findall(r"https://github\.com/[^)\s]+/pull/\d+", live)) != 3:
        fail("live block must list exactly three upstream PRs")
    if not re.search(r"<strong>\d+</strong> contributions in \d{4}", live):
        fail("live block is missing contribution count")
    if "active public repos" not in live or "upstream PRs" not in live:
        fail("live block is missing core metrics")
    if not re.search(r"refreshed \d{1,2} [A-Z][a-z]{2} · \d{2}:\d{2} SGT", live):
        fail("live block lacks freshness timestamp")
    if readme.count("Xinchen Lee") != 1:
        fail("full name should appear exactly once")
    if "[XCAD](https://github.com/teddyli18000/XCAD)" not in readme:
        fail("Selected work must include XCAD")
    if "### 🔬 [Millikan AI]" in readme:
        fail("Millikan AI should not be visually privileged")
    remote_images = re.findall(r'<img[^>]+src="(https://[^\"]+)"', readme)
    if any(not url.startswith(APPROVED_IMAGE_PREFIXES) for url in remote_images):
        fail("remote image uses an unapproved host")
    if len(remote_images) > 10:
        fail("keep remote imagery lightweight")
    animated_fluent = [url for url in remote_images if "Animated-Fluent-Emojis" in url]
    if not 7 <= len(animated_fluent) <= 9:
        fail("use a restrained but visible set of animated Fluent emoji accents")
    data = json.loads(LIVE.read_text(encoding="utf-8"))
    for key in ("year", "contributions", "active_public_repos", "upstream_prs", "updated_at"):
        if key not in data:
            fail(f"live.json missing {key}")
    if len(data.get("selected_external", [])) != 3:
        fail("live.json must retain three selected upstream PRs")
    generator = GENERATOR.read_text(encoding="utf-8")
    for token in ("live_markdown", "replace_block", "selected_external", "visible_signature", "refreshed"):
        if token not in generator:
            fail(f"generator missing {token}")
    if "assets/" in generator or "<svg" in generator:
        fail("generator must remain text/data only")
    print("PASS: v5 profile, truthful live block, lightweight public motion accents")


if __name__ == "__main__":
    main()
