# Profile README operating notes

- `README.md` is the public surface. Keep it GitHub-native, text-first, and easy to scan.
- Do not add AI-generated art, local hero renders, badge walls, typing SVGs, or stats widgets.
- Emoji, Unicode symbols, native Markdown/HTML, and a small non-critical public image are acceptable when they add personality rather than decoration.
- `scripts/generate_profile.py` owns only the marked live/footer blocks and `data/live.json`.
- Public metrics and contribution links must be truthful; on API failure retain the last-good snapshot.
- The scheduled Action runs daily at 00:17 SGT and commits only README/data changes.
- Keep private/current work high-level and public project claims directly linkable.
