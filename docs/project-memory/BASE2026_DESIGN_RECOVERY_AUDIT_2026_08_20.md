# Base2026 Design Recovery Audit — 2026-08-20

## Decision

Base2026 must move to one **independent Base2026-only design contract**. No historical full-page candidate may be restored verbatim: every coherent candidate found in the repository either carries the retired Alex Personal shell, the warm/orange legacy treatment, or both. The selected implementation target is therefore `b26-independent-v1`: a compact cool-blue research-product system built at the generator/release boundary, not a repaint of generated HTML files.

This is a visual-system decision only. It does not authorize a deployment, a Cloudflare/D1/DNS change, a data import, an indexability change, or a Git operation.

## Audit scope and live evidence

The following production routes were loaded on 2026-08-20 at desktop 1440 px and mobile 390 px:

| Route family | Representative route | Final status | Overflow at both widths | Current visual authority observed |
| --- | --- | --- | --- | --- |
| Startup home | `/` | 200 | 0 px | `base2026-startup-homepage.html` plus startup shell; inline duplicate header and unrelated Tailwind-style footer |
| Search workspace | `/workspace/` | 200 | 0 px | old `static/styles.css` search surface plus injected startup header/footer |
| Topic index | `/topics/` | 200 | 0 px | generated legacy surface plus injected startup header/footer |
| Creator index | `/creators/` | 200 | 0 px | generated legacy surface plus injected startup header/footer |
| Info page | `/methodology.html` | 307 to canonical extensionless route, then 200 | 0 px | generated legacy surface plus injected startup header/footer |
| Roadmap | `/roadmap.html` | 307 to canonical extensionless route, then 200 | 0 px | legacy roadmap visual system plus injected startup header/footer |
| Support form | `/support.html` | 307 to canonical extensionless route, then 200 | 0 px | startup form template and startup shell |
| Partner form | `/partner.html` | 307 to canonical extensionless route, then 200 | 0 px | startup form template and startup shell |
| Source detail | `/sources/tiktok-video-7667726450258201869.html` | 307 to canonical extensionless route, then 200 | 0 px | generated legacy surface plus injected startup header/footer |

The screenshots are ephemeral local QA evidence under `/tmp/base2026-design-recovery.b7UuWX/`; they are intentionally not project assets or publication inputs. The Playwright session was closed after capture. One console **warning** was observed on the Roadmap: a legacy `mailto:` form is reported by Chrome as mixed-content-like. It is not a JavaScript exception, but the candidate must remove the warning or suppress the obsolete form before the zero-console-error acceptance gate.

The defect is therefore composition, not cache, routing, overflow, or a failed shell replacement:

- Home has the startup header but an inline Superdesign/Tailwind-style footer rather than `templates/base2026-startup-footer.html`.
- Workspace, Topics, Creators, Methodology, Roadmap and source detail retain `static/styles.css` and Geist while the injected header/footer use the warm startup Manrope system.
- Support and Partner use the startup system but inherit the same warm/orange tokens.
- `templates/base2026-startup-homepage.html` explicitly contains the unwanted right-side support-panel stripe. It must be deleted in the candidate; it is not a browser defect.

## Current source authorities

`scripts/build-base2026-cloudflare-release.py` is the correct release boundary. Its relevant controls are:

| Concern | Current authority | Candidate correction |
| --- | --- | --- |
| Root home | `templates/base2026-startup-homepage.html` and `templates/base2026-startup-homepage.css` | Replace duplicate raw header/footer and inline token rules with shared placeholders and the independent core stylesheet. Preserve copy, schema, links and route. |
| Shared shell | `templates/base2026-startup-header.html`, `templates/base2026-startup-footer.html`, `templates/base2026-startup-shell.css` | Replace as one semantic header/footer/core-token system. Retain only Base2026 navigation, approved GitHub/X icons and accessible labels. |
| Release injection | `_apply_startup_shell`, `_render_startup_page`, `_rewrite_workspace_html` in `scripts/build-base2026-cloudflare-release.py` | Inject the new core stylesheet/body marker exactly once and normalize all legacy route families without editing emitted HTML files one by one. |
| Workspace | staged former `index.html`, moved by `_rewrite_workspace_html` to `/workspace/` | Preserve D1 search, `POST /api/search/multi-search`, assets and runtime; scope its existing search CSS below the new global contract. |
| Topics, creators and source/detail pages | `scripts/generate-public-pages.py` emits their future source HTML; `web/static` supplies the current staged corpus | Replace legacy `site_header`, page-shell and footer authorities in the generator, then let the release boundary apply the one shell to existing staged pages. |
| Methodology and Roadmap | `scripts/generate-info-pages.py` emits future info pages | Replace the legacy page shell/footer and roadmap presentation at the generator level; preserve Markdown content, links, canonical/robots and form semantics. |
| Support, Partner, About and Privacy | `templates/base2026-{support,partner,about,privacy}.html` | Align them to the new core tokens and shared shell only. Do not change the Worker/D1 form contract. |

The current build already proves the correct architectural approach: it copies the existing public corpus into a fresh release candidate and applies a shell boundary. The recovery must extend that boundary rather than mass-editing thousands of emitted files.

## Design-lineage search

Inspected refs/worktrees included:

- `3a6cd166a4bae8df8063d8ac882225f47494aae8` — standalone startup surface;
- `de96c08f8f5e28f3ac0ce5236093b4f0b5c152e9` — current public startup-profile commit;
- `1f65bfcde42d35144183da44e67f675a98cd9bf5` — former Base shell/master rebuild;
- `b9eb4d530224cf8845ef06a0755ede54f95bd4b0` — Stitch V1 corpus and its retained visual screenshots;
- `84a0ad118f04519469db9cd1d283537cb6aca832`, `66ace5958a4686bba0659c7a99c7e0e258972494`, `7c19947727220f2e2b35e6e2cfc78d9a2592e17a`, and `2d0d300ebf2e921aaf896fd08b184df69d0a519e` — visual-authority, shell-consistency, V4-presentation and visual-reset candidates.

Findings:

- The retained `base2026-knowledge-stitch-v1` visual screenshots are coherent as a corpus, but visibly include Alex Personal service navigation and the personal commercial footer. They are explicitly rejected by the current Base2026-only requirement.
- The `1f65bfcde` Base2026 token/component package is useful only as a structural reference: it defines a dense research/product component grammar, spacing and responsive behavior. Its full shell is coupled to `ay-alex-v4-static` and warm/orange evidence tokens, so it is not an accepted source design.
- The startup overlay from `3a6cd166` successfully removed personal links but retained the same warm paper/navy/burnt-orange vocabulary (`#f7f4ee`, `#111820`, `#c84f07`) and mixed a Superdesign export into an independent shell. It is the immediate regression source, not the recovery target.

No compatible earlier complete design system exists to copy intact. Recoverable material is the **product discipline** of the former Base component system—dense search, readable evidence, restrained cards, clear controls—not its Alex-coupled visual or footer authority.

## `b26-independent-v1` contract

The candidate must use these shared semantic tokens and components everywhere:

- Palette: canvas `#F7F9FC`, surface `#FFFFFF`, ink `#0B1736`, muted `#526177`, line `#DDE5F0`, blue evidence accent `#315EEA`, hover `#254AC0`, dark CTA `#10213F`.
- Typography: Manrope for readable product copy and Geist Mono only for compact labels, data and code-like metadata. No personal-site type rules and no Tailwind utility classes as design authority.
- Layout: one `1160px` desktop content shell; `20px` mobile gutter; an explicit 4/8/12/16/24/32/48/72/96 spacing scale. A reading column may be narrower only where source text benefits; search and information architectures use the shared shell.
- Components: one sticky 72px desktop/64px mobile header, normal visible focus rings, compact solid/outline buttons, 10px control radius, 16px surface radius, contextual—not blanket—cards, and one responsive Base2026 footer. Full-pill controls are reserved for small filters/tags, not the default button/card shape.
- Data density: workspace filters, result cards, topic/creator cards and roadmap rows stay scannable and compact. No hero-card inflation, decorative browser dots, decorative vertical stripes, or decorative `01 / 02 / 03` section labels.
- Home: retain useful startup structure/copy but render shared shell/footer and convert the inherited roadmap presentation into a concise current-status/next-step component that links to the full Roadmap. The support panel becomes a regular dark CTA with no stripe.
- Brand isolation: reject `ay-`/Alex Personal classes, personal-service links, `aggressorbulkit.online`, `Get Free Snapshot`, `#c84f07`, `#d9730d`, and old personal footer copy from all candidate public HTML.

## Candidate plan and acceptance gates

1. Use the clean publication worktree at `de96c08f8f5e28f3ac0ce5236093b4f0b5c152e9` as the base for a new isolated candidate; preserve the canonical dirty checkout untouched.
2. Implement the shared B26 core/header/footer and generator/release-boundary normalization. Do not touch Worker routes, D1 bindings, form handlers, public datasets, canonical/robots/redirect rules or external-attribution URLs.
3. Build a fresh static candidate. Run Python release tests, Worker tests/typecheck, import dry-run, Wrangler dry-run, public-boundary/leak scans, internal-link/canonical/robots/sitemap/llms checks, search API smoke, Support/Partner write/readback, and representative source-link checks.
4. Capture before/after screenshots for the nine-route matrix at 1440px and 390px. Require one shared header/footer/component system, zero horizontal overflow, zero console errors, keyboard/focus validity and labelled forms.
5. Run a reviewer pass over the exact source diff and generated candidate. Only then may a separately authorized deployment/release decision be considered; rollback Worker versions remain `c5e88c7f-707b-4572-8d33-e369eecb2bb7` and `4389e513-c16a-4bcf-9f8c-b97ac55b7825`.

## Current blockers and next action

- No design-recovery source change has been made in this audit.
- GitHub CodeQL billing and legacy Pages API failures remain external and unrelated to the visual recovery.
- The local remote-tracking `origin/main` is stale at `03ac829a...`, while a read-only `git ls-remote` confirms the actual remote `main` and `codex/base2026-startup-publication-20260820` are both `de96c08f...`. This is a continuity note, not a reason to fetch, reset or alter refs.

Next safe action: create the isolated `b26-independent-v1` source candidate from the clean publication worktree, beginning with the shared core/header/footer and release-boundary injection. Deployment remains prohibited until the full fresh candidate and QA gates pass.
