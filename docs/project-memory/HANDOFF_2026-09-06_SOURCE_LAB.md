# Source Laboratory presentation candidate — 2026-09-06

Status: HQ accepted the desktop/mobile composition, hero and typography;
the requested final copy and YouTube footer delta is complete. Ready for HQ
private-runtime integration. No commit, push, merge, deployment or intake run performed.

## Scope and source

Branch `codex/base2026-source-lab-20260906`, public source base
`925761c1d0d4d0a03b8ace93abcbb264af6bb014`. The canonical builder uses the
latest HQ-accepted public asset artifact with the released member runtime and
both WordPress downloads. The source checkout's default assets path is stale.

Shared core/header/footer cover the corpus, docs, journal and member shell.
The homepage has the approved conceptual paper/prism/action image; tool pages
use consistent source-paper forms and editorial rows. The workspace places
search before background context while preserving its content and hooks.
Projected D1 sources reuse the canonical asset header/footer, with a bounded
read and a graceful breadcrumb fallback; queries and public payloads are
unchanged. The local source animation uses GSAP 3.15.0 core/ScrollTrigger.

## Acceptance

- Canonical full artifact: 4,302 files / 98,241,512 bytes (v4).
- Artifact tree SHA-256:
  `9541d2f254482852fa686fd56e2318dfcd756a0c7b939f6bdc041a814adb8d18`.
- Builder public/private, path, media, sitemap and binary preservation checks
  pass; private/local marker counts are zero.
- Current public member script and WordPress 0.1.0/0.1.1 ZIPs are byte-identical
  to the accepted input. `--retain-member-script` is explicit and tested;
  the existing default behavior remains available.
- Python: 116 relevant builder, design, tool, member, editorial and publication
  tests pass. JavaScript: 13 motion/tools-runtime tests pass. Worker: full
  suite 647 tests passed; final projected-source delta recheck 40 tests passed.
  Typecheck and explicit-assets Wrangler dry-run pass.
- Native in-app browser: 15 representative routes at 1440 and 390 px, each
  with one canonical header/footer, no horizontal overflow and no captured
  console errors. These are page-family checks, not a 4,302-page live crawl.
- Actual replay/pause/resume, pause across resize, reduced-motion static
  rendering, no-JavaScript content/native menu, desktop/mobile Escape and
  focus restoration verified. Scroll progress moves naturally with the page;
  the H1 remains still. Lifecycle/bfcache cleanup also has runtime tests.
- Public API adapter smoke: homepage evidence brief; Evidence Search returns
  10 of 29 admitted internal-linking matches; source comparison resolves
  2 records / 2 sources / 2 creators; brief resolves 1 public record and
  bounded excerpt; Page Source Check changes title Review to Observed after
  correcting the fictional supplied HTML. Network/indexing remain Unknown.

The final v4 pass changes only the six HQ-supplied text strings and adds
`Base2026 on YouTube` to the shared footer. All 4,212 changed artifact files
match those exact substitutions; other files, member runtime, downloads,
media and the projected-source renderer/patch remain byte-identical to v3.
The 16 affected homepage/tools tests and the canonical build gates pass.
Original browser screenshots describe the accepted v3 layout; this pass did
not use the browser because HQ owns its review surface.

## Review limits and next action

Local preview is `http://127.0.0.1:8753/`, now serving v4. Its development adapter sends only
public read-only retrieval and synthetic source-check requests to the public
API, omits cookies and absorbs analytics events. It aliases the Evidence
Search API URL for localhost; production templates retain their original
endpoint. Canonical links can remain origin-bound in this preview. The member
view is explicitly signed out; no real Google login or private collection
mutation is claimed. The projected-source preview uses the actual candidate
renderer with an identified synthetic public row.

HQ's current private auth-recovery Worker is newer than public main. The
projected-source presentation patch passes `git apply --check` against that
private source. HQ must apply this narrow patch to its accepted runtime and
complete the combined release checks; the public-source dry-run is not a
replacement for that runtime. No private implementation was copied into Git.

Review source in this worktree and the existing Design office's
`source-lab-20260906` receipt/screenshots. Main groups: canonical templates;
`templates/assets/source-lab`; local vendor/runtime; canonical builder;
projected-source Worker renderer; focused tests; this handoff and NEXT_ACTION.
HQ owns private-runtime integration and release. Chief remains the sole AgencyOS/board writer.

Suggested commit: `feat: apply Source Laboratory design across public surfaces`
