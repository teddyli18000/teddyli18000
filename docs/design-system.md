# Living Editorial Field

The profile is a living editorial field: one warm/cool visual atmosphere that
holds a readable work ledger, exploratory threads, public contribution proof,
and a small branch of side quests. The page should feel composed when the
assets are absent; artwork adds rhythm and material, never a substitute for
content.

## Tokens

- **Canvas:** mineral white `#F7F4EE` and graphite `#101216`.
- **Ink:** `#1D2024` on light and `#F5F2EB` on dark.
- **Field:** restrained coral/amber and cyan accents, kept soft enough that
  links and headings remain primary.
- **Rules:** low-contrast neutral hairlines aligned to the shared 960 px
  measure.
- **Material:** a small translucent panel may hold the live instrument. Glass
  is jewelry for hierarchy, not a page-wide surface treatment.

## Material hierarchy

1. **Hero:** the identity field and first read. Desktop and narrow sources each
   provide light/dark animation plus reduced-motion PNG fallbacks.
2. **Selected Work:** Millikan AI is the editorial feature. Its tiny motion
   mark is a punctuation line; repository links and restrained metadata carry
   the claim. Screen Clone Manager and Baidu Drive Mover remain a compact
   secondary ledger.
3. **Current Lines:** an intentionally quieter exploratory note. Small models,
   AI developer infrastructure, and robotics & perception are boundaries of
   interest, not shipped-product claims.
4. **Open source / live:** generated public activity is a living instrument,
   with three truthful metrics, a timestamp, and directly clickable upstream
   PRs. It is not a dashboard or a stats wall.
5. **Side Quests:** a compact departure gesture and three odd utilities or
   experiments that reveal range without competing with the feature.

## Motion roles

- Hero motion establishes the field; the first frame must stand alone.
- The Millikan mark is a tiny handoff, not a second hero.
- The Side Quest asset is a short departure line; it should remain legible at
  its reduced height.
- Reduced-motion PNGs preserve composition and contrast, not a frozen loading
  state.
- The live SVG is static data-backed material. Its warm field and translucent
  panel provide atmosphere while three metrics remain the hard limit.

## Live data contract

Actions runs `scripts/generate_profile.py` with authenticated GitHub access.
The generator refreshes `README.md`'s marked live and footer blocks,
`assets/live-light.svg`, `assets/live-dark.svg`, and `data/live.json`.

The live instrument contains exactly three values: contributions YTD, active
public repositories, and upstream pull requests. A short native Markdown list
keeps three real external PRs clickable. If GitHub cannot be reached, the
generator retains the previous `data/live.json` snapshot and its timestamp;
it never invents a zero or placeholder value.

The footer is a date-seeded rotation from `data/content.json`, so daily refresh
does not produce random copy churn.

## Reference shelf

The original motion, glass, shader, and living-profile references remain
implementation research only. They belong in this document or source history,
not in the public README. The public surface should describe the work and the
evidence, not its parts bin.

- Glass studies: [liquid-glass-studio](https://github.com/iyinchao/liquid-glass-studio), [liquid-glass](https://github.com/archisvaze/liquid-glass), [liquidGL](https://github.com/naughtyduk/liquidGL), [shuding/liquid-glass](https://github.com/shuding/liquid-glass), [nikdelvin/liquid-glass](https://github.com/nikdelvin/liquid-glass)
- Motion studies: [paper-design/shaders](https://github.com/paper-design/shaders), [Cindori/FluidGradient](https://github.com/Cindori/FluidGradient), [liquid-shape-distortions](https://github.com/collidingScopes/liquid-shape-distortions)
- Living profile studies: [recent-activity](https://github.com/Readme-Workflows/recent-activity), [metrics](https://github.com/lowlighter/metrics), [guilyx](https://github.com/guilyx/guilyx), [creative-profile-readme](https://github.com/coderjojo/creative-profile-readme)
