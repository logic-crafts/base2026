# Base2026 / Alex Source Footprint proof bridge — 2026-06-27

Status: live small-batch proof bridge deployed and QA checked.

## Strategic intent

Connect Alex conversion/MoneyPages with the Base2026 proof layer without turning commercial pages into bloated research pages.

Pattern:

- Alex site: explains service, audit, pricing, conversion.
- Base2026: supplies public source-backed proof and methodology.
- Source Footprint page: explains why an AI visibility audit checks more than the website.

## Live changes

### Alex / MoneyPage layer

- `https://aggressorbulkit.online/ai-visibility-source-footprint/`
  - Added Research trail links to:
    - `/knowledge/ai-visibility-pages/`
    - `/knowledge/measuring-ai-visibility-without-query-click-data/`
    - `/knowledge/topics/brand-proof-pages.html`
    - `/knowledge/topics/ai-citations.html`
  - Removed a low-contrast inline link from the orange featured block after mobile QA.

- `https://aggressorbulkit.online/ai-visibility-audit/`
  - Added copy explaining that the snapshot maps the wider AI visibility source footprint.
  - Added CTA link: `See Source Footprint` → `/ai-visibility-source-footprint/`.

- `https://aggressorbulkit.online/ai-visibility-diagnostic-audit/`
  - Added source-footprint explanation inside the Base2026 research section.
  - Added CTA link: `See Source Footprint` → `/ai-visibility-source-footprint/`.

- `https://aggressorbulkit.online/pricing/`
  - Replaced proof card 02 with `Source footprint gaps` linking to `/ai-visibility-source-footprint/`.

## Index gate result

All changed URLs passed live checks:

- HTTP 200.
- Self-canonical.
- No `noindex` conflict.
- Expected new links present.
- Target proof URLs return HTTP 200.

Evidence:

- `geo/output/evidence/source-footprint-proof-bridge-20260627/live-link-check.json`
- `geo/output/evidence/source-footprint-proof-bridge-20260627/mobile-qa.json`
- `geo/output/evidence/source-footprint-proof-bridge-20260627/source-footprint-mobile.png`
- `geo/output/evidence/source-footprint-proof-bridge-20260627/pricing-mobile.png`

## Visual QA notes

- Source Footprint desktop: new Research trail links wrap cleanly; no clipping/overlap. Cookie banner overlays mid-page as expected.
- Source Footprint mobile 390px: `docScrollWidth=390`, `bodyScrollWidth=390`, no horizontal overflow, offenders empty.
- Pricing desktop: proof card 02 layout acceptable.
- Pricing mobile 390px: no horizontal overflow, proof card link present. Cookie banner obscures lower pricing content in screenshot but does not indicate layout breakage.

## IndexNow

Submit only the four changed canonical indexable URLs:

- `/ai-visibility-source-footprint/`
- `/ai-visibility-audit/`
- `/ai-visibility-diagnostic-audit/`
- `/pricing/`

Google action remains sitemap/GSC priority monitoring; no Google Indexing API or bulk request-indexing automation.
