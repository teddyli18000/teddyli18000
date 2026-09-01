#!/usr/bin/env python3
"""Polish mature generated cards without reimplementing their data logic.

Data/layout come from github-readme-stats and github-profile-summary-cards.
This script only:
- swaps the weak `Contributed to (last year)` row for full-history contributions;
- repurposes github-readme-stats' existing rank ring as a truthful PR merge-rate ring;
- preserves the last-good nonzero commit count if the upstream stats action transiently returns zero;
- publishes the mature summary-cards profile-details and most-commit-language SVGs;
- maps generated cards onto the profile's shared visual palette.
"""
from __future__ import annotations

import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
STATS = ASSETS / "stats-card.svg"
PREVIOUS_STATS = Path("/tmp/profile-previous-stats-card.svg")
PROFILE_DETAILS = ASSETS / "profile-details.svg"
COMMIT_LANGS = ASSETS / "commit-languages-card.svg"
SUMMARY_ROOT = ROOT / "profile-summary-card-output"

PALETTE = [
    "#FFD43B",
    "#00C2FF",
    "#A855F7",
    "#3B82F6",
    "#FF6B6B",
    "#F43F8C",
    "#F97316",
    "#22C55E",
]

SUMMARY_THEME = {
    "#0366d6": "#69D2A5",
    "#77909c": "#F3F6F8",
    "#0d1117": "#263746",
    "#2e343b": "#435666",
    "#8b949e": "#69D2A5",
    "#40c463": "#69D2A5",
}


def summary_source(filename: str) -> Path:
    candidates = list(SUMMARY_ROOT.glob(f"**/{filename}"))
    if not candidates:
        raise SystemExit(f"profile-summary-cards did not generate {filename}")
    return candidates[0]


def find_total_contributions() -> str:
    text = summary_source("0-profile-details.svg").read_text(encoding="utf-8")
    match = re.search(r"([0-9][0-9.,]*[kKmM]?)\s+Contributions on GitHub", text)
    if not match:
        raise SystemExit("could not extract full-history contributions from profile-details card")
    return match.group(1)


def metric_number(text: str, testid: str) -> int:
    match = re.search(
        rf'data-testid="{re.escape(testid)}"[^>]*>\s*([0-9][0-9,]*)',
        text,
        flags=re.S,
    )
    if not match:
        raise SystemExit(f"could not read {testid} from stats card")
    return int(match.group(1).replace(",", ""))


def replace_metric(text: str, testid: str, value: int | str) -> str:
    updated, count = re.subn(
        rf'(<text[^>]*data-testid="{re.escape(testid)}"[^>]*>\s*)[^<]+(</text>)',
        rf"\g<1>{value}\g<2>",
        text,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise SystemExit(f"could not replace {testid} in stats card")
    return updated


def last_good_commits() -> int:
    if not PREVIOUS_STATS.is_file():
        raise SystemExit("generated stats returned zero commits and no last-good stats card is available")
    previous = PREVIOUS_STATS.read_text(encoding="utf-8")
    commits = metric_number(previous, "commits")
    if commits <= 0:
        raise SystemExit("generated stats returned zero commits and the last-good card is also zero")
    return commits


def polish_stats(total_contributions: str) -> None:
    text = STATS.read_text(encoding="utf-8")
    commits = metric_number(text, "commits")
    if commits <= 0:
        commits = last_good_commits()
        text = replace_metric(text, "commits", commits)
        print(f"Upstream stats returned zero commits; retained last-good value {commits}")

    prs = metric_number(text, "prs")
    merged = metric_number(text, "prs_merged")
    merge_rate = merged / prs if prs else 0.0
    merge_percent = round(merge_rate * 100)

    text = text.replace("Contributed to (last year):", "Total Contributions:")
    text = replace_metric(text, "contribs", total_contributions)

    desc = (
        f"Total Commits: {commits}, Total PRs: {prs}, Total PRs Merged: {merged}, "
        f"Total Contributions: {total_contributions}, PR merge rate: {merge_percent}%"
    )
    text = re.sub(
        r'<title id="titleId">.*?</title>',
        f'<title id="titleId">GitHub activity, PR merge rate: {merge_percent}%</title>',
        text,
        count=1,
        flags=re.S,
    )
    text = re.sub(
        r'<desc id="descId">.*?</desc>',
        f'<desc id="descId">{desc}</desc>',
        text,
        count=1,
        flags=re.S,
    )
    text = re.sub(
        r'(data-testid="percentile-top-header"[^>]*>\s*)[^<]+(</text>)',
        r"\g<1>MERGED\g<2>",
        text,
        count=1,
        flags=re.S,
    )
    text = re.sub(
        r'(data-testid="percentile-rank-value"[^>]*>\s*)[^<]+(</text>)',
        rf"\g<1>{merge_percent}%\g<2>",
        text,
        count=1,
        flags=re.S,
    )

    circumference = 2 * math.pi * 40
    target_offset = circumference * (1.0 - merge_rate)
    text = re.sub(
        r'(to\s*\{\s*stroke-dashoffset:\s*)[0-9.]+;',
        rf"\g<1>{target_offset:.4f};",
        text,
        count=1,
        flags=re.S,
    )
    STATS.write_text(text, encoding="utf-8", newline="\n")


def restyle_summary(text: str) -> str:
    for old, new in SUMMARY_THEME.items():
        text = text.replace(old, new).replace(old.upper(), new)
    text = text.replace('rx="5" ry="5"', 'rx="14" ry="14"')
    return text


def publish_profile_details() -> None:
    text = restyle_summary(summary_source("0-profile-details.svg").read_text(encoding="utf-8"))
    PROFILE_DETAILS.write_text(text, encoding="utf-8", newline="\n")


def publish_commit_languages() -> None:
    text = restyle_summary(summary_source("2-most-commit-language.svg").read_text(encoding="utf-8"))
    colors: list[str] = []
    for color in re.findall(r'<rect[^>]+fill="(#[0-9A-Fa-f]{6})"[^>]+stroke=', text):
        if color not in colors and color not in SUMMARY_THEME.values():
            colors.append(color)
    if len(colors) < 5:
        raise SystemExit(f"expected at least five commit-language colors, found {len(colors)}")
    for old, new in zip(colors[: len(PALETTE)], PALETTE):
        text = text.replace(old, new)
    COMMIT_LANGS.write_text(text, encoding="utf-8", newline="\n")


def main() -> None:
    total = find_total_contributions()
    polish_stats(total)
    publish_profile_details()
    publish_commit_languages()
    print(f"Published summary cards with {total} full-history contributions")


if __name__ == "__main__":
    main()
