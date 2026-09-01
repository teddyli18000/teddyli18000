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
PROFILE_DETAILS = ROOT / "assets" / "profile-details.svg"
COMMIT_LANGS = ROOT / "assets" / "commit-languages-card.svg"
REFRESH_WORKFLOW = ROOT / ".github" / "workflows" / "profile-refresh.yml"
SNAKE_WORKFLOW = ROOT / ".github" / "workflows" / "snake.yml"

APPROVED_IMAGE_PREFIXES = (
    "https://user-images.githubusercontent.com/",
    "https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/",
    "https://img.shields.io/badge/",
    "https://raw.githubusercontent.com/teddyli18000/teddyli18000/output/",
)


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def check_svg(path: Path, width: str, height: str) -> str:
    if not path.is_file():
        fail(f"missing generated card: {path.name}")
    text = path.read_text(encoding="utf-8")
    root = ET.fromstring(text)
    if root.attrib.get("width") != width or root.attrib.get("height") != height:
        fail(f"{path.name} must stay {width}x{height}")
    if path.stat().st_size < 1000:
        fail(f"{path.name} looks like an error/empty card")
    if path.stat().st_size > 384 * 1024:
        fail(f"{path.name} is unexpectedly large")
    return text


def main() -> None:
    readme = README.read_text(encoding="utf-8")
    lower = readme.lower()
    if "profile-readme:v9" not in readme:
        fail("README version marker is not v9")
    for marker in ("profile-live:start", "profile-live:end", "profile-footer:start", "profile-footer:end"):
        if readme.count(marker) != 1:
            fail(f"expected exactly one {marker}")

    if "mostly building · occasionally overengineering · sometimes both" in readme or "⌁" in readme:
        fail("removed throwaway microcopy reappeared")

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

    local_images = re.findall(r'<img[^>]+src="(\./assets/[^\"]+)"', readme)
    expected_images = [
        "./assets/profile-details.svg",
        "./assets/stats-card.svg",
        "./assets/commit-languages-card.svg",
    ]
    if local_images != expected_images:
        fail("Open source block must use profile-details + activity + commit-language cards")

    profile = check_svg(PROFILE_DETAILS, "700", "200")
    stats = check_svg(STATS_CARD, "470", "190")
    commits = check_svg(COMMIT_LANGS, "340", "200")

    for token in ("Contributions on GitHub", "gpsc-root", "@media (prefers-reduced-motion:reduce)"):
        if token not in profile:
            fail(f"profile details card missing {token}")
    for token in ("Total Commits:", "Total PRs:", "Total PRs Merged:", "Total Contributions:", "MERGED"):
        if token not in stats:
            fail(f"stats card missing {token}")
    if "Contributed to (last year):" in stats or re.search(r'percentile-top-header"[^>]*>\s*Top', stats, flags=re.S):
        fail("stats card regressed to weak/ambiguous metrics")
    if not re.search(r'data-testid="percentile-rank-value"[^>]*>\s*\d+%', stats, flags=re.S):
        fail("stats card merge-rate ring is missing")
    for token in ("@keyframes gpsc-fade", 'class="arc"', "gpsc-item"):
        if token not in commits:
            fail(f"commit-language summary card missing {token}")
    contrast = ["#FFD43B", "#00C2FF", "#A855F7", "#3B82F6", "#FF6B6B"]
    if sum(color in commits for color in contrast) < 5:
        fail("commit-language card lost its high-contrast palette")

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
        "ANIMATION: load",
        'DURATION: "2.4"',
        'UTC_OFFSET: "8"',
        "NAME: Xinchen Lee",
        "assets/profile-details.svg",
        "assets/commit-languages-card.svg",
        'cron: "2,12,22,32,42,52 * * * *"',
    ):
        if token not in refresh:
            fail(f"refresh workflow missing {token}")
    if "card: top-langs" in refresh:
        fail("legacy repository-size language card should stay removed in v9")

    if not POLISHER.is_file():
        fail("card polisher is missing")
    polisher = POLISHER.read_text(encoding="utf-8")
    for token in ("Total Contributions:", "MERGED", "publish_profile_details", "publish_commit_languages", "SUMMARY_THEME"):
        if token not in polisher:
            fail(f"card polisher missing {token}")

    if not SNAKE_WORKFLOW.is_file():
        fail("snake workflow is missing")
    snake_workflow = SNAKE_WORKFLOW.read_text(encoding="utf-8")
    for token in ("Platane/snk@v3", "target_branch: output", "github-snake-dark.svg"):
        if token not in snake_workflow:
            fail(f"snake workflow missing {token}")

    data = json.loads(LIVE.read_text(encoding="utf-8"))
    if len(data.get("selected_external", [])) != 3 or not data.get("updated_at"):
        fail("live.json must retain three selected upstream PRs and updated_at")

    generator = GENERATOR.read_text(encoding="utf-8")
    for token in ("fetch_external", "footer_markdown", "assets/profile-details.svg", "assets/stats-card.svg", "assets/commit-languages-card.svg", "↻ refreshed"):
        if token not in generator:
            fail(f"generator missing {token}")

    print("PASS: v9 profile with animated summary details, activity stats, commit-language card, snake, and hardened refresh")


if __name__ == "__main__":
    main()
