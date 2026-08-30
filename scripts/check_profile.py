#!/usr/bin/env python3
"""Release gate for the compact, component-driven GitHub profile."""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
GENERATOR = ROOT / "scripts" / "generate_profile.py"
LIVE = ROOT / "data" / "live.json"
STATS_CARD = ROOT / "assets" / "stats-card.svg"
LANGUAGES_CARD = ROOT / "assets" / "languages-card.svg"
REFRESH_WORKFLOW = ROOT / ".github" / "workflows" / "refresh-profile.yml"
SNAKE_WORKFLOW = ROOT / ".github" / "workflows" / "snake.yml"

APPROVED_IMAGE_PREFIXES = (
    "https://user-images.githubusercontent.com/",
    "https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/",
    "https://img.shields.io/badge/",
    "https://raw.githubusercontent.com/teddyli18000/teddyli18000/output/",
)


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def check_generated_svg(path: Path) -> None:
    if not path.is_file():
        fail(f"missing generated card: {path.name}")
    text = path.read_text(encoding="utf-8")
    ET.fromstring(text)
    if path.stat().st_size < 1000:
        fail(f"{path.name} looks like an error/empty card")
    if path.stat().st_size > 256 * 1024:
        fail(f"{path.name} is unexpectedly large")


def main() -> None:
    readme = README.read_text(encoding="utf-8")
    lower = readme.lower()
    if "profile-readme:v8" not in readme:
        fail("README version marker is not v8")
    for marker in ("profile-live:start", "profile-live:end", "profile-footer:start", "profile-footer:end"):
        if readme.count(marker) != 1:
            fail(f"expected exactly one {marker}")

    if "mostly building · occasionally overengineering · sometimes both" in readme:
        fail("removed top microcopy reappeared")
    if "⌁" in readme:
        fail("footer must not use decorative filler glyphs")

    open_source = readme.find("## ↗ Open source / live")
    stack = readme.find("## 🛠 Tech stack")
    snake = readme.find("## 🐍 Contribution trail")
    if min(open_source, stack, snake) < 0 or not (open_source < stack < snake):
        fail("major README section order changed")

    for heading in ("<h3>✦ Selected work</h3>", "<h3>🧭 Current</h3>", "<h3>🛸 Side quests</h3>"):
        if readme.count(heading) != 1:
            fail(f"three-column block missing {heading}")
    if readme.count('<td width="') != 3 or readme.count('valign="top"') != 3:
        fail("Selected work / Current / Side quests must stay a three-column block")

    for project in ("AiForMillikan", "screen-clone-manager", "baidu-drive-mover", "XCAD"):
        if f"teddyli18000/{project}" not in readme:
            fail(f"Selected work missing {project}")
    for project in ("outlook-mail-helper", "medical-img-preparer", "millikan-drop-processor"):
        if f"teddyli18000/{project}" not in readme:
            fail(f"Side quests missing {project}")

    local_images = re.findall(r'<img[^>]+src="(\./assets/[^\"]+)"', readme)
    if local_images != ["./assets/stats-card.svg", "./assets/languages-card.svg"]:
        fail("Open source block must use the two locally generated mature stats cards")
    check_generated_svg(STATS_CARD)
    check_generated_svg(LANGUAGES_CARD)

    live = readme.split("<!-- profile-live:start -->", 1)[1].split("<!-- profile-live:end -->", 1)[0]
    if len(re.findall(r"https://github\.com/[^)\s]+/pull/\d+", live)) != 3:
        fail("live block must list exactly three upstream PRs")
    if "Outside my repos" not in live:
        fail("live block lost Outside my repos")

    if readme.count("Xinchen Lee") != 1:
        fail("full name should appear exactly once")

    remote_images = re.findall(r'<img[^>]+src="(https://[^\"]+)"', readme)
    if any(not url.startswith(APPROVED_IMAGE_PREFIXES) for url in remote_images):
        fail("remote image uses an unapproved host")
    shields = [url for url in remote_images if url.startswith("https://img.shields.io/badge/")]
    if not 8 <= len(shields) <= 12:
        fail("Tech stack should use 8-12 focused badges")
    fluent = [url for url in remote_images if "Animated-Fluent-Emojis" in url]
    if not 4 <= len(fluent) <= 6:
        fail("keep animated emoji restrained to the hero")
    snake_urls = re.findall(r'https://raw\.githubusercontent\.com/teddyli18000/teddyli18000/output/github-snake(?:-dark)?\.svg', readme)
    if len(snake_urls) < 2:
        fail("Contribution trail must include light/dark snake assets")

    footer = readme.split("<!-- profile-footer:start -->", 1)[1].split("<!-- profile-footer:end -->", 1)[0]
    if "<em>“" not in footer or "”</em>" not in footer:
        fail("footer should render a considered English quote/line")

    for token in ("typing-svg", "profile-trophy", "gradient-svg-generator", "visitor counter"):
        if token.lower() in lower:
            fail(f"README contains banned template token: {token}")

    if not REFRESH_WORKFLOW.is_file():
        fail("refresh workflow is missing")
    refresh = REFRESH_WORKFLOW.read_text(encoding="utf-8")
    for token in (
        "stats-organization/github-readme-stats-action@v2",
        "card: stats",
        "card: top-langs",
        "include_all_commits=true",
        "assets/stats-card.svg",
        "assets/languages-card.svg",
        'cron: "17 */2 * * *"',
    ):
        if token not in refresh:
            fail(f"refresh workflow missing {token}")

    if not SNAKE_WORKFLOW.is_file():
        fail("snake workflow is missing")
    snake_workflow = SNAKE_WORKFLOW.read_text(encoding="utf-8")
    for token in ("Platane/snk@v3", "target_branch: output", "github-snake-dark.svg"):
        if token not in snake_workflow:
            fail(f"snake workflow missing {token}")

    data = json.loads(LIVE.read_text(encoding="utf-8"))
    if len(data.get("selected_external", [])) != 3:
        fail("live.json must retain three selected upstream PRs")
    if not data.get("updated_at"):
        fail("live.json must retain updated_at")

    generator = GENERATOR.read_text(encoding="utf-8")
    if "activity_card_svg" in generator or "contributionCalendar" in generator:
        fail("custom generic stats generation must stay removed")
    for token in ("fetch_external", "footer_markdown", "assets/stats-card.svg", "assets/languages-card.svg"):
        if token not in generator:
            fail(f"generator missing {token}")

    print("PASS: v8 three-column profile with local mature stats cards and contribution snake")


if __name__ == "__main__":
    main()
