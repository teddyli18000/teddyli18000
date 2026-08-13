# Profile README operating notes

- `README.md` is the public surface. Keep project claims linkable and private work high-level.
- `scripts/generate_profile.py` owns the marked live and footer blocks plus `assets/live-*.svg` and `data/live.json`.
- `scripts/render_assets.py` owns the committed desktop/narrow hero, Millikan mark, and side-quest assets. It composites the maintained `assets/hero-field-source.jpg` plate with code-rendered type and motion. This is an intentional local/manual step because those assets should not churn daily.
- Run `python scripts/generate_profile.py` with `GH_TOKEN`, or with an authenticated `gh` CLI available. Run raster generation with the pinned packages in `requirements-assets.txt`.
- Preserve the light/dark and reduced-motion `<picture>` source order. GitHub is the target renderer; no inline script or CSS may be required for comprehension.
