# Base2026 Non-Publication Growth Pack — 2026-08-29 (local-only)

## Scope and operating status

This is a local preparation pack for a future, owner-authorized distribution
pass. It consolidates copy, metadata, link rules, and assets for DEV,
Hashnode, Hacker News, Reddit, Indie Hackers, and Product Hunt.

No account was created, no login was performed, and no draft, post, upload,
submission, contact, or publication was made for this pack. The copy below is
material to review and adapt later, not a record of an external action.

The public product and dataset are source-first and read-only. The practical
growth unit is one useful technical or product conversation at a time, with a
single relevant canonical link. Do not turn this pack into a multi-platform
link blast, a vote campaign, or a claim about traction.

## Decision first: Hugging Face and Zenodo

### HOLD — free Hugging Face or Zenodo distribution

The current repository evidence is not sufficient to publish the public
dataset to a free Hugging Face or Zenodo record. The code and documentation
are Apache-2.0, but the repository explicitly says that this does not grant
rights to third-party creator videos, platform captions, or referenced source
content. A privacy-safe reviewed excerpt is not automatically redistributable
under a dataset license.

The hold is about rights and release mechanics, not whether the product is
useful or whether the current public web surface is free to read.

| Required for a defensible dataset mirror | Repository evidence checked 2026-08-29 | Result |
| --- | --- | --- |
| A dataset-level license with scope and terms | LICENSE limits Apache-2.0 to repository code and documentation; the catalog, manifest, and data dictionary have no dataset-level SPDX license or license URL | Missing |
| A rights basis for each included record or an explicit metadata-only scope | Current public records preserve creator/source attribution, original URLs, dates, policy flags, and reviewed/public flags, but do not carry license, rights, or reuse-basis fields | Missing |
| Explicit provenance sufficient to reproduce and audit a record | Source IDs/URLs, creator handles/URLs, publication/capture dates, policy flags, and review state provide partial operational provenance; there is no explicit per-record provenance object covering retrieval, snapshot, transformation, and evidence | Partial |
| A stable, complete, versioned data payload | The checked public release receipt describes a reviewed static snapshot and exact artifact checks; the GitHub release surface is catalog/metadata-oriented while generated JSONL bodies are runtime/deployment artifacts excluded from Git publication | Not yet a mirror package |
| Corrections and removals compatible with the host | Source policy and opt-out paths exist, but they do not by themselves establish how an immutable Zenodo version or a cached Hugging Face revision would be corrected, withdrawn, or superseded | Incomplete |
| Owner authorization to create accounts and upload | No account or upload authority was exercised in this task | Not granted |

### Release evidence audit

The static v3 release evidence makes the missing fields concrete. This is a
dated release audit, not a growth metric, and it must not be confused with the
live D1 totals:

| Checked surface | Snapshot entries | Explicit license / rights / provenance key |
| --- | ---: | --- |
| `documents.jsonl` | 1,525 | None on all audited rows |
| `passages.jsonl` | 2,319 | None on all audited rows |
| `insight_cards.jsonl` | 1,939 | None on all audited rows |
| `topic_signal_briefs.jsonl` | 28 | No dataset-level rights/provenance declaration |
| `manifest.json` and the checked-in catalog | Manifest and distributions describe scope, boundary, and URLs | No dataset-level license, rights, or provenance declaration |

The rows do retain useful operational fields such as source ID, source URL,
creator handle/URL where available, publication or capture date, policy flags,
review/public state, and bounded public text. Those fields support attribution
and review; they do not supply a reuse license or a complete provenance record.

The static v3 manifest is useful release evidence: it is excerpt-only,
excludes full transcripts, and separates public reviewed cards from excluded
private or review-held material. Its recorded snapshot counts are release
facts, not growth metrics, and must not be mixed with the live D1 totals. Those
privacy and review controls still do not answer who licenses a creator's
source text or whether a third party may mirror it.

### GO gate for a later HF/Zenodo pass

Do not replace this HOLD with an inferred CC-BY, CC0, ODC, or Apache license.
The owner must first choose and document the rights model. A later GO
requires all of the following:

1. An owner/legal decision that states the scope of the dataset license and
   separates Base2026-authored transformations from third-party source
   material.
2. Either a deliberately metadata/pointer-only export, with a fresh
   public-release audit, or a reviewed export whose included text has an
   explicit per-record reuse basis. A metadata-only choice is not an
   automatic GO; it still needs a schema and rights audit.
3. Dataset-level and per-record fields for the applicable license or rights
   basis, source-content reuse limit, provenance, retrieval/snapshot
   identifier, transformation method, and correction/takedown state. The
   original source URL, creator attribution, and publication date remain
   required.
4. A complete versioned payload, manifest, checksums, and a written policy for
   corrections, takedowns, replacement versions, and immutable archived
   versions.
5. A new public/private publication audit confirming that no raw media,
   captions, ASR, full private transcripts, review packets, credentials,
   logs, local database files, or release archives are included.
6. Explicit owner authorization for the account, upload, metadata submission,
   and receipt capture. This pack does not provide that authorization.

Until that gate is complete, the canonical public dataset page and API remain
the distribution surface:

- Dataset: https://base2026.dev/dataset
- Manifest: https://base2026.dev/static/manifest.json
- Quickstart: https://github.com/offflinerpsy/base2026/blob/main/docs/PUBLIC_DATASET_QUICKSTART.md

## Verified canonical source set

Use stable direct links and no tracking parameters or URL shorteners. Recheck
the live source immediately before any future external action.

| Surface | Canonical URL | Use |
| --- | --- | --- |
| Product | https://base2026.dev/ | Primary tryable product link |
| Dataset | https://base2026.dev/dataset | Public dataset boundary and entry point |
| Journal | https://base2026.dev/journal/source-backed-video-search-cloudflare/ | Build story and technical source article |
| Workspace | https://base2026.dev/workspace/ | Search/workspace surface when a direct product view is useful |
| Quickstart | https://github.com/offflinerpsy/base2026/blob/main/docs/PUBLIC_DATASET_QUICKSTART.md | Public dataset setup and query examples |
| API index | https://base2026.dev/api-index.json | API and machine-readable entry point |
| Data dictionary | https://base2026.dev/data-dictionary.json | Field definitions |
| Manifest | https://base2026.dev/static/manifest.json | Static snapshot metadata |
| Repository | https://github.com/offflinerpsy/base2026 | Code, docs, issues, and public project history |
| GitHub release | https://github.com/offflinerpsy/base2026/releases/tag/public-data-v2026.08.29 | Release receipt and catalog context |
| Source policy | https://base2026.dev/source-policy | Attribution, correction, and removal policy |
| Opt out | https://base2026.dev/opt-out | Creator removal request path |

Do not use historical legacy `/knowledge` links in new copy.

## Truthful shared copy

These statements are supportable from the current README, public source
policy, quickstart, and journal. Keep the copy qualitative unless a specific
dated source is linked and the number is labeled as a static snapshot or live
runtime total.

### One-line description

> Base2026 is an open-source video research engine and source-first evidence
> library for short-form expert video.

### Short product description

> Base2026 turns reviewed public short-form videos into attributed, searchable
> evidence that people and AI systems can inspect, compare, and trace to the
> original source. The public layer is read-only and keeps raw media, raw
> captions, ASR, and private transcripts out of the release.

### Technical build paragraph

> I built Base2026 around a narrow question: what did practitioners actually
> say about SEO, GEO, AEO, and AI search? The public layer keeps creator
> attribution, bounded reviewed excerpts, topic context, and the original
> source link visible. Public search is read-only; raw media, raw captions,
> ASR, full private transcripts, and review packets stay out of the public
> release. The project includes a public JSONL/API surface so someone can
> inspect the data contract instead of taking a launch claim on faith.

### Copy guardrails

- Do not claim users, revenue, rankings, traffic, coverage, conversion,
  adoption, or backlinks without a current source and a dated definition.
- Do not describe the dataset as CC-BY, CC0, ODC, Apache-2.0, or
  “open-licensed” until the rights gate above is actually closed.
- Say “reviewed public excerpts/cards” rather than “full transcripts” or
  “complete video archive.”
- Preserve creator attribution and the original source link in any derivative
  explanation.
- Do not imply affiliation with TikTok, Cloudflare, Google, OpenAI, or any
  creator whose public source appears in the research.
- Any copy assisted by an AI system must receive human review. Hacker News
  requires the final submission/comment text to be human-written rather than
  generated or AI-edited.

## Channel execution packs

Every channel below remains HOLD for external action in this task. The
“ready” material means locally reviewable copy and metadata only.

### DEV

**Use case:** A substantive technical article or a materially adapted version
of the existing build journal. Do not publish a title-only link drop.

**Proposed metadata**

- Title: `How I Built Source-Backed Expert-Video Search on Cloudflare`
- Description: `A practical build note on turning public short-form expert video into attributable, searchable evidence while keeping raw media and private transcripts out of the public release.`
- Tags: `cloudflare`, `opensource`, `webdev`, `ai`
- Canonical source: `https://base2026.dev/journal/source-backed-video-search-cloudflare/`

If reposting or adapting the existing journal, the local text package can use:

```yaml
---
title: How I Built Source-Backed Expert-Video Search on Cloudflare
published: false
description: A practical build note on turning public short-form expert video into attributable, searchable evidence while keeping raw media and private transcripts out of the public release.
tags: cloudflare, opensource, webdev, ai
canonical_url: https://base2026.dev/journal/source-backed-video-search-cloudflare/
---
```

Use DEV’s native canonical setting or `canonical_url` front matter when
cross-posting. The canonical must point to the Base2026 journal only when the
DEV post is a repost/adaptation of that article; decide separately if the
piece becomes materially original. Link once, in context, to the dataset or
repository. Manually review the final article and any AI-assistance
disclosure before a future owner-authorized publication.

Official reference: [DEV writing, editing, and scheduling
help](https://dev.to/help/writing-editing-scheduling).

### Hashnode

**Use case:** A native adapted article for developer readers, not a raw link
drop or duplicate campaign.

**Proposed metadata**

- Title: `How I Built Source-Backed Expert-Video Search on Cloudflare`
- Subtitle: `What the public/private boundary looks like in a small evidence product.`
- Tags: `Cloudflare`, `Open Source`, `AI`, `SEO`
- Original URL/canonical: `https://base2026.dev/journal/source-backed-video-search-cloudflare/`

Paste the article as a native post and use Hashnode’s **Add Original URL**
field for the canonical when the post is a repost/adaptation. Link once to
the dataset and, if needed, once to the repository. Do not make the product
page, dataset, and journal compete as three equal calls to action.

Official reference: [Hashnode editor: writing a blog
post](https://docs.hashnode.com/blogs/editor/writing-a-blog-post). Recheck
the current editor and publication rules before action.

### Hacker News / Show HN

**Preferred mode:** Show HN only after confirming that the live product is
tryable without an account and that the submission is about something people
can actually use. Show HN is not the place for a blog post, signup page,
newsletter, list, or fundraiser.

**Proposed Show HN submission**

- Title: `Show HN: I built a source-backed search engine for expert short-form video`
- URL: `https://base2026.dev/`
- First-comment seed:

> I built Base2026 to answer a narrower research question: what did
> practitioners actually say about SEO, GEO, AEO, and AI search? The public
> product is read-only and searchable without an account. It keeps creator
> attribution, bounded evidence, and the original source link visible; raw
> media, raw captions, and private transcripts stay out of the release. I’m
> especially interested in whether the search result and evidence trail are
> clear enough to inspect and challenge.

The final title should omit the site name, and the final comment must be
rewritten and posted by a human. Do not ask for upvotes, comments, or traffic.
Do not submit both a Show HN product URL and a journal URL in the same cycle.
If the product is not demonstrably tryable, the fallback is one ordinary
submission of the original technical article, not a disguised Show HN.

Official references: [Hacker News guidelines](https://news.ycombinator.com/newsguidelines.html)
and [Show HN guidelines](https://news.ycombinator.com/showhn.html).

### Reddit

**Mode:** Choose one genuinely relevant subreddit only after reading its
sidebar and current rules. Ask the moderators when the community fit or link
policy is unclear. Make the post native to that community and disclose the
author relationship. Never use a link-only post, repeated cross-posts, vote
requests, DMs, automation, or a workaround for a no-link rule.

**Reddit-native draft**

> I built a small public evidence library for short-form expert video.
>
> I wanted a way to search what practitioners said about SEO and AI search
> while keeping the original source and context visible. The public layer is
> read-only and uses reviewed excerpts/cards; it does not publish raw media or
> private transcripts.
>
> I’m looking for critique on the evidence trail: is it clear why a result is
> included and how to verify it?
>
> Dataset: https://base2026.dev/dataset

Use a build-oriented version for a technical community and a data-oriented
version for a research/data community; do not paste the same copy everywhere.
If the target community bans self-promotion or external links, stop rather
than hiding the link or moving the promotion into comments.

Official references: [Reddit’s self-promotion
guidance](https://www.reddit.com/wiki/selfpromotion) (an older, explicitly
non-updated wiki) and [Reddit Pro’s organic
playbook](https://redditinc.com/hubfs/Reddit%20Inc/Content/Reddit%20Pros%20organic%20playbook.pdf).
The target subreddit’s current rules take precedence.

### Indie Hackers

**Mode:** A founder/build conversation with useful context and one direct
product link. Choose the current category or community space at the time of
action; do not assume an old flair or group is still available.

**Proposed title**

`I built a public evidence library for short-form expert video — what should I improve?`

**Proposed body**

> I kept running into a simple research problem: short-form expert advice is
> easy to watch and hard to search, compare, and cite. I built Base2026 as a
> small public, read-only evidence layer for SEO, GEO, AEO, and AI-search
> research. It keeps the creator/source link and bounded reviewed evidence
> visible, and keeps raw media, raw captions, and private transcripts out of
> the public release.
>
> I’m looking for feedback from founders and developers on the retrieval
> experience and data contract. Try it here: https://base2026.dev/

Disclose that you built the product. Avoid revenue, user, or traction claims,
press-release language, and duplicated Reddit copy. If the current community
requires a different format or prohibits this kind of post, stop and follow
its rule.

Reference: [Indie Hackers community-based
marketing guide](https://www.indiehackers.com/post/guide-how-to-do-community-based-marketing-ee5c766673).

### Product Hunt

**Mode:** A self-hunt from a personal maker account only. A company account,
paid hunter/promoter, upvote request, contest reward, or automated campaign is
out of scope.

**Proposed listing metadata**

- Name: `Base2026`
- Tagline: `Search source-backed expert video for SEO and AI research`
- Description (within Product Hunt’s 260-character field):
  `Base2026 is a free, read-only research engine for short-form expert video. Search reviewed, attributed evidence for SEO, GEO, AEO, and AI-search work, then trace each result to its original source.`
- Topics: `Search`, `AI`, `Engineering & Development`, `Marketing & Sales`
- Pricing: `Free`
- Status: `Live`
- Maker: `Alex Yarosh`
- Primary URL: `https://base2026.dev/`

**Proposed first comment**

> I built Base2026 because short-form expert knowledge is easy to watch and
> hard to search, compare, and cite. The public product keeps attribution,
> bounded reviewed evidence, and original source links visible. It is free to
> use, read-only, and available without an account. I’d value feedback on
> where the evidence trail is clear—and where it still needs work.

Use the direct product URL as the primary URL. The dataset and journal can be
secondary context only; the journal must not replace the product as the
listing target. Product Hunt’s recommended image sizes are an asset
requirement, not a reason to reuse uncleared local screenshots:

- One square thumbnail, preferably 240 x 240 or larger at the same ratio.
- At least two clean gallery images, preferably 1270 x 760 or larger.
- An optional full YouTube demo URL only if the video is actually public and
  safe to link.
- Maker identity and a personal account that is eligible to post.

No approved Product Hunt thumbnail, gallery set, or public demo asset is
recorded by this pack. Do not upload or create a Product Hunt draft until the
owner supplies those assets and authorizes the action.

Official references: [Product Hunt: post a
product](https://help.producthunt.com/en/articles/479557-how-to-post-a-product),
[before you launch](https://www.producthunt.com/launch/before-launch), and
[sharing your launch](https://www.producthunt.com/launch/sharing-your-launch).

## Platform-specific canonical and link rules

| Channel | Canonical/link rule | Stop condition |
| --- | --- | --- |
| DEV | Use native canonical or `canonical_url` to the Base2026 journal for a repost/adaptation. | The article is materially different and no owner decision sets its canonical. |
| Hashnode | Use the native **Add Original URL** field for a repost/adaptation of the journal. | The current editor or canonical behavior is unclear. |
| Hacker News | Submit the direct original URL; Show HN uses the tryable product, not the journal. Omit the site name from the title. | No-signup tryability or the human-written comment requirement cannot be verified. |
| Reddit | No global canonical assumption. Use one stable direct link permitted by the target subreddit and disclose affiliation. | The subreddit disallows links/self-promotion or the community fit is weak. |
| Indie Hackers | Use a native founder/build post with one contextual direct product link. Do not assume an old flair or canonical feature. | Current category, format, or self-promotion rule is unclear. |
| Product Hunt | Primary URL is the direct product. Dataset/journal links are secondary context only. | Personal maker eligibility or launch assets are missing. |

Do not add UTM parameters, affiliate parameters, link shorteners, or hidden
redirects. A future receipt should record the exact external URL, target
canonical (if any), publication timestamp, and the source link used.

## Asset checklist

### Ready for local preparation

- Current direct product, dataset, journal, repository, dictionary, manifest,
  source-policy, and opt-out URLs listed above.
- The README’s product description and the public/private boundary.
- The public dataset quickstart and catalog for explaining machine-readable
  access.
- The technical journal and its existing canonical source.
- A public, read-only product surface that can be rechecked before a future
  Show HN or Product Hunt action.
- Human review capacity for every final article, comment, or launch field.

### Missing or HOLD

- A current personal maker/account identity for each external platform.
- Fresh Product Hunt thumbnail, gallery images, and optional public demo.
- Channel-specific final screenshots or screen recordings that have been
  cleared for public reuse.
- A verified target subreddit, Indie Hackers category/community, or current
  moderation decision.
- A live check that the product remains easy to try without an account.
- Dataset-level and per-record rights/license/provenance metadata for any
  Hugging Face or Zenodo mirror.
- A complete versioned HF/Zenodo payload, checksums, correction/takedown
  procedure, and owner upload authorization.

### Never put into a public growth asset

- Raw media, raw captions, ASR, full private transcripts, review packets,
  private notes, credentials, logs, local database files, generated release
  archives, or unreviewed raw captions.
- Local filesystem paths or ignored output directories.
- A copied source excerpt whose reuse basis has not been established.
- Private pipeline counters, account identifiers, or owner-only operational
  details.

## Future local execution sequence

When the owner explicitly opens a channel, use this bounded sequence:

1. Recheck the live Base2026 target URL, current source policy, and the
   platform’s current rules. Select one target surface and one audience.
2. Choose one pack above and manually adapt it to the community. Remove any
   claim that cannot be sourced today.
3. For DEV or Hashnode, set canonical metadata before the article is sent
   anywhere. For HN, rewrite the final text as a human. For Reddit or Indie
   Hackers, make the post native and disclose authorship. For Product Hunt,
   verify the maker account and all image/video assets.
4. Obtain the separate owner authorization required for the external action.
   This document itself is not authorization.
5. After an authorized publication, capture a receipt containing the exact
   URL, timestamp, title, canonical outcome where applicable, target link,
   and any correction/takedown route. Do not immediately duplicate the same
   copy on another platform.
6. Observe useful responses and referral/discovery evidence before deciding
   whether another channel is warranted. Do not convert an absence of
   observed traffic into a negative product claim.

## Local evidence and source notes

The rights decision above is grounded in these checked-in project sources:

- [README](../../README.md)
- [LICENSE](../../LICENSE)
- [Public dataset quickstart](../PUBLIC_DATASET_QUICKSTART.md)
- [Public dataset catalog](../../examples/base2026-public-dataset-catalog.json)
- [Public JSONL schema](../schemas/PUBLIC_JSONL_SCHEMA.md)
- [Source and content policy](../public-pages/04_SOURCE_AND_CONTENT_POLICY.md)
- [Publication boundary](PUBLICATION_BOUNDARY.md)
- [Public dataset growth release receipt](BASE2026_PUBLIC_DATASET_GROWTH_RELEASE_2026_08_29.md)
- [Editorial syndication receipt](BASE2026_EDITORIAL_SYNDICATION_RECEIPT_2026_08_29.md)
- [SEO/GEO growth map](BASE2026_SEO_GEO_GROWTH_MAP_2026_08_28.md)

These files establish the current boundary and public routes. They do not
grant new account, upload, publication, legal, or platform-moderation
authority.

## Final status

- Non-publication growth pack: **READY for local review only**.
- DEV, Hashnode, Hacker News, Reddit, Indie Hackers, Product Hunt:
  **HOLD for external action** until the owner opens a channel and completes
  its current rule/asset checks.
- Hugging Face and Zenodo: **HOLD** until the dataset rights/license,
  provenance, versioning, and upload-authorization gates are closed.
- External publication, login, upload, registration, submission, contact,
  deployment, commit, and push: **not performed**.

Suggested future commit message (not executed):
`docs: add non-publication growth pack and distribution hold`
