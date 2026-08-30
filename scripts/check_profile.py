#!/usr/bin/env python3
"""Release gate for the compact, data-driven GitHub profile."""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
GENERATOR = ROOT / "scripts" / "generate_profile.py"
LIVE = ROOT / "data" / "live.json"
ACTIVITY_CARD = ROOT / "assets" / "activity-card.svg"
LANGUAGES_CARD = ROOT / "assets" / "languages-card.svg"
SNAKE_WORKFLOW = ROOT / ".github" / "workflows" / "snake.yml"

APPROVED_IMAGE_PREFIXES = (
    "https://user-images.githubusercontent.com/",
    "https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/",
    "https://img.shields.io/badge/",
    "https://raw.githubusercontent.com/teddyli18000/teddyli18000/output/",
)


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def check_card(path: Path, width: str, height: str, tokens: tuple[str, ...]) -> None:
    if not path.is_file():
        fail(f"missing generated card: {path.name}")
    text = path.read_text(encoding="utf-8")
    root = ET.fromstring(text)
    if root.attrib.get("width") != width or root.attrib.get("height") != height:
        fail(f"{path.name} must stay {width}x{height}")
    for token in tokens:
        if token not in text:
            fail(f"{path.name} missing {token}")
    if path.stat().st_size > 64 * 1024:
        fail(f"{path.name} is too large")


def main() -> None:
    readme = README.read_text(encoding="utf-8")
    lower = readme.lower()
    if "profile-readme:v7" not in readme:
        fail("README version marker is not v7")
    for marker in ("profile-live:start", "profile-live:end", "profile-footer:start", "profile-footer:end"):
        if readme.count(marker) != 1:
            fail(f"expected exactly one {marker}")

    sections = (
        "## ↗ Open source / live",
        "## ✦ Selected work",
        "### 🧭 Current lines",
        "## 🛠 Tech stack",
        "## 🛸 Side quests",
        "## 🐍 Contribution trail",
    )
    positions = []
    for section in sections:
        if readme.count(section) != 1:
            fail(f"expected exactly one {section}")
        positions.append(readme.index(section))
    if positions != sorted(positions):
        fail("README section order changed")

    for token in ("github-readme-stats", "typing-svg", "profile-trophy", "gradient-svg-generator", "A+", "visitor counter"):
        if token.lower() in lower:
            fail(f"README contains banned template/gamified token: {token}")

    local_images = re.findall(r'<img[^>]+src="(\./assets/[^\"]+)"', readme)
    if local_images != ["./assets/activity-card.svg", "./assets/languages-card.svg"]:
        fail("live block must use exactly the activity and language cards")

    check_card(
        ACTIVITY_CARD,
        "470",
        "240",
        ("Public activity", "Contributions", "Commits", "Public repos", "Upstream PRs", "MERGED"),
    )
    check_card(LANGUAGES_CARD, "470", "240", ("Code mix", "ACTIVE PUBLIC REPOS"))

    live = readme.split("<!-- profile-live:start -->", 1)[1].split("<!-- profile-live:end -->", 1)[0]
    if len(re.findall(r"https://github\.com/[^)\s]+/pull/\d+", live)) != 3:
        fail("live block must list exactly three upstream PRs")
    if "Outside my repos" not in live:
        fail("live block lost Outside my repos")

    if readme.count("Xinchen Lee") != 1:
        fail("full name should appear exactly once")
    for project in ("AiForMillikan", "screen-clone-manager", "baidu-drive-mover", "XCAD"):
        if f"teddyli18000/{project}" not in readme:
            fail(f"Selected work missing {project}")

    selected = readme.split("## ✦ Selected work", 1)[1].split("### 🧭 Current lines", 1)[0]
    if selected.count("\n-") != 4:
        fail("Selected work should stay four compact bullets")
    current = readme.split("### 🧭 Current lines", 1)[1].split("---", 1)[0]
    if current.count("\n-") > 1:
        fail("Current lines should stay compact")
    side = readme.split("## 🛸 Side quests", 1)[1].split("---", 1)[0]
    if side.count("\n-") != 3:
        fail("Side quests should stay three compact bullets")

    remote_images = re.findall(r'<img[^>]+src="(https://[^\"]+)"', readme)
    if any(not url.startswith(APPROVED_IMAGE_PREFIXES) for url in remote_images):
        fail("remote image uses an unapproved host")
    shields = [url for url in remote_images if url.startswith("https://img.shields.io/badge/")]
    if not 8 <= len(shields) <= 12:
        fail("Tech stack should use 8-12 focused badges")
    fluent = [url for url in remote_images if "Animated-Fluent-Emojis" in url]
    if not 7 <= len(fluent) <= 9:
        fail("keep the existing restrained animated emoji set")
    snake_urls = re.findall(r'https://raw\.githubusercontent\.com/teddyli18000/teddyli18000/output/github-snake(?:-dark)?\.svg', readme)
    if len(snake_urls) < 2:
        fail("Contribution trail must include light/dark snake assets")

    if not SNAKE_WORKFLOW.is_file():
        fail("snake workflow is missing")
    snake_workflow = SNAKE_WORKFLOW.read_text(encoding="utf-8")
    for token in ("Platane/snk@v3", "target_branch: output", "github-snake-dark.svg"):
        if token not in snake_workflow:
            fail(f"snake workflow missing {token}")

    data = json.loads(LIVE.read_text(encoding="utf-8"))
    for key in ("year", "contributions", "active_public_repos", "upstream_prs", "updated_at"):
        if key not in data:
            fail(f"live.json missing {key}")
    if len(data.get("selected_external", [])) != 3:
        fail("live.json must retain three selected upstream PRs")

    generator = GENERATOR.read_text(encoding="utf-8")
    for token in ("totalCommitContributions", "languages(first:20", "languages_card_svg", "activity_card_svg", "visible_signature"):
        if token not in generator:
            fail(f"generator missing {token}")

    print("PASS: v7 compact dashboard, live cards, focused stack, contribution snake")


if __name__ == "__main__":
    main()
