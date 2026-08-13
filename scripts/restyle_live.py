#!/usr/bin/env python3
"""Restyle the generated live GitHub snapshot into an editorial data strip."""
from __future__ import annotations

import datetime as dt
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "data" / "live.json"
ASSETS = ROOT / "assets"
SGT = dt.timezone(dt.timedelta(hours=8), name="SGT")


def svg(stats: dict, updated: dt.datetime, dark: bool) -> str:
    background = "#111316" if dark else "#f8f6f1"
    ink = "#f1ede5" if dark else "#211f1c"
    muted = "#9b9891" if dark else "#78736b"
    rule = "#35383c" if dark else "#d9d3c9"
    warm = "#c98969" if dark else "#c86e52"
    cool = "#7f9990" if dark else "#87998a"
    stamp = updated.strftime("%d %b %Y · %H:%M SGT").lstrip("0")
    metrics = [
        (str(stats["contributions"]), f"contributions · {stats['year']}"),
        (str(stats["active_public_repos"]), "active public repos"),
        (str(stats["upstream_prs"]), "upstream PRs"),
    ]
    x_positions = [58, 352, 646]
    nodes = "".join(
        f'<text x="{x}" y="118" class="value">{html.escape(value)}</text>'
        f'<text x="{x}" y="148" class="label">{html.escape(label)}</text>'
        for x, (value, label) in zip(x_positions, metrics)
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="220" viewBox="0 0 960 220" role="img" aria-label="Public GitHub activity">
<defs><linearGradient id="wash" x1="0" x2="1"><stop offset="0" stop-color="{warm}" stop-opacity=".14"/><stop offset=".55" stop-color="{cool}" stop-opacity=".08"/><stop offset="1" stop-color="{warm}" stop-opacity=".05"/></linearGradient><filter id="blur"><feGaussianBlur stdDeviation="22"/></filter></defs>
<rect width="960" height="220" fill="{background}"/>
<path d="M-40 150 C220 72 590 224 1000 52" fill="none" stroke="url(#wash)" stroke-width="74" filter="url(#blur)"/>
<text x="902" y="38" text-anchor="end" class="stamp">updated {html.escape(stamp)}</text>
{nodes}
<path d="M58 166 H902" stroke="{rule}" stroke-opacity=".55"/>
<path d="M326 82 V156 M620 82 V156" stroke="{rule}" stroke-opacity=".45"/>
<style>text{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;fill:{ink}}}.stamp,.label{{font-size:12px;letter-spacing:.8px;fill:{muted}}}.value{{font-family:Georgia,"Times New Roman",serif;font-size:42px;font-weight:400}}</style>
</svg>'''


def main() -> None:
    stats = json.loads(LIVE.read_text(encoding="utf-8"))
    updated = dt.datetime.fromisoformat(stats["updated_at"].replace("Z", "+00:00")).astimezone(SGT)
    (ASSETS / "live-light.svg").write_text(svg(stats, updated, False), encoding="utf-8")
    (ASSETS / "live-dark.svg").write_text(svg(stats, updated, True), encoding="utf-8")
    print(f"Restyled live activity at {updated.isoformat()}")


if __name__ == "__main__":
    main()
