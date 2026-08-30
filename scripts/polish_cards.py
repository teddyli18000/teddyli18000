#!/usr/bin/env python3
"""Polish mature generated cards without reimplementing their data logic.

Data/layout come from github-readme-stats and github-profile-summary-cards.
This script only:
- swaps the weak `Contributed to (last year)` row for full-history contributions
  reported by github-profile-summary-cards;
- repurposes github-readme-stats' existing rank ring as a truthful PR merge-rate
  ring using the card's own PR / merged-PR values;
- remaps top-language colors to a higher-contrast palette while preserving all
  language names and percentages.
"""
from __future__ import annotations

import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATS = ROOT / "assets" / "stats-card.svg"
LANGS = ROOT / "assets" / "languages-card.svg"
SUMMARY_ROOT = ROOT / "profile-summary-card-output"

PALETTE = [
    "#FFD43B",  # yellow
    "#00C2FF",  # cyan
    "#A855F7",  # violet
    "#3B82F6",  # blue
    "#FF6B6B",  # coral
    "#F43F8C",  # magenta
    "#F97316",  # orange
    "#22C55E",  # green
]


def find_total_contributions() -> str:
    candidates = list(SUMMARY_ROOT.glob("**/0-profile-details.svg"))
    if not candidates:
        raise SystemExit("profile-summary-cards did not generate 0-profile-details.svg")
    text = candidates[0].read_text(encoding="utf-8")
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


def polish_stats(total_contributions: str) -> None:
    text = STATS.read_text(encoding="utf-8")
    commits = metric_number(text, "commits")
    prs = metric_number(text, "prs")
    merged = metric_number(text, "prs_merged")
    merge_rate = merged / prs if prs else 0.0
    merge_percent = round(merge_rate * 100)

    text = text.replace("Contributed to (last year):", "Total Contributions:")
    text = re.sub(
        r'(<text[^>]*data-testid="contribs"[^>]*>\s*)[^<]+(</text>)',
        rf"\g<1>{total_contributions}\g<2>",
        text,
        count=1,
        flags=re.S,
    )

    desc = (
        f"Total Commits: {commits}, Total PRs: {prs}, Total PRs Merged: {merged}, "
        f"Total Contributions: {total_contributions}, PR merge rate: {merge_percent}%"
    )
    text = re.sub(r"<title id=\"titleId\">.*?</title>",
                  f'<title id="titleId">GitHub activity, PR merge rate: {merge_percent}%</title>',
                  text, count=1, flags=re.S)
    text = re.sub(r"<desc id=\"descId\">.*?</desc>",
                  f'<desc id="descId">{desc}</desc>',
                  text, count=1, flags=re.S)

    text = re.sub(
        r'(data-testid="percentile-top-header"[^>]*>\s*)[^<]+(</text>)',
        r"\g<1>MERGED\g<2>", text, count=1, flags=re.S,
    )
    text = re.sub(
        r'(data-testid="percentile-rank-value"[^>]*>\s*)[^<]+(</text>)',
        rf"\g<1>{merge_percent}%\g<2>", text, count=1, flags=re.S,
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


def polish_languages() -> None:
    text = LANGS.read_text(encoding="utf-8")
    colors: list[str] = []
    for color in re.findall(
        r'data-testid="lang-progress".*?fill="(#[0-9A-Fa-f]{6})"',
        text,
        flags=re.S,
    ):
        if color not in colors:
            colors.append(color)
    if len(colors) < 6:
        raise SystemExit(f"expected at least six language colors, found {len(colors)}")
    for old, new in zip(colors[: len(PALETTE)], PALETTE):
        text = text.replace(old, new)
    LANGS.write_text(text, encoding="utf-8", newline="\n")


def main() -> None:
    total = find_total_contributions()
    polish_stats(total)
    polish_languages()
    print(f"Polished cards with {total} full-history contributions and {len(PALETTE)} contrast colors")


if __name__ == "__main__":
    main()
