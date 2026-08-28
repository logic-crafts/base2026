# Base2026 Google Search Console and Bing Webmaster Tools preflight

Date: 2026-08-28
Scope: preflight plus owner-authorized execution for `https://base2026.dev/`
Status: **verified, submitted, and live-checked on 2026-08-28**

## Execution receipt — 2026-08-28

- Google Search Console: Domain property `sc-domain:base2026.dev` is verified
  under `hello@base2026.dev` through the existing DNS-provider verification
  path. No verification token is stored here.
- Google sitemap readback: `https://base2026.dev/sitemap.xml` is a successful
  sitemap index; `https://base2026.dev/sitemap-dynamic.xml` is successful and
  reports 39 discovered pages.
- Bing Webmaster Tools: only `https://base2026.dev/` was imported from Google
  Search Console. The separate personal property was not selected or changed.
- Bing sitemap readback: both sitemap URLs were successfully submitted with
  zero immediate errors and zero warnings; both are currently Processing.
- IndexNow: one 57-URL canonical change packet was accepted with HTTP `202`.
  The public key remains outside this document. Acceptance is a notification
  receipt, not proof of indexing.
- The former gate is closed: the production sitemap contains 1,633 unique
  extensionless URLs and zero `.html` URLs, the dynamic sitemap returns 39
  eligible pages, and sampled final pages are self-canonical and HTTP `200`.

The sections below preserve the original preflight and explain why submission
was initially blocked. They are historical evidence, not the current state.

## Result

The safest ownership path is:

1. Verify a Google Search Console **Domain property** for `base2026.dev` from the owner-controlled Base2026 Google Workspace account.
2. After the property is verified and the public URL set is clean, import only that property into Bing Webmaster Tools using Bing's Google Search Console import. Use Bing's manual DNS/XML/meta methods only if import is unavailable.
3. Preserve the separate personal property for `aggressorbulkit.online`. Do not rename, merge, remove, submit the Base2026 sitemap to, or otherwise change that property.

Do not submit a sitemap yet. The live sitemap has a material URL/canonical inconsistency that should be corrected and rechecked first.

## Boundary and work performed

No authenticated browser or dashboard was opened. No property was created, DNS or site content was changed, sitemap or URL was submitted, IndexNow notification was sent, deployment was run, or token was copied into this document. The repository was already dirty; this preflight adds only this document.

The account boundary for the mutation owner is the Base2026 Workspace identity recorded by the project (`hello@base2026.dev`, re-confirm at execution time). The personal `aggressorbulkit.online` property remains outside this task. If both properties appear in one account selector, select only the exact `base2026.dev` property.

## Current live evidence (checked 2026-08-28)

### DNS and site separation

| Surface | Current public evidence |
|---|---|
| `base2026.dev` | Cloudflare A: `104.21.26.76`, `172.67.135.159`; Cloudflare AAAA present; NS: `elly.ns.cloudflare.com`, `vicky.ns.cloudflare.com`; MX: `1 smtp.google.com` |
| `www.base2026.dev` | Cloudflare edge; redirects `301` to the apex |
| `aggressorbulkit.online` | Separate A: `207.244.242.42`; Timeweb NS (`ns1/ns2.timeweb.ru`, `ns3/ns4.timeweb.org`); Timeweb MX (`mx1/mx2.timeweb.ru`) |

One redacted Google Search Console-style TXT value is present at the Base2026 apex, but its owner/property match is unproven. It may belong to another Google service. Do not treat its presence as verified ownership or delete/replace it without an owner dependency check. Personal-domain verification TXT records are separate and are not evidence for Base2026.

### HTTP, robots, and sitemap

| URL | Result |
|---|---|
| `https://base2026.dev/` | `200`, HTML, `index,follow`, self-canonical |
| `https://base2026.dev/workspace/` | `200`, HTML, `index,follow`, self-canonical |
| `https://base2026.dev/robots.txt` | `200`, `text/plain` |
| `https://base2026.dev/sitemap.xml` | `200`, XML sitemap index |
| `https://base2026.dev/sitemap-dynamic.xml` | `404` |
| `https://base2026.dev/api/health` | `200`, `{"ok":true,"service":"base2026","search":"d1-fts5","index":"base2026_public_tiktok"}` |

Current `robots.txt` is:

```text
User-agent: *
Allow: /

Sitemap: https://base2026.dev/sitemap.xml
```

The live sitemap index has five child sitemaps, each returning `200` XML, with **1,617 `<url>` records** in total:

- 1,526 `/sources/` records, including 1,525 `.html` detail URLs;
- 88 `/topics/` records, including 87 `.html` detail URLs;
- 3 other `.html` pages; and
- no creator, compare, or solution records.

The root and child sitemap `<lastmod>` values are `2026-07-29`. The public manifest reports a release created `2026-07-29T14:27:42` with 1,525 public source documents. The local release builder emits a second dynamic-sitemap line and the Worker source has a dynamic route, but that route currently returns `404`; this is local/live drift, not a change made here.

### URL/canonical gate (blocking)

Representative sitemap detail checks showed:

- `/sources/tiktok-video-7388244947352210734.html` → `307` to `/sources/tiktok-video-7388244947352210734` → final `200`, while the final HTML declares the `.html` URL canonical;
- `/topics/ai-citations.html` → `307` to `/topics/ai-citations` → final `200`, while the final HTML declares the `.html` URL canonical.

Thus the sitemap's generated detail URLs are at least partly redirecting URLs whose final pages point canonical back to the redirecting form. The full 1,612-detail corpus was not exhaustively rechecked in this bounded preflight; treat this as a release gate and verify every sitemap URL before submission. Google and Bing should receive stable, absolute canonical URLs that return the canonical final response. Do not “solve” this by submitting both URL forms.

Several public pages inspected outside the sitemap (`/`, `/workspace/`, `/creators/`, `/methodology.html`, `/api.html`) returned `200` with index-follow metadata and self-canonicals but are not listed in the static sitemap. Decide intentionally whether that is omission or expected scope before submission. `support.html`, `apply-research.html`, and `privacy.html` also require a final metadata/indexability pass before being treated as sitemap candidates.

## Existing local receipts and verification markers

- Existing GSC/Bing documents are historical records for the old `aggressorbulkit.online`/`/knowledge/` surface; they are not a current `base2026.dev` verification receipt.
- The old GSC record names `sc-domain:aggressorbulkit.online`; do not reuse it for Base2026.
- Current Base2026 HTML/source scans found no `google-site-verification`, `msvalidate.01`, `BingSiteAuth.xml`, or Bing meta verification marker.
- A root-hosted IndexNow key file is publicly reachable, but an IndexNow key authenticates URL notifications and is **not** proof that a Bing Webmaster property is owned. Its filename and value are intentionally omitted.
- Historical JSON receipts referenced by older docs are not present in the current checkout. No current GSC/Bing dashboard readback exists in this preflight.

## Mutation checklist (owner-authorized follow-up only)

1. **Confirm identity and target.** In the owner-controlled Workspace account, add/select exactly Domain `base2026.dev` (not `https://www.base2026.dev/`, a path, or `aggressorbulkit.online`). Keep the personal property untouched.
2. **Verify GSC ownership.** Use the Search Console wizard's DNS TXT/CNAME record. Record the exact token only in the approved DNS/password-management surface; never put it in project docs. Add it at the Base2026 DNS provider only if the wizard token is not already served. Keep the record while the property is in use.
3. **Capture GSC proof.** Read back `sc-domain:base2026.dev`, verified owner/account alias, verification method, and timestamp. Do not copy the token. Confirm `sc-domain:aggressorbulkit.online` still exists unchanged.
4. **Close the URL gate.** Separately correct or explicitly accept the `.html`/extensionless redirect-canonical mismatch, then recheck all 1,617 sitemap records for HTTP status, final URL, canonical equivalence, indexability, and robots access. Recheck the sitemap index, child files, and dynamic-sitemap decision after the release. Preserve the current release and documented Worker rollback until the new state passes.
5. **Submit one sitemap in GSC.** Only after step 4, submit the exact `https://base2026.dev/sitemap.xml`. Capture Success, last-read time, and discovered count. Do not bulk use Request indexing; a sitemap is a discovery hint, not an indexing guarantee.
6. **Import to Bing.** In Bing Webmaster Tools, use Google Search Console import and select only `base2026.dev`. Confirm automatic verification/property name and imported sitemap scope. If import is unavailable, add `https://base2026.dev/` manually and use a DNS CNAME, XML file, or meta method; keep the verification control in the owner account.
7. **Capture Bing proof.** Read back the selected `base2026.dev` site, verification state, sitemap URL/status, and timestamp. Do not submit the old personal sitemap or `/knowledge/sitemap.xml` to the Base2026 property.
8. **Use IndexNow only for later changes.** If a live canonical URL changes after verification, notify only changed canonical URLs with the existing host key and record the notification response plus Bing dashboard readback. Acceptance (`200`/`202`) is not proof of crawl or indexing.

### Proof and rollback

- Proof must identify the exact property, owner account alias, verification method, sitemap URL, dashboard status, last-read time, and live URL checks—never a credential or token.
- If the wrong GSC/Bing property is created, remove only the new property/import connection or revoke the new account linkage after recording the mistake; do not touch the personal property.
- If DNS ownership is later retired, remove only the newly added record after checking that no other service depends on it. Do not delete the existing redacted Google TXT by assumption.
- If the URL/release gate regresses, restore the last known-good Worker/static release and sitemap, then re-run HTTP/canonical checks. No rollback or external mutation was performed here.

## Official references

- [Google: Verify site ownership](https://support.google.com/webmasters/answer/9008080)
- [Google: Submit a sitemap](https://support.google.com/webmasters/answer/7451001)
- [Google: Build and submit a sitemap](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap)
- [Google: Robots.txt specification](https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec)
- [Bing: Add and verify a site](https://www.bing.com/webmasters/help/add-and-verify-site-12184f8b)
- [Bing: Submit sitemaps](https://www.bing.com/webmasters/help/sitemaps-3b5cf6ed)
- [Bing: URL submission](https://www.bing.com/webmasters/help/URL-Submission-62f2860b)
- [Bing: IndexNow getting started](https://www.bing.com/indexnow/getstarted)
