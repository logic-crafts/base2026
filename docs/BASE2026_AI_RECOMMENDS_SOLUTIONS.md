# Base2026 AI Recommends Solutions — Product and Page Contract

Status: local implementation contract
Updated: 2026-07-10
Owner: Alex Yarosh / Logic Crafts LLC
Release boundary: no live publication or indexation without explicit approval

## 1. Product promise

Base2026 converts fragmented short-form expert signals into evidence-backed operating guidance.

The product is not a transcript archive, an AI-content farm, or a marketing agency. It is an independent source-intelligence and decision-support system:

> Search the evidence, understand the competing signals, apply a practical recommendation, and measure the result.

## 2. Primary user and job-to-be-done

Primary users:

- owner-operators and marketing leads at small/local service businesses;
- in-house SEO/content operators who need a defensible next action;
- analysts and AI agents that need structured, attributable evidence;
- researchers comparing public expert recommendations.

Primary job:

> “I have a specific growth/visibility problem. Show me what credible public signals say, separate claims from verified facts, recommend a bounded action, and tell me how to know whether it worked.”

## 3. Public content architecture

### Layer A — Source Intelligence

Purpose: proof and attribution.

A Source Intelligence page contains source identity, reviewed excerpt/passage, source-specific claims, topics, and the original-source link. It may contribute evidence to a Solution page even when the source page itself remains `noindex,follow`.

A source page is indexable only when it has independent value: public evidence, at least one reviewed public insight, useful topic assignment, summary, attribution URL, and no full private transcript exposure.

### Layer B — Topic Evidence

Purpose: exploration and comparison.

A Topic Evidence page groups public insight cards and creator viewpoints. It helps a researcher inspect the corpus but is not automatically a complete recommendation.

### Layer C — AI Recommends Solution

Purpose: decision and action.

This is the primary indexable growth/product layer. A Solution page answers one explicit problem or intent and synthesizes several reviewed signals into a Base2026 recommendation, playbook, reusable asset, and measurement plan.

### Layer D — Apply and Measure

Purpose: product activation.

The CTA must keep the user inside the Base2026 product journey:

1. inspect linked evidence;
2. copy/use the checklist, worksheet, or decision table;
3. apply the playbook;
4. record a baseline and outcome;
5. optionally contribute a correction, result, or new source.

A site-level service CTA may remain in the inherited global shell, but Solution-page primary CTAs must not present Base2026 as an agency or service package.

## 4. Green Solution page contract

Every `index,follow` AI Recommends Solution page must include all required fields.

### Intent and decision

- `audience`: who is making the decision;
- `problem`: the concrete problem;
- `primary_query`: the main search/answer intent;
- `recommendation`: concise Base2026 verdict;
- `decision_scope`: what the recommendation covers and does not cover;
- `why_now`: why the problem deserves attention now.

### Evidence

- at least two distinct reviewed source signals by default;
- at least two distinct creator/source identities where the corpus supports it;
- exact internal Source Intelligence links;
- a visible distinction between **creator claim**, **Base2026 synthesis**, and **authoritative external fact**;
- authoritative external citation for platform/product behavior, eligibility, policy, or ranking claims;
- disagreements, uncertainty, or evidence limits disclosed rather than averaged away.

A single-source Solution is allowed only when the source is authoritative and the page supplies substantial independent utility. It must still pass manual review.

### Independent utility

- step-by-step implementation playbook;
- reusable asset: checklist, decision table, template, worksheet, or measurement rubric;
- “when not to use” / risks section;
- baseline and KPIs;
- verification cadence;
- related Source Intelligence links;
- related Solution links where available.

### Technical quality

- unique title, meta description, H1, canonical and stable slug;
- valid `Article` or `HowTo` schema without unsupported claims;
- accessible heading hierarchy and link labels;
- no private captions, raw ASR, review notes, prompt text, or candidate-only claims;
- internal links resolve inside the local artifact;
- mobile and desktop visual QA pass;
- deterministic output from a reviewed data artifact;
- no direct model-to-publication path.

## 5. Indexability rubric

A page is `index,follow` only when every hard gate is green.

| Gate | Green requirement |
|---|---|
| Intent | One clear problem, audience and primary query |
| Evidence | 2+ reviewed source signals; authoritative citation where needed |
| Synthesis | Base2026 recommendation is more useful than a source recap |
| Action | Executable playbook with ordered steps |
| Reusable value | Checklist/template/table/rubric present |
| Measurement | Baseline, KPI and cadence present |
| Risk | Limits and when-not-to-use present |
| Provenance | Source links and evidence roles visible |
| Technical | Title/meta/H1/canonical/schema/internal links valid |
| Visual | Desktop/mobile QA approved |
| Editorial | Human/Sol review recorded; no unsupported external claim |

If any hard gate fails, the generated page remains `noindex,follow` and is excluded from the release sitemap.

## 6. Pilot portfolio selected from the current corpus

The following five pilots were selected because the public corpus already contains multiple reviewed signals and a clear user decision. Counts are a 2026-07-10 keyword-cluster snapshot, not unique factual endorsements.

### 1. Google Business Profile visibility audit for Maps and AI answers

- corpus footprint: 142 public cards / 137 sources;
- audience: local business owner or local SEO operator;
- intent: audit and improve GBP completeness and visibility inputs;
- asset: field-by-field audit worksheet;
- authoritative verification required for Google product behavior and category/eligibility claims.

### 2. High-impression, low-CTR Search Console action plan

- corpus footprint: 38 public cards / 37 sources;
- audience: SEO/content operator;
- intent: identify pages with visibility but weak clicks and choose the next action;
- asset: decision table covering title/snippet, intent coverage, internal links, and measurement;
- avoid claiming causality from CTR alone.

### 3. AI search visibility measurement with GA4 and Search Console

- corpus footprint: 60 public cards / 58 sources;
- audience: marketing analyst or owner measuring AI referrals/visibility;
- intent: build a bounded measurement baseline;
- asset: measurement worksheet and channel/source classification table;
- platform-specific reports must be verified against current official documentation.

### 4. Answer-ready service page checklist

- corpus footprint: 50 public cards / 40 sources;
- audience: local service business or content operator;
- intent: make a service page clearer, evidence-rich and easier to cite/understand;
- asset: section-level page checklist and before/after QA rubric;
- avoid promising rankings or AI citations.

### 5. Content refresh prioritization playbook

- corpus footprint: 14 public cards / 13 sources;
- audience: site owner with an existing content library;
- intent: decide what to refresh, consolidate, keep, or retire;
- asset: opportunity scorecard using current performance, business value and evidence freshness;
- avoid unsupported claims that changing dates alone improves rankings.

## 7. Backlog outcome taxonomy

“Backlog complete” does not mean every source receives a public card. Every canonical source must end in one of these states:

- `solution_cluster_contributor` — useful evidence for one or more Solution pages;
- `source_intelligence_public` — useful source-specific card, not necessarily a Solution input;
- `reviewed_no_card` — reviewed but no durable public insight worth publishing;
- `needs_source_review` — evidence/transcript quality insufficient;
- `cold_hold` — no usable local evidence;
- `duplicate_or_superseded` — redundant signal retained only for provenance.

The primary business metric is not cards created. It is:

`reviewed sources → green solution-cluster contributors → verified Solution pages → approved indexable pages → measured user actions/outcomes`.

## 8. Release success metrics

Pilot-level:

- 5/5 pages have stable intent and complete required fields;
- 0 unsupported platform/policy claims;
- 100% evidence/internal links resolve;
- 100% reusable assets are actionable without contacting an agency;
- 100% robots decisions explainable by the rubric;
- desktop and mobile QA pass.

Portfolio-level after release approval:

- organic impressions and qualified clicks by Solution intent;
- visits from Solution → evidence and Solution → Apply/Measure;
- checklist/worksheet engagement where measurable with privacy-safe analytics;
- return visits and internal search refinements;
- corrections/evidence contributions;
- pages kept, improved, merged, noindexed or retired based on outcome — not page count.
