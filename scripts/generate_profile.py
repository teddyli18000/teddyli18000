#!/usr/bin/env python3
"""Refresh the profile's upstream activity list, refresh stamp, and footer.

Generic GitHub statistics come from mature profile-card actions. This script owns
the profile-specific upstream PR list (every merged PR authored outside the owner's
repos), visible refresh timestamp, and footer rotation.
"""
from __future__ import annotations

import datetime as dt
import html
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
PAGE_SIZE = 100
MAX_PAGES = 10  # GitHub search caps at 1000 results; ten full pages reach it


def api(path: str) -> dict:
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
        if not shutil.which("gh"):
            raise
        proc = subprocess.run(["gh", "api", path], capture_output=True, check=True)
        return json.loads(proc.stdout)


def pull_status(repo: str, item: dict) -> str:
    """Resolve merged/open/draft/closed for one search hit.

    Only merged PRs are published, so a transient detail failure must never demote
    a merged PR: `pull_request.merged_at` from the search hit is authoritative on
    its own. The per-PR detail only refines an open PR into a draft.
    """
    detail: dict | None = None
    try:
        detail = api(f"repos/{repo}/pulls/{item['number']}")
    except Exception as error:
        print(f"pull detail unavailable for {repo}#{item['number']} ({error}); using search metadata")

    if (item.get("pull_request") or {}).get("merged_at") or (detail and detail.get("merged")):
        return "merged"
    if item["state"] == "open" and detail and detail.get("draft"):
        return "draft"
    return item["state"]


def fetch_external() -> list[dict]:
    """Every PR the owner authored outside their own repos, across all search pages."""
    query_string = urllib.parse.urlencode(
        {"q": f"author:{LOGIN} type:pr -user:{LOGIN}", "per_page": PAGE_SIZE}
    )
    hits: list[dict] = []
    for page in range(1, MAX_PAGES + 1):
        batch = api(f"search/issues?{query_string}&page={page}").get("items") or []
        hits.extend(batch)
        if len(batch) < PAGE_SIZE:
            break

    external: list[dict] = []
    for item in hits:
        repo = item["repository_url"].split("/repos/", 1)[1]
        external.append(
            {
                "repo": repo,
                "number": item["number"],
                "title": item["title"],
                "url": item["html_url"],
                "status": pull_status(repo, item),
                "updated_at": item["updated_at"],
            }
        )
    return external


def published_external(items: list[dict]) -> list[dict]:
    """The merged PRs only, newest activity first; the profile shows shipped work.

    `repo`/`number` break ties so the order is total: two PRs can share an
    `updated_at`, and an order that depended on the API's result ordering would
    make `signature()` see phantom changes and commit a new stamp every run.
    """
    return sorted(
        (item for item in items if item["status"] == "merged"),
        key=lambda item: (
            -dt.datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00")).timestamp(),
            item["repo"],
            item["number"],
        ),
    )


def signature(items: list[dict]) -> list[dict]:
    return [
        {key: item[key] for key in ("repo", "number", "title", "url", "status")}
        for item in items
    ]


def hour_bucket(value: dt.datetime) -> tuple[int, int, int, int]:
    local = value.astimezone(SGT)
    return local.year, local.month, local.day, local.hour


def last_good() -> tuple[list[dict], list[dict], dt.datetime]:
    snapshot = json.loads(LIVE.read_text(encoding="utf-8"))
    external = snapshot.get("external") or []
    selected = snapshot.get("selected_external") or published_external(external)
    if not selected:
        raise ValueError("live.json does not contain a last-good merged upstream PR list")
    stamp_raw = snapshot.get("updated_at")
    if not stamp_raw:
        raise ValueError("live.json is missing updated_at")
    stamp = dt.datetime.fromisoformat(stamp_raw.replace("Z", "+00:00")).astimezone(SGT)
    return external, selected, stamp


def collect() -> tuple[list[dict], list[dict], dt.datetime, bool, bool]:
    try:
        external = fetch_external()
        selected = published_external(external)
        if not selected:
            raise ValueError("no merged upstream pull requests found")
        now = dt.datetime.now(SGT)
        try:
            _, previous_selected, previous_stamp = last_good()
            content_changed = signature(selected) != signature(previous_selected)
            refresh_due = hour_bucket(now) != hour_bucket(previous_stamp)
            changed = content_changed or refresh_due
            updated = now if changed else previous_stamp
        except Exception:
            changed = True
            updated = now
        return external, selected, updated, True, changed
    except Exception as error:
        external, selected, stamp = last_good()
        print(f"GitHub refresh failed ({error}); retaining last-good data from {stamp.isoformat()}")
        return external, selected, stamp, False, False


def replace_block(text: str, name: str, body: str) -> str:
    start = f"<!-- profile-{name}:start -->"
    end = f"<!-- profile-{name}:end -->"
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError(f"expected exactly one {start} and {end}")
    before, rest = text.split(start, 1)
    _, after = rest.split(end, 1)
    return f"{before}{start}\n{body.rstrip()}\n{end}{after}"


def live_markdown(selected: list[dict], updated: dt.datetime) -> str:
    notes = json.loads(DATA.read_text(encoding="utf-8")).get("external_notes", {})
    lines = [
        '<p align="center">',
        '  <img width="100%" src="./assets/profile-details.svg" alt="GitHub profile details and contribution trend.">',
        '</p>',
        '<p align="center">',
        '  <img width="57%" src="./assets/stats-card.svg" alt="GitHub activity statistics.">',
        '  <img width="41%" src="./assets/commit-languages-card.svg" alt="Most used languages across GitHub commits.">',
        '</p>',
        '',
        '**Outside my repos**',
        '',
    ]
    for item in selected:
        key = f"{item['repo']}#{item['number']}"
        note = notes.get(key, item["title"])
        # `published_external` only hands over merged PRs; render any other status
        # honestly so a regression shows up instead of being mislabelled.
        marker = "✓ merged" if item["status"] == "merged" else f"↗ {item['status']}"
        lines.append(f"- {marker} → [{item['repo']} #{item['number']}]({item['url']}) · {note}")
    stamp = updated.strftime("%d %b %Y · %H:%M SGT").lstrip("0")
    lines.extend(["", f"<sub>↻ refreshed {stamp}</sub>"])
    return "\n".join(lines)


def footer_markdown(today: dt.datetime) -> str:
    content = json.loads(DATA.read_text(encoding="utf-8"))
    pool = content["footer_lines"]
    item = pool[int(today.strftime("%Y%j")) % len(pool)]
    text = html.escape(item["text"])
    author = item.get("author")
    suffix = f" — {html.escape(author)}" if author else ""
    return f'<sub><em>“{text}”</em>{suffix}</sub>'


def main() -> None:
    external, selected, updated, fresh, changed = collect()
    text = README.read_text(encoding="utf-8")
    text = replace_block(text, "live", live_markdown(selected, updated))
    text = replace_block(text, "footer", footer_markdown(dt.datetime.now(SGT)))
    README.write_text(text, encoding="utf-8", newline="\n")

    if fresh and changed:
        snapshot = {
            "external": external,
            "selected_external": selected,
            "updated_at": updated.isoformat(),
        }
        LIVE.write_text(
            json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    state = "Updated" if changed else ("Checked" if fresh else "Retained")
    print(f"{state} {len(external)} upstream PRs; showing {len(selected)} at {updated.isoformat()}")


if __name__ == "__main__":
    main()
