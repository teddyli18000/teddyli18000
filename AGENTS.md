# Profile README operating notes

- `README.md` is the public surface. Keep it GitHub-native, text-first, and easy to scan.
- Do not add AI-generated art, local hero renders, badge walls, typing SVGs, generic stats widgets, ambient banners, or decorative background strips.
- One custom local SVG data card is allowed under Open Source / Live when every visual element maps to truthful public data and the Action regenerates it.
- Emoji, Unicode symbols, native Markdown/HTML, and a few lightweight animated emoji are acceptable when they add personality rather than decoration.
- `scripts/generate_profile.py` owns the marked live/footer blocks, `assets/activity-card.svg`, and `data/live.json`.
- Public metrics and contribution links must be truthful; on API failure retain the last-good snapshot.
- The scheduled Action checks every two hours and only commits when README/data/card output actually changes.
- Keep private/current work high-level and public project claims directly linkable.
