# Agency design correction — published release

Checkpoint: 2026-09-06. The owner's correction supersedes the earlier claim
that the Source Laboratory release completed the design goal. HQ integrated the reviewed presentation change with the accepted private
runtime and published the frozen artifact. The product phase remains Phase 29.

## Implemented result

- Reused the approved ceramic b26 seal in the shared header, footer, favicon
  and layered homepage source engine. Brand derivatives have an explicit
  size/hash allowlist in the canonical builder.
- Added a finite GSAP source-card → lens → attributed excerpt → working-brief
  sequence with visible spatial travel, one illustrative caption, Pause,
  Resume and Replay, offscreen/hidden-tab pause and reduced-motion fallback.
  Native testing found a responsive cleanup bug; the final runtime preserves
  the last live progress after GSAP reverts, including a user pause.
- Rebuilt Blog discovery around the existing paginated public editorial API.
  It loads the complete corpus, derives categories, and supports search,
  empty/reset states, pagination, keyboard focus and browser history.
- Added Topics search, metadata-based grouping, source-count filters, sorting,
  pagination and shareable query state. Primary controls precede collections.
- Corrected internal panel padding, oversized headings, header/anchor offsets
  and decorative numbering. Preserved actual counts, versions and citations.
- Completed labelled social links and neutral directory references to the
  reviewed AlternativeTo, WebAppsDirectory, CitableHub and mcpservers.org
  listings. Founder LinkedIn is identified as the founder's profile.

## Source and frozen artifact

Branch: `codex/base2026-design-correction-20260906`, based on `36a16001f`
after PR64. The canonical builder produced
`output/agency-correction-20260906-v3` from the accepted prior public artifact
with the homepage template/stylesheet and explicit member-script retention.
No second production builder or private runtime source was introduced.

- Public artifact: 4,312 files, 106,395,772 bytes.
- Tree SHA256: `20e490a2b92a09553418bd99e8d8b727ba240e9bb1f4df99a996f1d7d5dd8420`.
- Member JS retained byte-exact:
  `28c5d3963e76140ad804994ed34248b4e3d3070c0878afd6f492e8b46a651ab2`.
- WordPress 0.1.1 ZIP retained byte-exact:
  `0909cd308c94b356b7831113891dac55e6039225a3c1f5c603730b0502c8eea4`.
- WordPress 0.1.0 ZIP retained byte-exact:
  `f588eddae0df5b91da4d70576b6cdec01d3a637b003ea076b9357cace6cb7e2a`.
- Narrow Worker presentation patch SHA256:
  `7a76d1bbcfa620af47dd5c0a0be1eed89883eecf6f30fa5f57fa92feaa3a7dc3`.

The Worker delta only updates projected-source favicon/cache references and
removes index-only Blog discovery enhancement from article shells. Applying
that patch to the accepted private integration checkout passed a read-only
`git apply --check`; Design did not apply it or edit that checkout.

## Verification

- 98 Python tests covering builder, homepage, editorial catalog/index, Topics
  and tools; 24 Node test-runner cases covering motion and discovery/tool
  runtimes; 172 Worker tests across four affected suites; TypeScript check.
- Design-authority check, canonical artifact gates, scoped diff check and
  Wrangler dry run with explicit v3 assets passed. Dry run is not deployment.
- Native in-app browser: 15 page families at 1440 and 390 px; final homepage
  captures at 1280 and 320 px. No horizontal overflow, duplicate page shell,
  missing H1 or browser warning/error in the recorded route pass.
- Blog: all 31 public articles across two API pages and eight actual
  categories; a second-page-only search result, category/empty/reset states,
  pagination and Back/Forward verified. Without JS the second cursor page
  still presents its four server-rendered articles.
- Topics: 80 existing records; search, source-count filtering, sorting,
  empty/reset states, pagination and Back/Forward verified.
- Actual hero frame sequences at multiple times, native pause/resume/replay,
  offscreen pause, reduced motion and paused 1440 → 390 → 1440 state verified.
  Headline/form stay visible; native menu Escape and article-anchor clearance
  pass. Public workspace search and homepage evidence-brief flows pass.

## Preview boundary and release verification

The preview adapter uses read-only public responses and candidate Worker
renderers. The projected-source fixture is explicitly illustrative. It does
not prove an authenticated member session or production D1 rendering.
Screenshots, API snapshots, release artifacts and the full review receipt are
kept outside public source in the existing Design office receipt location.

HQ applied only the reviewed presentation/test delta to the accepted private
runtime. The combined check passed 256 Worker tests, 27 member tests,
TypeScript and a scoped diff check. The deployed version is
`f200b4b7-87b6-4174-a87e-c0d6eea69947`, active at 100 percent. Its main-module
SHA256 is `c26cb6e3cf099e90a7cb5bbb8957524ca4fa5b55e61bb82780fe08833f106f33`
(2,283,609 bytes). Sixteen live public assets matched the reviewed artifact.
Existing bindings, auth flags, observability, member script and downloads
were preserved. Native production checks confirmed the actual b26 mark,
visible card travel, complete Blog discovery, live article/source rendering,
mobile panel and heading clearance, and an existing member session with its
saved collection intact. No member data was changed.

Continue the existing build, distribution, observation and improvement
cycle through the existing AgencyOS registry. Chief remains its sole writer;
the local office screen reads the same task and result records. The next
accepted media preproduction task covers Page Source Check. Preserve the
new visual contract and current private-runtime integration for future releases.
