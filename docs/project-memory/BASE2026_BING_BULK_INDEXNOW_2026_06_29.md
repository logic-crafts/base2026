# Base2026 Bing bulk IndexNow submission — 2026-06-29

## Trigger

Alex asked to verify the Bing indexing limit information, prepare Base2026 for mass Bing submission, submit what is safe to submit, and re-prioritize the active marketing/indexation work.

## External rule verification

- Bing Webmaster Tools URL Submission documentation states manual/API URL submission supports up to 10,000 URLs per domain per day, resetting at midnight UTC.
- Bing documentation recommends IndexNow as the preferred automated path.
- IndexNow documentation/FAQ states bulk POST can submit up to 10,000 URLs per request.
- IndexNow is for added, updated, or deleted URLs; submitting all URLs is acceptable when the site has had a broad update/migration/redesign. Base2026 had broad live generated-page/nav/static changes, so a full current sitemap submission is justified.

## Live sitemap set

Source sitemap:

```text
https://aggressorbulkit.online/knowledge/sitemap.xml
```

Live sitemap state at submission time:

- Sitemap index children: 5
- Unique URLs found: 1,703
- Source pages: 1,544
- Topic pages: 40
- Compare pages: 40
- Creator pages: 17
- Other hubs/info/money/resource pages: 62

Generated files:

- `output/indexnow/base2026-all-live-sitemap-urls-20260629.txt`
- `output/indexnow/base2026-priority-nonsource-urls-20260629.txt`
- `output/indexnow/base2026-source-urls-20260629.txt`

## Eligibility gate

A parallel live QA gate checked every sitemap URL for:

- HTTP 200
- no query URL
- no `noindex`
- canonical URL equivalent to the submitted URL
- final URL equivalent to the submitted URL

Result:

- Checked: 1,703
- Eligible: 1,703
- Skipped: 0
- Reason counts: `eligible=1703`

Evidence files:

- `output/indexnow/base2026-all-live-sitemap-20260629-checks-fast.csv`
- `output/indexnow/base2026-all-live-sitemap-20260629-summary.json`
- `output/indexnow/base2026-all-live-sitemap-20260629-payload-fast.json`

## Submission

Endpoint:

```text
https://www.bing.com/indexnow
```

Submission result:

- Submitted URLs: 1,703
- HTTP status: 200
- Retry-After: none
- Result file: `output/indexnow/base2026-all-live-sitemap-20260629-bing-submit-result.json`

The IndexNow key was already hosted and verified through the existing Base2026 root key-file setup. Do not expose the key in user-facing reports.

## Interpretation

This submission notifies Bing/IndexNow; it does not guarantee indexing. Bing will still decide crawl/index inclusion based on accessibility, content quality, internal links, duplication, and crawl budget.

## Next marketing/indexation priority order

1. **Bing verification:** after Bing has time to process, inspect Bing Webmaster Tools IndexNow dashboard and sitemap processing for the 1,703-URL submission. Do not resubmit unchanged URLs repeatedly.
2. **Google Search Console:** keep Google on sitemap + selective URL Inspection only. Do not try to use Google's Indexing API for normal pages. Re-check the existing demand-led/AI visibility URL set before adding more manual requests.
3. **Internal-link reinforcement:** strengthen crawl paths from `/knowledge/`, AI Visibility Lab, AI Visibility Resource Hub, `/knowledge/topics/`, `/knowledge/creators/`, and high-value indexed topic/source pages before generating more near-duplicate pages.
4. **Money-page expansion gate:** expand CTPH/MoneyPage pages only when each page has unique evidence/source support, self-canonical indexable HTML, visual QA, and sitemap inclusion. Keep city/niche drafts `noindex,nofollow` until evidence-approved.
5. **Conversion testing:** pick 3–5 strongest Bing/Copilot/local-service pages for CTA/analytics validation and optional Microsoft Ads/direct-audit experiments.
6. **TikTok/source pipeline:** continue reviewing held `needs_source_review` rows one by one; do not bulk-clear uncertain captions/ASR just to create more pages.

## Do-not-do

- Do not submit `noindex` city/niche drafts.
- Do not repeatedly resubmit unchanged URLs in the same day.
- Do not treat IndexNow status 200 as proof of indexing.
- Do not automate Google request-indexing clicks at scale.
