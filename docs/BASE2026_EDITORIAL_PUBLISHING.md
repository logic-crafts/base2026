# Base2026 editorial publishing — operating contract

Status: live runtime and first exact publication/replay verified 2026-08-30.
Production proof: [release receipt](project-memory/BASE2026_EDITORIAL_RUNTIME_RELEASE_2026_08_30.md).
This governs the shared original-article and maintained-guide publisher.
[Evidence-to-SEO operating manual](BASE2026_EVIDENCE_TO_SEO_OPERATING_MANUAL.md)
adds the guide dependency and canonical rules. The Cloudflare pipeline manual
still governs raw-video intake and evidence-card projection.

## One publishing path

Public evidence → original structured article → Sol Max review of the exact
payload → authenticated private ingress → existing PUBLIC_PROJECTION service
binding → public validator → atomic D1 article/receipt → blog, RSS and sitemap.

The public Worker never invokes an authoring model or fetches arbitrary source
URLs. Source availability, claim support, attribution and image provenance
are checked during authoring. Schema validity and a model-review label are not
proof of truth or authority. Admin authentication supplies authority; SHA-256
binds the reviewed text.

## Files and public routes

- cloudflare/base2026-worker/src/editorial.ts: schema, hash and durable store.
- cloudflare/base2026-worker/src/editorial-render.ts: escaped HTML/JSON-LD/XML.
- cloudflare/base2026-worker/src/editorial-routes.ts: public GET/HEAD only.
- cloudflare/base2026-worker/migrations/0004_editorial_articles.sql: additive
  editorial_articles and editorial_publication_receipts; search tables and
  corpus counters remain separate.
- cloudflare/base2026-worker/src/editorial-catalog.json: two legacy articles.
- cloudflare/base2026-worker/scripts/editorial-packet.mjs: local-only validation
  and packing, with a separately supplied exact-hash review; no network publish.
- templates/base2026-blog-index.html and the two base2026-blog CSS files:
  approved-design surface, integrated by the existing release builder.

| Route | Contract |
| --- | --- |
| /blog | Canonical hub, recent D1 articles plus original journal links |
| /blog/slug/ | Readable original article; canonical trailing slash |
| /blog/feed.xml | RSS with canonical URLs and stable permalink GUIDs |
| /api/blog | Public metadata and keyset pagination cursor |
| /api/blog/slug | Approved public article DTO and content hash |
| /sitemap-blog.xml | Independent sitemap index |
| /sitemaps/blog-n.xml | Up to 100 fully validated article routes per child |

/blog/, /blog.html and /blog/index.html redirect to /blog. An existing article
without its slash redirects to its canonical. Old /journal/ URLs do not move.
Cursor hub pages are noindex,follow; articles remain separately crawlable.

robots.txt advertises the blog index separately: do not nest a sitemap index
inside the root index. The hub itself appears in the static hub sitemap.
Responses have a short cache TTL; a stored receipt is not a browser readback.
Storage or persisted-validation failures return 503, not a successful empty
article. The sitemap index is a count-only list of fixed child endpoints, not
an article-health receipt; every child checks the payload, hash and applied
receipt before emitting any article URL. No HTTP write, private transcript,
raw media or credential is exposed.

## Service-binding contract

Methods on the existing PublicProjectionEntrypoint, not public HTTP:

    publishEditorialArticle(packet, overwrite?)
    inspectEditorialArticle(slug)

The exact TypeScript schema is authoritative. Packet is {payload, review}:

- Schema base2026.editorial.v1; kind source_based_article, engineering_note
  or evidence_guide. Guide requirements are additional, not a bypass.
- Plain-text title, description, lede, category, tags and paragraph/list
  sections. Each cited statement refers to source IDs.
- Source-based articles need at least two distinct source URLs, not a claim
  of independence. Every listed source must be cited by a block.
- Engineering notes need first_party_context and an actual first-party source.
- Evidence guides use a registered existing /topics/slug canonical, at least
  one cited source, an explicit user task and 1–12 exact public dependencies.
  Every dependency binds identity, eight-field document hash, short exact quote
  and citation. At least one must directly support the task. Source counts do
  not certify independence, truth or rights. A separate semantic review remains
  mandatory. The public renderer rechecks dependencies and returns 503 on drift.
- The five registered guide slugs cannot be published as new blog articles.
  Blog lists, RSS and blog sitemaps exclude guides before pagination. Guide
  metadata/content and sitemap use /api/guides, /api/guides/slug and
  /sitemap-guides.xml. These routes and guide HTML are read-only/no-store.
- UTC-normalized publication/update/source-check timestamps; byline Alex
  Yarosh; visible truthful AI-assistance disclosure.
- Optional reviewed /static/assets/ image with alt, credit and ai_generated.
  New image assets require an asset release; article text does not.
- Review fields: reviewer sol-max, outcome pass, reviewed_at and exact
  payload_sha256. Review cannot precede the update or source checks.

Reject unknown fields, unbounded input, arbitrary HTML, secret/contact/local
material, transcript-shaped payloads and unresolved citations. Filters cannot
recognize every unmarked copied transcript; semantic/privacy review remains.

The private ingress uses the existing admin HMAC timestamp/nonce/body-hash
verification. Envelope is exactly {packet, overwrite?}; inspection is {slug}.
Reject unknown fields, query parameters and oversized bodies before RPC.
Do not grant publication authority to intake credentials or model output.
Do not enable the legacy broad release switch. Derive now from the Worker
clock, not the request. Logs contain bounded public slug/hash/result codes,
never payloads, signatures or secrets. No private host or account ID is here.

The complete private HTTP envelope is capped at 65,536 bytes, independently of
the larger pure-validator payload ceiling. The CLI's packet_bytes receipt is
the serialized packet size, not the size of its surrounding transport envelope.
Check the final envelope before dispatch; do not raise the shared ingress limit.

From the public Worker directory, local preparation uses:

```sh
node scripts/editorial-packet.mjs validate --payload /absolute/private/draft.json
node scripts/editorial-packet.mjs pack --payload /absolute/private/draft.json --review /absolute/private/review.json --out /absolute/private/packet.json
```

The review must follow actual source, factual, privacy and rendered-content
checks. Pack creates a new private file exclusively; it never creates a review,
overwrites an existing packet or sends a request. Wrap its payload/review packet
in the exact authenticated transport envelope. Endpoint and credentials belong
only to the protected operator handoff, never public Git or author input.

## Idempotency and correction

One D1 batch writes the article and applied receipt. Exact current
slug/revision/hash replay is a no-op returning already_published. Correction
requires a higher revision and explicit compare-and-swap:

    overwrite = {expected_revision, expected_payload_sha256}

Original publication time stays unchanged. Never adopt a conflict hash and
blindly overwrite another writer. Review the current text and a new correction.
Receipt-insert failure rolls back its article. Historical receipts do not prove
that an old revision is currently live. After a timeout inspect before retrying;
reuse the exact reviewed packet, not regenerated text with the same revision.

For guides, authorized stored-receipt inspection deliberately does not certify
dependency health: it exposes the exact current CAS tuple so a held guide can
be repaired. Public reads use the stricter dependency-checked path. Publication
rechecks snapshots inside the same D1 transaction as the conditional mutation;
read-time hashing is followed by an atomic article/source identity check.
Switching an existing record between blog and guide canonical kinds is refused.

Do not roll back to a pre-guide Worker after a guide has entered this shared
table: old validators cannot safely read the new kind. Restore a verified
guide-compatible version, or use a separately reviewed compatibility/recovery
procedure. Never erase article data or receipts to make an old build appear healthy.

## Authoring, distribution and honest limits

Sol Max research/writing currently runs in the owner's Codex office. It is not
an unlimited cloud-only model API. Cloudflare serves approved articles without
that host. Official Buffer handles X: queued posts publish in its cloud,
refilling requires the office host and protected credentials.

LinkedIn is Computer Use-only under the current safety/confirmation rules,
not Buffer or security-check evasion. Medium uses the original Base2026
canonical. Owned-site links must be contextual, not repeated sitewide blocks.
Measure articles, canonical readbacks, indexing, sessions and useful actions
separately. Social views are not visitors; do not publish filler for a quota.

## Release checklist

1. Confirm exact ownership, live Worker version and remote migration history.
2. Unit/type checks, actual D1 transaction tests and negative route tests.
3. New exact artifact from reviewed public baseline; pin current assets in
   Wrangler so an older design cannot be silently redeployed.
4. Public-boundary gate, unchanged protected CSS/corpus, shell-only navigation
   diff, desktop/mobile/no-JS/canonical/RSS/sitemap checks.
5. Apply additive migration 0004 only if not already applied; evidence guides
   reuse those tables without another migration. Release the public candidate
   and separately reviewed private ingress; each owner deploys only its Worker.
6. Publish one reviewed real article, verify RPC receipt, D1 aggregate, live
   canonical, API, RSS, sitemap and internal links.
7. A specifically authorized first-engine acceptance replay may prove no
   duplicate article or receipt. It is not a routine publishing step; never
   repeat a completed acceptance replay or blindly retry an uncertain write.
8. Record deployed/public, uncommitted, scheduled and measured states
   separately, with rollback and concrete continuation instructions.
