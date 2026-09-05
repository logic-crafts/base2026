# Tools Studio presentation and media candidate — 2026-09-05

Status: reviewed source candidate. Local browser QA passed. This is not a
deployment receipt. Builder integration and public release belong to HQ.

## Scope and baseline

Branch: `codex/base2026-tools-media-20260905`, based on public main after PR54,
`d5116a3f06ecfa0bd4888b4417d4e6227b728f8f`.

Continue phase29 through the existing Tools Studio. The approved direction is
a paper-blue evidence workbench: source cards, a contextual passage with its
attribution attached, and a working brief. Preserve the blue/white/navy
`b26-independent-v1` system, Manrope/Geist Mono and the existing Cloudflare brand.

Only the hub's HTML/CSS/JS, its two scoped test files, the four reviewed media
assets, their manifest and this unique handoff change. The WordPress section of
the shared Studio stylesheet remains byte-identical to the baseline. Core,
homepage, header/footer, member/auth, Worker/API, public data and builder are
outside this change. No shared project-memory files were edited in parallel.

## Result

- A larger illustrative workbench replaces the dense row of pixel robots.
  Four immediate keyboard-accessible stations retain the existing workflow.
  The final station is labelled Use, with a brief and human decision as output.
- Evidence Search is the featured first task, with an actual public pre-query
  form capture. Other cards identify the practitioner job and retain their
  input, output, limits and real destination.
- The existing finite illustration path remains pauseable, stops offscreen or
  in a hidden document, and replays only on an explicit action. Completion now
  offers Replay illustration; reduced motion disables its motion control.
- Cards reveal once on scroll using transform/opacity and the existing easing
  tokens. Keyboard focus, reduced motion, print and no-JS retain visible content.
  No GSAP dependency is warranted for this bounded explanatory sequence.
- Static station buttons are inert and the motion toggle hidden until JS is
  ready. All five product actions and the explanatory content remain available
  without JS. Public counters retain unavailable/stale states and server time.
- The Tools page has its own social preview metadata. The square product card
  shows the actual Evidence Search form before a query, not a fabricated result.

## Selected assets

All source paths below are under `templates/assets/tools-studio/`.
The [asset manifest](../../templates/assets/tools-studio/asset-manifest.json)
records exact hashes, bytes, dimensions, alt text, source and accessibility notes.

| File | Dimensions | Bytes | Use |
| --- | --- | ---: | --- |
| `evidence-workbench.webp` | 1200 × 800 | 46,250 | Hero/overview conceptual illustration |
| `evidence-search-interface.webp` | 1203 × 744 | 42,796 | Actual pre-query Evidence Search form |
| `tools-studio-social.png` | 1200 × 630 | 241,571 | Social landscape and Tools OG preview |
| `evidence-search-card.png` | 1080 × 1080 | 162,507 | Square Evidence Search product card |

The master was generated with the real built-in imagegen tool. Its model
version was neither selectable nor verified. No GPT Image2.5 claim is made.
The form was captured from the signed-out public Evidence Search page at
2026-09-05T18:54:57.021Z; no query was submitted. It includes no private record,
authentication, result claim or third-party video material. Exports combine
that selected imagery with Base2026-authored typography and layout. No EXIF,
IPTC or XMP metadata is present in the four selected files.

Raw/master images, complete screenshots, the generation prompt, export-layout
sources and detailed browser receipts stay in the established private Studio
design-media directory. Growth receives only the selected exports and manifest.
Candidate URLs in the manifest are not live/upload receipts.

## Exact builder integration — HQ action

The existing builder already writes the three Studio template files. It does
not copy arbitrary `templates/assets/` images. Before any release of this
candidate, insert this explicit binary mapping alongside the Studio CSS/JS
emission in `scripts/build-base2026-cloudflare-release.py`:

```python
for name in (
    "evidence-workbench.webp",
    "evidence-search-interface.webp",
    "tools-studio-social.png",
    "evidence-search-card.png",
):
    write_generated_public_file(
        f"static/assets/tools-studio/{name}",
        (PROJECT_ROOT / "templates" / "assets" / "tools-studio" / name).read_bytes(),
        kind="binary",
    )
```

Do not glob a private media directory or copy master files. The manifest is
review documentation and is not required as a served asset. No new JS library,
CSP exception, font, API or Worker change is needed. Existing social metadata
handling preserves this page's explicit `og:image` and `twitter:image` tags.

Builder acceptance must assert these exact four binary paths/hashes and the
Tools social-image URL, and confirm the complete retained-source/public-data
publication gate. Recheck the existing shared shell using the normal release
process; this local page preview is not a complete 4,286-file release artifact.

## Verification and review

- `python3 -m pytest tests/test_base2026_tools_studio.py tests/test_build_base2026_cloudflare_release.py -q`: 43 passed.
- `node --test tests/base2026_tools_studio_runtime.test.js`: 8 passed, including
  hidden/offscreen work, stale counters, keyboard tabs, single-action replay,
  all-card reveal and dynamic reduced-motion handling.
- Independent bounded executor owned only these tests; Studio root reviewed
  the result, implementation, publication boundary and final rendered output.
- Disposable local Chromium: 1440 × 1000 and 390 × 844; zero horizontal
  overflow, zero console/page errors and all images loaded in the final pass.
  One H1, keyboard arrows/Home/End, static no-JS actions, reduced motion and
  preference change, offscreen pause and explicit service failure all passed.
- Public counts were read through the preview's bounded public-stats relay at
  19:00:19Z and 19:00:26Z: 2,275 documents, 1,649 sources, 125 evidence routes,
  183 cards. These are dated QA reads, never static fallbacks or user activity.
- Both media exports fit their exact canvases with no clipping/overflow.
  Desktop, mobile, workbench, full-page, reduced-motion and no-JS candidates
  are retained privately. The new in-page raster payload totals 89,046 bytes;
  only the hero is high-priority, and the product screenshot is lazy-loaded.
- `git diff --check` passed. Public review admits only authored UI, the
  intentional public product capture, selected generated illustration/export
  files and public-safe tests/docs. No raw research, secrets or operational
  data enters Git.

## Next action

HQ reviews the candidate, adds the exact builder mapping in its integration
scope, then performs its normal retained-artifact audit and release/readback.
Growth may prepare distribution from the selected exports; posting and a
public media URL require their separate authorized receipt. No merge or
deployment was performed by Studio.

Suggested commit: `Polish Tools Studio and add reviewed product media`.
