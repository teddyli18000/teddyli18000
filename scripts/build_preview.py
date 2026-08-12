#!/usr/bin/env python3
"""Render README.md through GitHub's Markdown API and wrap it for local QA."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    markdown = (ROOT / "README.md").read_text(encoding="utf-8")
    payload = json.dumps({"text": markdown, "mode": "gfm", "context": "teddyli18000/teddyli18000"})
    rendered = subprocess.run(
        ["gh", "api", "markdown", "--input", "-"],
        input=payload,
        text=True,
        capture_output=True,
        check=True,
        encoding="utf-8",
    ).stdout
    css = """
    :root{color-scheme:light dark}*{box-sizing:border-box}body{margin:0;background:#f6f8fa;color:#1f2328;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}.shell{width:min(896px,calc(100% - 32px));margin:48px auto;background:#fff;border:1px solid #d0d7de;border-radius:8px;padding:32px}.markdown-body{font-size:16px;line-height:1.5;word-wrap:break-word}.markdown-body img{max-width:100%;height:auto;background:transparent}.markdown-body h2{margin:48px 0 20px;padding-bottom:.3em;border-bottom:1px solid #d8dee4;font-size:1.5em}.markdown-body h3{margin:28px 0 8px;font-size:1.25em}.markdown-body p{margin:0 0 16px}.markdown-body a{color:#0969da;text-decoration:none}.markdown-body hr{height:1px;border:0;background:#d8dee4;margin:32px 0}.markdown-body blockquote{margin:0 0 16px;padding:0 1em;color:#59636e;border-left:.25em solid #d0d7de}.markdown-body sub{color:#59636e}.markdown-body details{margin-top:30px}.markdown-body ul{padding-left:2em}.markdown-body li+li{margin-top:.35em}@media(prefers-color-scheme:dark){body{background:#0d1117;color:#f0f6fc}.shell{background:#0d1117;border-color:#30363d}.markdown-body h2{border-color:#21262d}.markdown-body a{color:#58a6ff}.markdown-body hr{background:#30363d}.markdown-body blockquote,.markdown-body sub{color:#8b949e}}@media(max-width:600px){.shell{width:100%;margin:0;border:0;border-radius:0;padding:16px}.markdown-body{font-size:14px}.markdown-body h2{margin-top:36px}.markdown-body h3{font-size:1.12em}}
    """
    output = f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>Profile README preview</title><style>{css}</style></head><body><main class='shell'><article class='markdown-body'>{rendered}</article></main></body></html>"
    (ROOT / "preview.html").write_text(output, encoding="utf-8")
    print(ROOT / "preview.html")


if __name__ == "__main__":
    main()

