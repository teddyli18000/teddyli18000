# Profile README operating notes

- `README.md` is the public surface. Keep it GitHub-native, compact, and easy to scan.
- Prefer mature, widely used profile components over reimplementing them when they already solve the problem well.
- Current approved external building blocks: `github-readme-stats` for language stats, Shields.io for stack badges, and `Platane/snk@v3` for the contribution snake.
- Keep only one custom local visual: `assets/activity-card.svg`, because it carries profile-specific public metrics and the upstream merged-PR ratio.
- Do not add AI-generated art, local hero renders, ambient banners, decorative background strips, typing SVGs, trophies, visitor counters, or extra generic stats cards.
- Emoji, Unicode symbols, native Markdown/HTML, and a few lightweight animated emoji are acceptable when they add personality rather than decoration.
- `scripts/generate_profile.py` owns the marked live/footer blocks, `assets/activity-card.svg`, and `data/live.json`.
- Public metrics and contribution links must be truthful; on API failure retain the last-good snapshot.
- The profile refresh Action checks every two hours and only commits when generated output actually changes.
- The snake workflow refreshes the contribution animation separately on the `output` branch.
- Keep private/current work high-level and public project claims directly linkable.
