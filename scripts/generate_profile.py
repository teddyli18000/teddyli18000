#!/usr/bin/env python3
"""Refresh the data-driven live block, SVG instrument, and rotating footer."""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
DATA = ROOT / "data" / "content.json"
LIVE = ROOT / "data" / "live.json"
LOGIN = os.environ.get("PROFILE_LOGIN", "teddyli18000")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
SGT = dt.timezone(dt.timedelta(hours=8), name="SGT")


def api(path: str, *, graphql: dict[str, object] | None = None) -> dict:
    """Read one GitHub API response, falling back to an authenticated gh CLI."""

    payload: bytes | None = None
    if graphql is not None:
        payload = json.dumps(graphql).encode()
        request = urllib.request.Request(
            "https://api.github.com/graphql", data=payload, method="POST"
        )
    else:
        request = urllib.request.Request(f"https://api.github.com/{path}")
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("User-Agent", f"{LOGIN}-profile-readme")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    if TOKEN:
        request.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except Exception:
        if not shutil_which("gh"):
            raise
        if graphql is not None:
            assert payload is not None
            proc = subprocess.run(
                ["gh", "api", "graphql", "--input", "-"],
                input=payload,
                capture_output=True,
                check=True,
            )
        else:
            proc = subprocess.run(["gh", "api", path], capture_output=True, check=True)
        return json.loads(proc.stdout)


def shutil_which(name: str) -> str | None:
    from shutil import which

    return which(name)


def fetch_profile() -> dict:
    now = dt.datetime.now(dt.timezone.utc)
    year_start = dt.datetime(now.year, 1, 1, tzinfo=dt.timezone.utc)
    query = """
    query($login:String!,$from:DateTime!,$to:DateTime!){
      user(login:$login){
        contributionsCollection(from:$from,to:$to){
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
                "from": year_start.isoformat().replace("+00:00", "Z"),
                "to": now.isoformat().replace("+00:00", "Z"),
            },
        },
    )["data"]["user"]

    query_string = urllib.parse.urlencode(
        {"q": f"author:{LOGIN} type:pr -user:{LOGIN}", "per_page": 30}
    )
    pulls = api(f"search/issues?{query_string}")
    external = []
    for item in pulls["items"]:
        repo = item["repository_url"].split("/repos/", 1)[1]
        number = item["number"]
        detail = api(f"repos/{repo}/pulls/{number}")
        status = "merged" if detail.get("merged") else (
            "draft" if detail.get("draft") else item["state"]
        )
        external.append(
            {
                "repo": repo,
                "number": number,
                "title": item["title"],
                "url": item["html_url"],
                "status": status,
                "updated_at": item["updated_at"],
            }
        )

    active_public_repos = sum(
        1
        for repo in graph["repositories"]["nodes"]
        if not repo["isFork"] and not repo["isArchived"]
    )
    return {
        "year": now.year,
        "contributions": graph["contributionsCollection"]["contributionCalendar"][
            "totalContributions"
        ],
        "active_public_repos": active_public_repos,
        "upstream_prs": pulls["total_count"],
        "external": external,
    }


def choose_external(items: list[dict]) -> list[dict]:
    rank = {"merged": 0, "open": 1, "draft": 2, "closed": 3}
    return sorted(
        items,
        key=lambda item: (
            rank.get(item["status"], 4),
            -dt.datetime.fromisoformat(
                item["updated_at"].replace("Z", "+00:00")
            ).timestamp(),
        ),
    )[:3]


def parse_stamp(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.astimezone(SGT)


def last_good_profile() -> tuple[dict, list[dict], dt.datetime]:
    """Load the previous authenticated snapshot without inventing new values."""

    snapshot = json.loads(LIVE.read_text(encoding="utf-8"))
    required = ("year", "contributions", "active_public_repos", "upstream_prs", "updated_at")
    if any(key not in snapshot for key in required):
        raise ValueError("live.json is missing required last-good fields")
    selected = snapshot.get("selected_external") or choose_external(snapshot.get("external", []))
    if len(selected) != 3:
        raise ValueError("live.json does not contain three last-good upstream PRs")
    return snapshot, selected, parse_stamp(snapshot["updated_at"])


def collect_profile() -> tuple[dict, list[dict], dt.datetime, bool]:
    try:
        stats = fetch_profile()
        selected = choose_external(stats["external"])
        if len(selected) != 3:
            raise ValueError(f"expected three upstream pull requests, got {len(selected)}")
        return stats, selected, dt.datetime.now(SGT), True
    except Exception as error:
        stats, selected, stamp = last_good_profile()
        print(f"GitHub refresh failed ({error}); retaining last-good data from {stamp.isoformat()}")
        return stats, selected, stamp, False


def replace_block(text: str, name: str, body: str) -> str:
    start = f"<!-- profile-{name}:start -->"
    end = f"<!-- profile-{name}:end -->"
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError(f"expected one {start} and one {end} marker")
    before, rest = text.split(start, 1)
    _, after = rest.split(end, 1)
    return f"{before}{start}\n{body.rstrip()}\n{end}{after}"


def live_markdown(stats: dict, selected: list[dict], updated: dt.datetime) -> str:
    content = json.loads(DATA.read_text(encoding="utf-8"))
    notes = content.get("external_notes", {})
    lines = [
        '<picture>',
        '  <source media="(prefers-color-scheme: dark)" srcset="./assets/live-dark.svg">',
        '  <img width="100%" alt="Public GitHub activity with contributions, active public repositories, and upstream pull requests." src="./assets/live-light.svg">',
        '</picture>',
        '',
        '**Outside my repos**',
        '',
    ]
    for item in selected:
        key = f"{item['repo']}#{item['number']}"
        note = notes.get(key, item["title"])
        lines.append(
            f"- {item['status']} → [{item['repo']} #{item['number']}]({item['url']}) · {note}"
        )
    stamp = updated.strftime("%d %b · %H:%M SGT").lstrip("0")
    lines.extend(["", f"<sub>generated from public GitHub activity · updated {stamp}</sub>"])
    return "\n".join(lines)


def svg(stats: dict, updated: dt.datetime, dark: bool) -> str:
    """Render a quiet editorial instrument with three truthful metrics."""

    bg = "#121418" if dark else "#f7f4ee"
    ink = "#f3f0e9" if dark else "#1d2024"
    muted = "#a7a59f" if dark else "#77736d"
    rule = "#34383e" if dark else "#d8d2c8"
    panel = "#20242a" if dark else "#ffffff"
    accent = "#7dd4cf" if dark else "#dc805f"
    stamp = updated.strftime("%d %b %Y · %H:%M SGT").lstrip("0")
    metrics = [
        (str(stats["contributions"]), f"CONTRIBUTIONS / {stats['year']}"),
        (str(stats["active_public_repos"]), "ACTIVE PUBLIC REPOS"),
        (str(stats["upstream_prs"]), "UPSTREAM PRS"),
    ]
    metric_nodes = []
    for index, (value, label) in enumerate(metrics):
        x = 58 + index * 290
        metric_nodes.append(
            f'<text x="{x}" y="125" class="value">{html.escape(value)}</text>'
            f'<text x="{x}" y="153" class="label">{html.escape(label)}</text>'
        )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="220" viewBox="0 0 960 220" role="img" aria-label="Public GitHub activity">
  <defs>
    <linearGradient id="field" x1="0" x2="1">
      <stop offset="0" stop-color="#efb36f" stop-opacity=".64"/>
      <stop offset=".48" stop-color="#ec8b70" stop-opacity=".38"/>
      <stop offset="1" stop-color="#75cbc9" stop-opacity=".50"/>
    </linearGradient>
    <filter id="soften"><feGaussianBlur stdDeviation="18"/></filter>
  </defs>
  <rect width="960" height="220" fill="{bg}"/>
  <path d="M16 190 C220 86 436 234 944 36" fill="none" stroke="url(#field)" stroke-width="48" opacity=".20" filter="url(#soften)"/>
  <rect x="30" y="28" width="900" height="164" rx="10" fill="{panel}" fill-opacity=".38" stroke="{rule}" stroke-opacity=".48"/>
  <text x="902" y="53" text-anchor="end" class="stamp">{html.escape(stamp)}</text>
  {''.join(metric_nodes)}
  <path d="M58 178 H902" stroke="{rule}" stroke-opacity=".55"/>
  <circle cx="512" cy="178" r="5" fill="{accent}"/>
  <circle cx="512" cy="178" r="10" fill="none" stroke="{accent}" stroke-opacity=".30"/>
  <style>
    text{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;fill:{ink}}}
    .label,.stamp{{font-size:12px;letter-spacing:1.8px}}
    .stamp,.label{{fill:{muted}}}
    .value{{font-size:38px;font-weight:580;letter-spacing:-1px}}
  </style>
</svg>'''


def main() -> None:
    stats, selected, updated, fresh = collect_profile()
    current = README.read_text(encoding="utf-8")
    current = replace_block(current, "live", live_markdown(stats, selected, updated))
    content = json.loads(DATA.read_text(encoding="utf-8"))
    footer_pool = content["footer_lines"]
    # Footer rotation follows the refresh date even when the live block falls
    # back to an older last-good snapshot.
    footer = footer_pool[int(dt.datetime.now(SGT).strftime("%Y%j")) % len(footer_pool)]
    current = replace_block(current, "footer", f"<sub>{footer}</sub>")
    README.write_text(current, encoding="utf-8", newline="\n")
    if fresh:
        (ROOT / "assets" / "live-light.svg").write_text(svg(stats, updated, False), encoding="utf-8")
        (ROOT / "assets" / "live-dark.svg").write_text(svg(stats, updated, True), encoding="utf-8")
        snapshot = {**stats, "selected_external": selected, "updated_at": updated.isoformat()}
        LIVE.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"{'Updated' if fresh else 'Retained'} {stats['contributions']} contributions, "
        f"{stats['active_public_repos']} active public repos, {stats['upstream_prs']} upstream PRs "
        f"at {updated.isoformat()}"
    )


if __name__ == "__main__":
    main()
