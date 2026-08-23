#!/usr/bin/env python3
"""Refresh truthful public GitHub activity and date-seeded profile microcopy."""
from __future__ import annotations

import datetime as dt
import json
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
LOGIN = os.environ.get("PROFILE_LOGIN", "teddyli18000")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
SGT = dt.timezone(dt.timedelta(hours=8), name="SGT")


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
            proc = subprocess.run(["gh", "api", "graphql", "--input", "-"], input=payload, capture_output=True, check=True)
        else:
            proc = subprocess.run(["gh", "api", path], capture_output=True, check=True)
        return json.loads(proc.stdout)


def fetch_profile() -> dict:
    now = dt.datetime.now(dt.timezone.utc)
    start = dt.datetime(now.year, 1, 1, tzinfo=dt.timezone.utc)
    query = """
    query($login:String!,$from:DateTime!,$to:DateTime!){
      user(login:$login){
        contributionsCollection(from:$from,to:$to){contributionCalendar{totalContributions}}
        repositories(first:100,privacy:PUBLIC,ownerAffiliations:OWNER){nodes{name isFork isArchived}}
      }
    }
    """
    graph = api("", graphql={"query": query, "variables": {"login": LOGIN, "from": start.isoformat().replace("+00:00", "Z"), "to": now.isoformat().replace("+00:00", "Z")}})["data"]["user"]
    query_string = urllib.parse.urlencode({"q": f"author:{LOGIN} type:pr -user:{LOGIN}", "per_page": 30})
    pulls = api(f"search/issues?{query_string}")
    external = []
    for item in pulls["items"]:
        repo = item["repository_url"].split("/repos/", 1)[1]
        number = item["number"]
        detail = api(f"repos/{repo}/pulls/{number}")
        status = "merged" if detail.get("merged") else ("draft" if detail.get("draft") else item["state"])
        external.append({"repo": repo, "number": number, "title": item["title"], "url": item["html_url"], "status": status, "updated_at": item["updated_at"]})
    active_public_repos = sum(1 for repo in graph["repositories"]["nodes"] if not repo["isFork"] and not repo["isArchived"])
    return {"year": now.year, "contributions": graph["contributionsCollection"]["contributionCalendar"]["totalContributions"], "active_public_repos": active_public_repos, "upstream_prs": pulls["total_count"], "external": external}


def choose_external(items: list[dict]) -> list[dict]:
    rank = {"merged": 0, "open": 1, "draft": 2, "closed": 3}
    return sorted(items, key=lambda item: (rank.get(item["status"], 4), -dt.datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00")).timestamp()))[:3]


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
        "active_public_repos": stats["active_public_repos"],
        "upstream_prs": stats["upstream_prs"],
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


def live_markdown(stats: dict, selected: list[dict], updated: dt.datetime) -> str:
    notes = json.loads(DATA.read_text(encoding="utf-8")).get("external_notes", {})
    lines = [
        '<div align="center">',
        f"  <p><strong>{stats['contributions']}</strong> contributions in {stats['year']} &nbsp;·&nbsp; <strong>{stats['active_public_repos']}</strong> active public repos &nbsp;·&nbsp; <strong>{stats['upstream_prs']}</strong> upstream PRs</p>",
        "</div>",
        "",
        "**Outside my repos**",
        "",
    ]
    for item in selected:
        key = f"{item['repo']}#{item['number']}"
        note = notes.get(key, item["title"])
        marker = "✓ merged" if item["status"] == "merged" else f"↗ {item['status']}"
        lines.append(f"- {marker} → [{item['repo']} #{item['number']}]({item['url']}) · {note}")
    stamp = updated.strftime("%d %b · %H:%M SGT").lstrip("0")
    lines.extend(["", f"<sub>↻ refreshed {stamp}</sub>"])
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
    if fresh and changed:
        snapshot = {**stats, "selected_external": selected, "updated_at": updated.isoformat()}
        LIVE.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    state = "Updated" if changed else ("Checked" if fresh else "Retained")
    print(f"{state} {stats['contributions']} contributions, {stats['active_public_repos']} active public repos, {stats['upstream_prs']} upstream PRs at {updated.isoformat()}")


if __name__ == "__main__":
    main()
