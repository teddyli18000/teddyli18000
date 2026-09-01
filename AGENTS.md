# Profile README operating notes

- `README.md` is the public surface. Keep it GitHub-native, compact, and easy to scan.
- Prefer mature, widely used profile components over reimplementing them when they already solve the problem well.
- `stats-organization/github-readme-stats-action@v2` owns the compact activity card; `vn7n24fzkq/github-profile-summary-cards@release` owns profile-details / commit-language data and animation. The README references committed SVGs, never live Vercel/Camo card URLs.
- `scripts/polish_cards.py` may adapt mature generated SVGs to the shared profile palette and truthful labels, but must not replace their data collection logic.
- Shields.io owns the focused tech-stack badges; `Platane/snk@v3` owns the contribution snake.
- `scripts/generate_profile.py` owns only the profile-specific upstream PR list, visible refresh timestamp, date-seeded footer rotation, and `data/live.json` last-good state.
- Do not add AI-generated art, ambient banners, decorative background strips, typing SVGs, trophies, visitor counters, or ad-hoc generic stats implementations.
- The work/current/side-quest area is intentionally one compact three-column HTML table.
- Keep the hero free of throwaway microcopy. The only rotating prose belongs in the footer and should be a sourced quote or a considered original line.
- Emoji, Unicode symbols, native Markdown/HTML, and a few lightweight animated emoji are acceptable when they add personality rather than decoration.
- Public contribution links must be truthful; on API failure retain the last-good snapshot.
- The profile refresh workflow uses several off-peak trigger windows per hour for scheduler reliability, while the generator advances the visible timestamp at most once per SGT hour.
- The snake workflow refreshes the contribution animation separately on the `output` branch.
- Keep private/current work high-level and public project claims directly linkable.
