#!/usr/bin/env python3
"""Refresh truthful public activity, one custom data card, and rotating microcopy.

Generic language statistics are deliberately delegated to github-readme-stats.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import shutil
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
DATA = ROOT / "data" / "content.json"
LIVE = ROOT / "data" / "live.json"
ASSETS = ROOT / "assets"
ACTIVITY_CARD = ASSETS / "activity-card.svg"
LOGIN = os.environ.get("PROFILE_LOGIN", "teddyli18000")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
SGT = dt.timezone(dt.timedelta(hours=8), name="SGT")
LANGUAGES_CARD_HTML = (
    "https://github-readme-stats.vercel.app/api/top-langs/?username=teddyli18000"
    "&amp;layout=compact&amp;langs_count=8&amp;card_width=470"
    "&amp;bg_color=0D1117&amp;title_color=00D8D6&amp;text_color=C9D1D9"
    "&amp;border_color=30363D&amp;border_radius=14"
)


def api(path: str, *, graphql: dict[str, object] | None = None) -> dict:
    payload = json.dumps(graphql).encode() if graphql is not None else None
    request = (
        urllib.request.Request("https://api.github.com/graphql", data=payload, method="POST")
        if graphql is not None
        else urllib.request.Request(f"https://api.github.com/{path}")
    )
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("User-Agent", f"{LOGIN}-profile-readme")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    if TOKEN:
        request.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except Exception:
        if not shutil.which("gh"):
            raise
        if graphql is not None:
            proc = subprocess.run(
                ["gh", "api", "graphql", "--input", "-"],
                input=payload,
                capture_output=True,
                check=True,
            )
        else:
            proc = subprocess.run(["gh", "api", path], capture_output=True, check=True)
        return json.loads(proc.stdout)


def fetch_profile() -> dict:
    now = dt.datetime.now(dt.timezone.utc)
    start = dt.datetime(now.year, 1, 1, tzinfo=dt.timezone.utc)
    query = """
    query($login:String!,$from:DateTime!,$to:DateTime!){
      user(login:$login){
        contributionsCollection(from:$from,to:$to){
          totalCommitContributions
          contributionCalendar{totalContributions}
        }
        repositories(first:100,privacy:PUBLIC,ownerAffiliations:OWNER){
          nodes{name isFork isArchived}
        }
      }
    }
    """
    graph = api(
        "",
        graphql={
            "query": query,
            "variables": {
                "login": LOGIN,
                "from": start.isoformat().replace("+00:00", "Z"),
                "to": now.isoformat().replace("+00:00", "Z"),
            },
        },
    )["data"]["user"]
    contributions = graph["contributionsCollection"]
    repos = graph["repositories"]["nodes"]

    query_string = urllib.parse.urlencode({"q": f"author:{LOGIN} type:pr -user:{LOGIN}", "per_page": 100})
    pulls = api(f"search/issues?{query_string}")
    external = []
    for item in pulls["items"]:
        repo = item["repository_url"].split("/repos/", 1)[1]
        number = item["number"]
        detail = api(f"repos/{repo}/pulls/{number}")
        status = "merged" if detail.get("merged") else ("draft" if detail.get("draft") else item["state"])
        external.append({
            "repo": repo,
            "number": number,
            "title": item["title"],
            "url": item["html_url"],
            "status": status,
            "updated_at": item["updated_at"],
        })

    return {
        "year": now.year,
        "contributions": contributions["contributionCalendar"]["totalContributions"],
        "total_commits": contributions["totalCommitContributions"],
        "active_public_repos": sum(1 for repo in repos if not repo["isFork"] and not repo["isArchived"]),
        "upstream_prs": pulls["total_count"],
        "external": external,
    }


def choose_external(items: list[dict]) -> list[dict]:
    rank = {"merged": 0, "open": 1, "draft": 2, "closed": 3}
    return sorted(
        items,
        key=lambda item: (
            rank.get(item["status"], 4),
            -dt.datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00")).timestamp(),
        ),
    )[:3]


def merged_upstream(stats: dict) -> int:
    return sum(1 for item in stats.get("external", []) if item.get("status") == "merged")


def last_good() -> tuple[dict, list[dict], dt.datetime]:
    snapshot = json.loads(LIVE.read_text(encoding="utf-8"))
    required = ("year", "contributions", "active_public_repos", "upstream_prs", "updated_at")
    if any(key not in snapshot for key in required):
        raise ValueError("live.json is missing required last-good fields")
    selected = snapshot.get("selected_external") or choose_external(snapshot.get("external", []))
    if len(selected) != 3:
        raise ValueError("live.json does not contain three upstream pull requests")
    stamp = dt.datetime.fromisoformat(snapshot["updated_at"].replace("Z", "+00:00")).astimezone(SGT)
    return snapshot, selected, stamp


def visible_signature(stats: dict, selected: list[dict]) -> dict:
    return {
        "year": stats["year"],
        "contributions": stats["contributions"],
        "total_commits": stats.get("total_commits"),
        "active_public_repos": stats["active_public_repos"],
        "upstream_prs": stats["upstream_prs"],
        "upstream_merged": merged_upstream(stats),
        "selected_external": [
            {key: item[key] for key in ("repo", "number", "title", "url", "status")}
            for item in selected
        ],
    }


def collect() -> tuple[dict, list[dict], dt.datetime, bool, bool]:
    try:
        stats = fetch_profile()
        selected = choose_external(stats["external"])
        if len(selected) != 3:
            raise ValueError(f"expected three upstream pull requests, got {len(selected)}")
        now = dt.datetime.now(SGT)
        try:
            previous, previous_selected, previous_stamp = last_good()
            changed = visible_signature(stats, selected) != visible_signature(previous, previous_selected)
            updated = now if changed else previous_stamp
        except Exception:
            changed = True
            updated = now
        return stats, selected, updated, True, changed
    except Exception as error:
        stats, selected, stamp = last_good()
        print(f"GitHub refresh failed ({error}); retaining last-good data from {stamp.isoformat()}")
        return stats, selected, stamp, False, False


def replace_block(text: str, name: str, body: str) -> str:
    start = f"<!-- profile-{name}:start -->"
    end = f"<!-- profile-{name}:end -->"
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError(f"expected exactly one {start} and {end}")
    before, rest = text.split(start, 1)
    _, after = rest.split(end, 1)
    return f"{before}{start}\n{body.rstrip()}\n{end}{after}"


def activity_card_svg(stats: dict, updated: dt.datetime) -> str:
    merged = merged_upstream(stats)
    total = max(0, int(stats["upstream_prs"]))
    ratio = merged / total if total else 0.0
    circumference = 2 * math.pi * 42
    active = circumference * ratio
    inactive = circumference - active
    stamp = updated.strftime("%d %b · %H:%M SGT").lstrip("0")
    commits = stats.get("total_commits")
    commit_text = str(commits) if commits is not None else "—"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="470" height="200" viewBox="0 0 470 200" role="img" aria-label="Public GitHub activity">
  <defs>
    <linearGradient id="ring" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#62d0a2"/>
      <stop offset="1" stop-color="#87dfbd"/>
    </linearGradient>
  </defs>
  <rect x="1" y="1" width="468" height="198" rx="14" fill="#263746" stroke="#435666"/>
  <text x="26" y="34" class="title">Public activity</text>
  <text x="27" y="51" class="meta">AUTO-REFRESHED · PUBLIC GITHUB</text>

  <g stroke="#69d2a5" fill="none" stroke-width="1.7">
    <path d="M29 69v9M24.5 73.5h9"/>
    <path d="M25 100h9M29.5 95.5v9" transform="rotate(45 29.5 100)"/>
    <rect x="24.5" y="122" width="9" height="9" rx="1.8"/>
    <path d="M24.5 158l9-9M27 149h6.5v6.5"/>
  </g>

  <text x="45" y="78" class="label">Contributions</text><text x="282" y="78" text-anchor="end" class="value">{stats['contributions']}</text>
  <text x="45" y="105" class="label">Commits / {stats['year']}</text><text x="282" y="105" text-anchor="end" class="value">{commit_text}</text>
  <text x="45" y="132" class="label">Public repos</text><text x="282" y="132" text-anchor="end" class="value">{stats['active_public_repos']}</text>
  <text x="45" y="159" class="label">Upstream PRs</text><text x="282" y="159" text-anchor="end" class="value">{stats['upstream_prs']}</text>

  <g transform="translate(382 113)">
    <circle r="42" fill="none" stroke="#3d5666" stroke-width="8"/>
    <circle r="42" fill="none" stroke="url(#ring)" stroke-width="8" stroke-linecap="round"
            stroke-dasharray="{active:.1f} {inactive:.1f}" transform="rotate(-90)"/>
    <text x="0" y="2" text-anchor="middle" class="ringValue">{merged}</text>
    <text x="0" y="20" text-anchor="middle" class="ringLabel">MERGED</text>
  </g>

  <text x="26" y="184" class="refresh">updated {stamp}</text>
  <style>
    .title{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;font-size:21px;font-weight:650;fill:#69d2a5}}
    .meta{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;font-size:8.5px;font-weight:600;letter-spacing:1.4px;fill:#91a5b4}}
    .label{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;font-size:13.5px;font-weight:600;fill:#f3f6f8}}
    .value{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;font-size:15px;font-weight:700;fill:#ffffff}}
    .ringValue{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;font-size:31px;font-weight:700;fill:#ffffff}}
    .ringLabel{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;font-size:8.5px;font-weight:700;letter-spacing:1.3px;fill:#8ea3b2}}
    .refresh{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;font-size:9.5px;fill:#91a5b4}}
  </style>
</svg>'''


def live_markdown(stats: dict, selected: list[dict], updated: dt.datetime) -> str:
    notes = json.loads(DATA.read_text(encoding="utf-8")).get("external_notes", {})
    merged = merged_upstream(stats)
    lines = [
        '<p align="center">',
        f'  <img width="49%" src="./assets/activity-card.svg" alt="Public GitHub activity: {stats["contributions"]} contributions in {stats["year"]}, {stats.get("total_commits", "unknown")} commits, {stats["active_public_repos"]} active public repositories, {stats["upstream_prs"]} upstream pull requests, {merged} merged upstream pull requests.">',
        f'  <img width="49%" src="{LANGUAGES_CARD_HTML}" alt="Most used languages across public GitHub repositories.">',
        '</p>',
        '',
        '**Outside my repos**',
        '',
    ]
    for item in selected:
        key = f"{item['repo']}#{item['number']}"
        note = notes.get(key, item["title"])
        marker = "✓ merged" if item["status"] == "merged" else f"↗ {item['status']}"
        lines.append(f"- {marker} → [{item['repo']} #{item['number']}]({item['url']}) · {note}")
    return "\n".join(lines)


def main() -> None:
    stats, selected, updated, fresh, changed = collect()
    text = README.read_text(encoding="utf-8")
    text = replace_block(text, "live", live_markdown(stats, selected, updated))
    content = json.loads(DATA.read_text(encoding="utf-8"))
    footer_pool = content["footer_lines"]
    index = int(dt.datetime.now(SGT).strftime("%Y%j")) % len(footer_pool)
    text = replace_block(text, "footer", f"<sub>⌁ {footer_pool[index]} ⌁</sub>")
    README.write_text(text, encoding="utf-8", newline="\n")

    ASSETS.mkdir(parents=True, exist_ok=True)
    ACTIVITY_CARD.write_text(activity_card_svg(stats, updated), encoding="utf-8", newline="\n")

    if fresh and changed:
        snapshot = {**stats, "selected_external": selected, "updated_at": updated.isoformat()}
        LIVE.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    state = "Updated" if changed else ("Checked" if fresh else "Retained")
    print(
        f"{state} {stats['contributions']} contributions, {stats.get('total_commits', 'n/a')} commits, "
        f"{stats['active_public_repos']} public repos, {stats['upstream_prs']} upstream PRs, "
        f"{merged_upstream(stats)} merged at {updated.isoformat()}"
    )


if __name__ == "__main__":
    main()
