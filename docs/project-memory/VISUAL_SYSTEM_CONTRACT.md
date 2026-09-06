# Base2026 Visual System Contract

Last updated: 2026-09-06 (Source Laboratory source candidate; release requires HQ review)
Authority: `b26-independent-v1`

## Rule

Base2026 is an independent research product. Every public route must preserve
the current cool-blue Base2026 shell and must not inherit the retired Alex
Personal, WordPress V4, warm cream/orange, Stitch, or generic AI-dashboard
designs.

## Canonical source authority

The final design authority is:

- `templates/base2026-core.css` — tokens, components and compatibility layer;
- `templates/base2026-startup-shell.css` — startup-only shell adjustments;
- `templates/base2026-startup-header.html` and
  `templates/base2026-startup-footer.html` — the only public header/footer;
- `templates/base2026-startup-homepage.html/.css` — homepage content/layout;
- `templates/base2026-source-lab.js` and the pinned local GSAP core /
  ScrollTrigger assets — progressive illustration and navigation behavior;
- `scripts/build-base2026-cloudflare-release.py` — the only production release
  boundary that may normalize retained generated pages;
- the builder tests and design-authority gate — release blockers, not optional
  visual checks.

`web/static/styles.css` may remain as retained component/search styling, but it
is loaded beneath `base2026-core.css` and is not allowed to define the product
shell or palette.

## Tokens

- Canvas: `#F7F9FC`
- Surface: `#FFFFFF`
- Muted surface: `#F0F4FA`
- Ink: `#0B1736`
- Muted text: `#526177`
- Line: `#DCE5F0`
- Evidence accent: `#315EEA`
- Accent hover: `#254AC0`
- Dark CTA: `#10213F`
- Positive state: `#147A5A`
- Control radius: `10px`
- Surface radius: `16px`
- Desktop shell: `1160px`
- Mobile gutter: `14px` per side
- Typography: Manrope for product copy; Geist Mono for compact labels/data

## Protected experience

- one sticky Base2026 header and one Base2026 footer;
- compact, readable search and evidence density;
- visible creator/source attribution and original-source links;
- source, topic, creator, roadmap, methodology and API pages use the same
  palette and component grammar;
- full-pill shapes are limited to tags and filters, not every button/card;
- one visible H1, normal focus rings, labelled controls and zero horizontal
  overflow at 390px;
- no visual change is complete until desktop and mobile screenshots, DOM
  checks, console checks, search/API checks and the release receipt pass.

## Source Laboratory presentation

The owner-authorized candidate keeps the independent palette and typography.
Use a compact grouped navigation, a source-oriented hero, clear editorial
rows and calm working forms. Context, attribution and unknowns remain visible.
The conceptual paper/prism/action artwork is separate from measured data.

Motion is an enhancement: a finite source-to-excerpt-to-action sequence and
natural scroll progress on its explanatory section. Headlines, forms, results
and member data remain readable without JavaScript. Respect reduced motion;
pause offscreen or in a hidden tab, preserve an explicit user pause across
breakpoints and bfcache, and offer Pause, Resume and Replay. No scroll locking,
pinning, snapping, infinite loops or progress claims based on illustrations.

## Forbidden regression markers

- `aggressorbulkit.online` or personal-service CTAs in final public HTML;
- Alex Personal header/footer classes or commercial service navigation;
- warm authority colors `#c84f07`, `#d9730d`, `#ef6b13`, `#fffaf0`;
- WordPress forms, `/wp-admin/`, pricing or free-audit routes;
- decorative `01 / 02 / 03` presentation as a page-wide motif;
- dark cyber, purple/pink gradient or unstyled generic AI-dashboard shells;
- a generator, hotfix or VPS script becoming a second production design
  authority.

## Legacy quarantine

Historical Personal V4, Stitch, Search V1, Source Detail V2 and template
migration assets remain in Git only as compatibility/history. They may not be
called by the Cloudflare production builder or copied into a release as shell
authority. Exact paths and deprecation rules are in
`BASE2026_DESIGN_AUTHORITY_AND_LEGACY_QUARANTINE_2026_08_28.md`.

Do not delete historical assets merely because their names look old. First
prove that no active generator, test, rollback or migration depends on them;
then move them in a separately reviewed archive change.
