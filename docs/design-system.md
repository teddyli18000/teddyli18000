# Native type & symbols

The profile intentionally avoids generated hero artwork. Its visual language is the GitHub page itself: typography, spacing, Unicode symbols, emoji, concise copy, and real links.

## Read order

1. **Identity** — name, one-line axis, four compact focus cues.
2. **Selected work** — one featured project, then two concise shipped utilities.
3. **Current lines** — quieter exploratory work.
4. **Open source / live** — three truthful metrics and three external PRs, refreshed automatically.
5. **Side quests** — personality through odd, real utilities rather than abstract decoration.

## Rules

- No AI-generated images or generated local hero assets.
- No badge walls, typing SVGs, streaks, trophy grids, or language dashboards.
- Emoji must carry meaning, not fill space.
- Remote images are optional, non-critical, and should come from stable public sources.
- The README remains useful if every remote image fails to load.

## Automation

`.github/workflows/refresh-profile.yml` runs every day at 00:17 SGT and can also be dispatched manually. It refreshes GitHub contribution data, upstream PRs, the freshness timestamp, and one date-seeded footer line. Pull requests run the same generator/checker without committing.
