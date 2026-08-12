#!/usr/bin/env python3
"""Refresh the small truthful/data-driven portion of the profile README."""

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
            proc = subprocess.run(
                ["gh", "api", "graphql", "--input", "-"],
                input=payload,
                capture_output=True,
                check=True,
            )
        else:
            proc = subprocess.run(
                ["gh", "api", path], capture_output=True, check=True
            )
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

    active_public = sum(
        1
        for repo in graph["repositories"]["nodes"]
        if not repo["isFork"] and not repo["isArchived"]
    )
    return {
        "year": now.year,
        "contributions": graph["contributionsCollection"]["contributionCalendar"][
            "totalContributions"
        ],
        "public_builds": active_public,
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


def replace_block(text: str, name: str, body: str) -> str:
    start = f"<!-- profile-{name}:start -->"
    end = f"<!-- profile-{name}:end -->"
    before, rest = text.split(start, 1)
    _, after = rest.split(end, 1)
    return f"{before}{start}\n{body.rstrip()}\n{end}{after}"


def live_markdown(stats: dict, selected: list[dict], updated: dt.datetime) -> str:
    year = stats["year"]
    alt = (
        f"Live GitHub activity: {stats['contributions']} contributions in {year}, "
        f"{stats['public_builds']} public builds, {stats['upstream_prs']} upstream pull requests. "
        f"Updated automatically."
    )
    lines = [
        '<picture>',
        '  <source media="(prefers-color-scheme: dark)" srcset="./assets/live-dark.svg">',
        f'  <img width="100%" alt="{alt}" src="./assets/live-light.svg">',
        '</picture>',
        '',
        '**Outside my repos**',
        '',
    ]
    content = json.loads(DATA.read_text(encoding="utf-8"))
    notes = content.get("external_notes", {})
    for item in selected:
        key = f"{item['repo']}#{item['number']}"
        note = notes.get(key, item["title"])
        lines.append(
            f"- {item['status']} → [{item['repo']} #{item['number']}]({item['url']}) · {note}"
        )
    stamp = updated.strftime("%d %b · %H:%M SGT").lstrip("0")
    lines.extend(
        ["", f"<sub>generated from public GitHub activity · updated {stamp}</sub>"]
    )
    return "\n".join(lines)


def svg(stats: dict, updated: dt.datetime, dark: bool) -> str:
    bg = "#121418" if dark else "#f7f4ee"
    ink = "#f3f0e9" if dark else "#1d2024"
    muted = "#a7a59f" if dark else "#77736d"
    rule = "#34383e" if dark else "#d8d2c8"
    glass = "#20242a" if dark else "#ffffff"
    glow = "#7dd4cf" if dark else "#dc805f"
    stamp = updated.strftime("%d %b %Y · %H:%M SGT").lstrip("0")
    metrics = [
        (str(stats["contributions"]), f"CONTRIBUTIONS / {stats['year']}"),
        (str(stats["public_builds"]), "PUBLIC BUILDS"),
        (str(stats["upstream_prs"]), "UPSTREAM PRS"),
    ]
    metric_nodes = []
    for index, (value, label) in enumerate(metrics):
        x = 58 + index * 290
        metric_nodes.append(
            f'<text x="{x}" y="121" class="value">{html.escape(value)}</text>'
            f'<text x="{x}" y="150" class="label">{html.escape(label)}</text>'
        )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="220" viewBox="0 0 960 220" role="img" aria-label="Live GitHub signal">
  <defs>
    <linearGradient id="field" x1="0" x2="1">
      <stop offset="0" stop-color="#efb36f" stop-opacity=".64"/>
      <stop offset=".48" stop-color="#ec8b70" stop-opacity=".38"/>
      <stop offset="1" stop-color="#75cbc9" stop-opacity=".50"/>
    </linearGradient>
    <filter id="blur"><feGaussianBlur stdDeviation="18"/></filter>
  </defs>
  <rect width="960" height="220" rx="30" fill="{bg}"/>
  <path d="M16 190 C220 86 436 234 944 36" fill="none" stroke="url(#field)" stroke-width="48" opacity=".20" filter="url(#blur)"/>
  <rect x="22" y="22" width="916" height="176" rx="24" fill="{glass}" fill-opacity=".56" stroke="{rule}"/>
  <path d="M58 67 H902" stroke="{rule}"/>
  <circle cx="58" cy="48" r="5" fill="{glow}"/>
  <text x="74" y="53" class="status">LIVE SIGNAL</text>
  <text x="902" y="53" text-anchor="end" class="stamp">{html.escape(stamp)}</text>
  {''.join(metric_nodes)}
  <path d="M58 176 H902" stroke="{rule}"/>
  <circle cx="512" cy="176" r="5" fill="{glow}"/>
  <circle cx="512" cy="176" r="10" fill="none" stroke="{glow}" stroke-opacity=".30"/>
  <style>
    text{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;fill:{ink}}}
    .status,.label,.stamp{{font-size:12px;letter-spacing:1.8px}}
    .stamp,.label{{fill:{muted}}}
    .value{{font-size:38px;font-weight:580;letter-spacing:-1px}}
  </style>
</svg>'''


def main() -> None:
    stats = fetch_profile()
    selected = choose_external(stats["external"])
    now = dt.datetime.now(SGT)
    current = README.read_text(encoding="utf-8")
    current = replace_block(current, "live", live_markdown(stats, selected, now))
    content = json.loads(DATA.read_text(encoding="utf-8"))
    footer_pool = content["footer_lines"]
    footer = footer_pool[int(now.strftime("%Y%j")) % len(footer_pool)]
    current = replace_block(current, "footer", f"<sub>{footer}</sub>")
    README.write_text(current, encoding="utf-8", newline="\n")
    (ROOT / "assets").mkdir(exist_ok=True)
    (ROOT / "assets" / "live-light.svg").write_text(svg(stats, now, False), encoding="utf-8")
    (ROOT / "assets" / "live-dark.svg").write_text(svg(stats, now, True), encoding="utf-8")
    snapshot = {**stats, "selected_external": selected, "updated_at": now.isoformat()}
    LIVE.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Updated {stats['contributions']} contributions, {stats['public_builds']} builds, "
        f"{stats['upstream_prs']} upstream PRs at {now.isoformat()}"
    )


if __name__ == "__main__":
    main()
