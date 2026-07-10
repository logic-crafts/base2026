# Alex Personal Site Home — Visual Rescue Packet

Created: 2026-07-04 19:03 Europe/Minsk
Scope: `https://aggressorbulkit.online/` Home only, with Base2026 `/knowledge/ai-visibility-pages/` as the closest internal visual reference.
Production status: **not touched**. This packet converts Alex's voice feedback into an agent-ready redesign brief.

## Source evidence

Live Home captured with `?qa=visual-rescue-20260704`:

- URL: `https://aggressorbulkit.online/`
- stylesheet: `/knowledge/static/styles.css?v=base2026-ai-pages-cardfix-20260628` + `/alex-native/styles.css?v=alex-home-form-trim-20260703b`
- viewport measured: `1280x577`, DPR 1
- no horizontal overflow: `scrollWidth=1280`, `clientWidth=1280`
- header height: `67px`
- hero: `top=123`, `height=320`, `width=1180`, `left=50`, `bottom=443`
- H1: `38.4px`, line-height `34.56px`, width `524px`
- first post-hero CTA bridge: `height=139`, bottom `604` — clipped by first viewport on 577px-high MacBook-like screen
- first split/form section: `height=687`
- repeated H2 sections on Home: `48px` / `48.96px` line-height

Reference page captured:

- URL: `https://aggressorbulkit.online/knowledge/ai-visibility-pages/`
- stylesheet: `/knowledge/static/styles.css?v=base2026-tiktok-public-20260703-1711`
- hero: `height=358`, `width=1080`, `left=100`
- reference hero text: `46.72px`, but page feels more deliberate because it has stronger system framing and narrower container.

## Alex's criticism converted into requirements

### 1. Global composition / first screen

Problem:
- The Home feels oversized and awkward on a MacBook-height viewport.
- Main container is too wide for the page rhythm: only `50px` side air at 1280px.
- Hero + CTA bridge + form section create stacked blocks that compete instead of a single first-screen funnel.

Requirements:
- Use a calmer maximum content width around `1080px` for premium sections, matching the better Base2026 page rhythm.
- Make the first viewport intentional: hero should own the screen or deliberately hand off to one compact next step, not show a half-cut second block.
- Reduce CTA duplication in the first two screens.

### 2. Hero

Problem:
- Hero feels like a large poster/banner, not a controlled conversion entry.
- Text/photo balance is not premium enough; there is dead horizontal space and edge pressure.
- The Home hero and Base2026 hero feel like different systems.

Requirements:
- Rebuild the hero as one source-of-truth pattern, not a patched banner.
- Keep orange/Base2026 warmth, but add stronger internal grid, better text/photo balance, and one clear action path.
- Decide whether the form is inside hero, immediately below hero, or later — not all at once.

### 3. Form

Problem:
- Current form looks like it came from another site.
- Full-width black submit button is visually heavy.
- Form competes with left-side CTA buttons.

Requirements:
- Convert form into an integrated snapshot card with the same surface language as the rest of the page.
- Keep only required fields: Website URL, Your name, Email.
- Use one primary submit action; remove duplicate left-column CTA in the same section.
- Form should look like part of the product/consulting system, not a generic embedded form.

### 4. Static vs clickable cards

Problem:
- `Why this matters` static cards and `Focused consulting` clickable service cards look visually identical.
- Clickable and non-clickable surfaces must not have the same affordance.

Requirements:
- Static explanation cards: quiet, non-button surfaces, no link affordance.
- Service/action cards: visibly clickable, with arrow/CTA row, hover/focus states, stronger edge/action treatment.
- Do not use `01 / 02 / 03` in content cards unless the number carries real procedural meaning. Current numbers carry no meaning and should be removed.

### 5. Base2026 section

Problem:
- `Where Base2026 fits` is reduced to more of the same cards/buttons.
- It should prove method and depth, not just be another CTA block.

Requirements:
- Make Base2026 an evidence/proof band: small lab/search/product preview, 2–3 proof bullets, and one restrained link to AI Visibility Lab.
- Preserve boundary: Base2026 is product/evidence layer, not an agency/services island.

### 6. FAQ

Problem:
- FAQ is visually wrong/spoiled and currently behaves like ordinary cards.

Requirements:
- Use a proper premium accordion (`details/summary`) with calm dividers, not 3 identical cards labeled FAQ.
- Keep it compact and near the end; no visual competition with offer/service cards.

### 7. CTA/button discipline

Problem:
- Buttons vary and repeat too much: header CTA, bridge buttons, split-section CTA buttons, form button, footer buttons.

Requirements:
- Define 3 button types only:
  1. Primary orange — one main conversion path.
  2. Secondary dark/text — supporting action.
  3. Base2026 green/accent — only for Base2026 proof route.
- Same radius, height, typography, and alignment across page.
- Avoid multiple equal-weight CTAs in the same viewport.

## Recommended design direction

Do **not** keep patching this page block-by-block. The visual system is now internally inconsistent.

Recommended route: **Editorial Conversion System**

- Keep Base2026 warmth and orange authority.
- Narrow the premium wrapper to the Base2026 reference rhythm.
- Hero becomes: strong headline + short deck + one action + compact proof chips + integrated portrait.
- Snapshot form becomes one designed card, either in hero side rail or directly below hero as a compact conversion strip.
- `Why this matters` becomes calm proof/problem tiles without numbers.
- `Focused consulting` becomes a real service navigation grid with click affordance.
- Base2026 becomes evidence/lab proof, not another identical card section.
- FAQ becomes accordion.

Alternative routes to preview before implementation:

1. **Editorial Conversion System** — strongest fit for personal expert + premium consulting.
2. **Product Lab System** — more Base2026/product-library feel; useful if Home should position Alex as operator of a research platform.
3. **Minimal Consulting System** — quieter, more expensive-feeling, fewer blocks; useful if we want to reduce visual noise and keep conversion simple.

## Vertical slices for implementation

### Slice 1 — Home first-screen rescue

Visible outcome:
- Hero + immediate handoff fit cleanly on MacBook-like viewport and no longer feel like giant/cut blocks.

Acceptance:
- [ ] desktop screenshot captured at 1280x577 and 1440x800
- [ ] mobile screenshot captured at 390x844
- [ ] `scrollWidth === clientWidth`
- [ ] no duplicate equal-weight CTA in first viewport
- [ ] hero wrapper width around the approved premium rhythm, not edge-stretched

### Slice 2 — Form integration

Visible outcome:
- Snapshot form looks native to the page, with three fields and one primary submit.

Acceptance:
- [ ] only Website URL, Your name, Email visible
- [ ] form action still posts to `/wp-admin/admin-post.php`
- [ ] no business-name/contact fields reintroduced
- [ ] form card visually matches hero/section surfaces

### Slice 3 — Cards and service affordance

Visible outcome:
- Static explanation cards and clickable service cards are visually different.

Acceptance:
- [ ] numbers removed from `Why this matters`
- [ ] non-click cards do not look clickable
- [ ] service cards have arrow/action affordance and focus/hover states
- [ ] 4 service cards are arranged as balanced 2x2 or 4-up, not a broken row

### Slice 4 — Base2026 proof band + FAQ accordion

Visible outcome:
- Base2026 feels like evidence/product proof; FAQ feels like a premium accordion.

Acceptance:
- [ ] Base2026 section includes evidence/product framing, not duplicate generic cards
- [ ] FAQ is real accordion and does not render as ordinary repeated cards
- [ ] CTA colors follow the 3-type rule

## Out of scope until Alex approves a route

- Production deploy.
- SEO/content expansion.
- Public Base2026 `/knowledge/` release.
- Git commit/push.
- Rewriting service-detail pages beyond shared token impact.

## Next safe step

Create a visual moodboard/preview with the three routes above using real Home content, choose one route, then implement only that route and verify live desktop/mobile before reporting completion.
