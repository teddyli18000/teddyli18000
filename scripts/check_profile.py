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
POLISHER = ROOT / "scripts" / "polish_cards.py"
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


def check_generated_svg(path: Path, expected_height: str = "190") -> str:
    if not path.is_file():
        fail(f"missing generated card: {path.name}")
    text = path.read_text(encoding="utf-8")
    root = ET.fromstring(text)
    if root.attrib.get("width") != "470" or root.attrib.get("height") != expected_height:
        fail(f"{path.name} must stay 470x{expected_height}")
    if path.stat().st_size < 1000:
        fail(f"{path.name} looks like an error/empty card")
    if path.stat().st_size > 256 * 1024:
        fail(f"{path.name} is unexpectedly large")
    return text


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

    stats = check_generated_svg(STATS_CARD)
    langs = check_generated_svg(LANGUAGES_CARD)
    for token in ("Total Commits:", "Total PRs:", "Total PRs Merged:", "Total Contributions:", "MERGED"):
        if token not in stats:
            fail(f"stats card missing {token}")
    if "Contributed to (last year):" in stats or re.search(r'percentile-top-header"[^>]*>\s*Top', stats, flags=re.S):
        fail("stats card regressed to weak/ambiguous metrics")
    if not re.search(r'data-testid="percentile-rank-value"[^>]*>\s*\d+%', stats, flags=re.S):
        fail("stats card merge-rate ring is missing")
    if not re.search(r'data-testid="contribs"[^>]*>\s*[1-9][0-9,.kKmM]*', stats, flags=re.S):
        fail("stats card full-history contributions are missing")

    lang_colors = re.findall(r'data-testid="lang-progress".*?fill="(#[0-9A-Fa-f]{6})"', langs, flags=re.S)
    if len(set(lang_colors)) < 8:
        fail("language card needs eight clearly distinct progress colors")

    live = readme.split("<!-- profile-live:start -->", 1)[1].split("<!-- profile-live:end -->", 1)[0]
    if len(re.findall(r"https://github\.com/[^)\s]+/pull/\d+", live)) != 3:
        fail("live block must list exactly three upstream PRs")
    if "Outside my repos" not in live:
        fail("live block lost Outside my repos")
    if not re.search(r"<sub>↻ refreshed \d{1,2} [A-Z][a-z]{2} \d{4} · \d{2}:\d{2} SGT</sub>", live):
        fail("live block must show its last successful refresh time")

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
        "vn7n24fzkq/github-profile-summary-cards@release",
        "card: stats",
        "card: top-langs",
        "include_all_commits=true",
        "rank_icon=percentile",
        "line_height=29",
        "python scripts/polish_cards.py",
        "assets/stats-card.svg",
        "assets/languages-card.svg",
        'cron: "7 * * * *"',
    ):
        if token not in refresh:
            fail(f"refresh workflow missing {token}")
    if "agent/profile-v7-compact-dashboard" in refresh:
        fail("preview-only branch push trigger must not ship")

    if not POLISHER.is_file():
        fail("card polisher is missing")
    polisher = POLISHER.read_text(encoding="utf-8")
    for token in ("Total Contributions:", "MERGED", "PALETTE", "profile-summary-card-output"):
        if token not in polisher:
            fail(f"card polisher missing {token}")

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
    for token in ("fetch_external", "footer_markdown", "assets/stats-card.svg", "assets/languages-card.svg", "↻ refreshed"):
        if token not in generator:
            fail(f"generator missing {token}")

    print("PASS: v8 three-column profile with mature stats data, contribution total, merge ring, contrast languages, snake, and live refresh stamp")


if __name__ == "__main__":
    main()
