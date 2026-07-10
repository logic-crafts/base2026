# Base2026 Redesign Content Packet

Updated: 2026-07-10
Status: content contract ready; final corpus counts pending completion of the active content freeze
Owner: Alex Yarosh / Logic Crafts LLC

## 1. What this packet is

This is the real-content contract for redesigning Base2026 alongside Alex Personal Page.

It is not a request to restyle the current orange/navy prototype. It defines the content, product states, page types, and reusable components that the new design must support.

## 2. Product relationship

Alex Personal Page and Base2026 belong to one visual family but have different jobs.

### Alex Personal Page

- establishes author identity and trust;
- explains Alex's point of view, work, products, and context;
- is narrative and personality-led;
- can introduce Base2026 and send qualified readers into it.

### Base2026

- turns source intelligence into evidence-backed practical decisions;
- is utility-led rather than biography-led;
- must show provenance, uncertainty, risks, and measurement;
- must never look like a bulk transcript archive.

### What may be shared

- typography families and scale;
- color foundations and semantic tokens;
- grid and spacing system;
- button, link, form, tag, and status primitives;
- header/footer family and responsive principles;
- motion and accessibility rules.

### What must remain distinct

- information architecture;
- page density;
- product navigation;
- evidence/provenance components;
- solution verdict, playbook, risk, and measurement components;
- source/indexability states.

Do not copy the Alex Personal Page body layout into Base2026.

## 3. Product chain

`Source Intelligence → AI Recommends Solution → Apply → Measure`

The redesign must make this chain visible without exposing internal pipeline mechanics.

## 4. Required page types

### A. Base2026 home / discovery

Purpose: explain the product and let users find problems, solutions, topics, and sources.

Required content slots:

- concise product promise;
- problem/intent search;
- featured solution paths;
- topical discovery;
- recent high-confidence source intelligence;
- explanation of evidence and verification standards;
- relationship to Alex Yarosh / Logic Crafts LLC.

### B. AI Recommends Solutions hub

Purpose: small problem-led portfolio, not an inventory dump.

Required content slots:

- problem-led title and explanation;
- solution cards with problem, verdict, expected outcome, evidence depth, and status;
- filtering by problem/intent, not by creator;
- explicit distinction between ready solutions and future backlog.

### C. AI Recommends Solution detail

This is the first reusable component/page contract for the shared redesign.

Required slots:

1. Problem statement.
2. `AI Recommends` verdict.
3. Expected outcome.
4. Why this recommendation is justified.
5. Evidence and provenance.
6. Risk, caveats, and stop conditions.
7. Step-by-step playbook.
8. Measurement plan.
9. Authoritative references for factual claims.
10. Related source intelligence.
11. Related solutions or next decision.
12. Indexability/status metadata for the publishing system.

The design must make verdict, action, risk, evidence, and measurement scannable without flattening everything into identical cards.

### D. Source intelligence page

Purpose: provenance and context for one source, not automatic SEO inventory.

Required slots:

- source/creator attribution and original URL;
- exact evidence excerpt;
- reviewed insight cards, if any;
- relationship to a solution or future cluster;
- clear evidence limitations;
- authoritative verification links when factual claims require them;
- source state and indexability state.

A transcript must not become the visual hero. Raw transcript access, if retained, is secondary/private provenance.

### E. Topic / problem page

Purpose: cluster evidence and solutions around a user problem.

Required slots:

- problem definition;
- recommended solution(s);
- useful reviewed source intelligence;
- missing-evidence notice where confidence is not yet sufficient;
- related topics without thin tag-page duplication.

### F. Search / empty / held states

The design must include:

- no result;
- useful source but no solution yet;
- source-only / reviewed-no-card;
- future-cluster backlog;
- private source-review hold;
- duplicate/superseded evidence;
- local-ready but awaiting redesign release.

These are product states, not error screens.

## 5. Real solution set for design work

Use the five approved pilot solutions, not lorem ipsum:

1. Google Business Profile Visibility Audit.
2. Search Console: High Impressions, Low CTR.
3. Measure AI Search Visibility.
4. Answer-Ready Service Page Checklist.
5. Content Refresh Prioritization.

Local routes:

- `/knowledge/solutions/`
- `/knowledge/solutions/google-business-profile-visibility-audit.html`
- `/knowledge/solutions/search-console-high-impressions-low-ctr.html`
- `/knowledge/solutions/measure-ai-search-visibility.html`
- `/knowledge/solutions/answer-ready-service-page-checklist.html`
- `/knowledge/solutions/content-refresh-prioritization.html`

## 6. Edge cases the design must survive

The designer/developer must test with real examples of:

- a solution with multiple creator sources plus authoritative references;
- creator advice that is useful only as a risk/counterexample;
- a source with an approved insight but no immediate solution page;
- a useful future-cluster item;
- a duplicate/self-promotional source that produces no card;
- a source with incomplete captions and private provenance only;
- a locally approved card intentionally not deployed into the old shell;
- a long evidence excerpt;
- zero evidence strong enough for an indexable page.

## 7. Content/state contract

| State | Public page | Indexability | Redesign behavior |
|---|---:|---|---|
| Approved solution | Yes, after release approval | `index,follow` only after all gates | Full solution detail |
| Approved source intelligence | Yes when it adds unique value | Conditional | Source page linked to a solution/topic |
| Local-ready / redesign release | Local only | Not deployed yet | Preserve for migration |
| Future cluster backlog | Usually no standalone page | No | Show only in internal/backlog UI unless product-approved |
| Reviewed no-card / source-only | Provenance only if needed | `noindex,follow` or private | No empty insight shell |
| Source review hold | No | Private | Never leak into public UI |
| Duplicate/superseded | No new page | No | Point internally to canonical source |

`index,follow` is earned, not default.

## 8. Data and code contracts

Frontend must consume these contracts rather than parse old HTML:

- `contracts/base2026.ai-recommends-solution.schema.json`
- `data/base2026_ai_recommends_solutions_pilot.json`
- `docs/BASE2026_AI_RECOMMENDS_SOLUTIONS.md`
- `scripts/base2026_ai_recommends_core.py`
- `scripts/generate-ai-recommends-solutions.py`
- `scripts/validate-ai-recommends-solutions.py`
- `scripts/validate-ai-recommends-html.py`

The current HTML/CSS is a disposable local prototype. The schema, evidence relationships, decisions, playbook, measurement, and indexability rules are the durable layer.

## 9. Component acceptance criteria

A redesign is accepted only if:

- all five real pilot records render without content loss;
- verdict, evidence, risk, playbook, and measurement remain distinguishable;
- long and short evidence cases work on desktop and mobile;
- source-only/no-card states do not create fake content;
- authoritative references are visually distinct from creator evidence;
- page hierarchy works without decorative numbering or generic card walls;
- keyboard focus, contrast, readable measure, and responsive wrapping pass QA;
- canonical/robots/schema behavior remains driven by data, not manually embedded per page;
- the shared Alex/Base visual family does not erase Base2026's utility/evidence identity.

## 10. Freeze boundary

Frozen before redesign implementation:

- page types;
- solution schema and required slots;
- evidence/provenance relationship;
- verdict/risk/playbook/measurement contract;
- source and indexability states;
- five real solution fixtures;
- explicit terminal outcomes for current pipeline backlog.

Not frozen:

- current orange/navy styling;
- current HTML structure beyond semantic requirements;
- component composition, art direction, imagery, interaction, motion, and responsive layout;
- final shared design tokens from the Alex Personal Page redesign.

## 11. Handoff timing

The current Content Freeze is closed and verified. The redesign may now begin against this packet, the solution schema, and the five pilot payloads.

New future source intake does not reopen this freeze automatically. It enters the ongoing ingestion/editorial pipeline and must not change the frozen semantic/data contracts without an explicit contract revision.
