# Profile README operating notes

- `README.md` is the public surface. Keep project claims linkable and private work high-level.
- `scripts/generate_profile.py` owns the marked live/footer blocks plus `assets/live-*.svg` and `data/live.json`.
- `scripts/render_assets.py` owns the committed hero, Millikan vignette, and Side Quest vignette assets. It is a manual/local step so decorative assets do not churn daily.
- The hero is editorial motion: mineral paper, serif type, and slow translucent ribbons. Do not reintroduce node graphs, pseudo-signals, status lights, bounded blobs, giant glass objects, or startup-dashboard motifs.
- Keep the small GIFs visible enough to read: Millikan is a measurement vignette; Side Quest is an app-window detour. Do not reduce them back to ambiguous marks.
- Preserve light/dark and reduced-motion `<picture>` source order. GitHub is the renderer; the profile must not require inline JS or CSS.
