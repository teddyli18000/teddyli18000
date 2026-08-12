# Profile README operating notes

- `README.md` is the public surface. Keep project claims linkable and private work high-level.
- `scripts/generate_profile.py` owns the marked live and footer blocks plus `assets/live-*.svg` and `data/live.json`.
- `scripts/render_assets.py` owns committed hero, live-signal, and side-quest assets. It is an intentional local/manual step because those assets should not churn daily.
- Run `python scripts/generate_profile.py` with `GH_TOKEN`, or with an authenticated `gh` CLI available. Run raster generation with the pinned packages in `requirements-assets.txt`.
- Preserve the light/dark and reduced-motion `<picture>` source order. GitHub is the target renderer; no inline script or CSS may be required for comprehension.
