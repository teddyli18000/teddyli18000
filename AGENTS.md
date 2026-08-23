# Profile README operating notes

- `README.md` is the public surface. Keep it GitHub-native, text-first, and easy to scan.
- Do not add AI-generated art, local hero renders, badge walls, typing SVGs, or stats widgets.
- Emoji, Unicode symbols, native Markdown/HTML, and a few lightweight non-critical public animation accents are acceptable when they add personality rather than decoration.
- `scripts/generate_profile.py` owns only the marked live/footer blocks and `data/live.json`.
- Public metrics and contribution links must be truthful; on API failure retain the last-good snapshot.
- The scheduled Action checks every two hours and only commits when README/data output actually changes.
- Keep private/current work high-level and public project claims directly linkable.
