=== Base2026 Evidence Sidebar ===
Contributors: base2026
Tags: gutenberg, research, seo, geo, citations
Requires at least: 6.5
Requires PHP: 7.4
Tested up to: 7.1
Stable tag: 0.1.1
License: GPLv2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html

Research a short topic in Gutenberg, inspect attributed sources, and optionally insert an editable research note.

== Description ==

Base2026 Evidence Sidebar adds a small Gutenberg PluginSidebar for researching a short topic against Base2026's free, read-only public corpus of curated expert-video evidence.

The editor types a topic (up to 160 characters), or explicitly clicks **Use selected block text** to copy text from the currently selected block into the query field. Nothing is read or sent automatically. After an explicit search click, the plugin shows a bounded set of public source cards with a source claim/title label, an evidence excerpt when the public brief provides one, creator attribution when available, publication date when available, the original source URL, and the corresponding Base2026 source record when returned.

The cards explain what an attributed source says. They do not label a claim as true, supported, counterevidence, authoritative, or effective. This is research from a bounded video corpus, not whole-web verification, an SEO score, an automatic rewrite, or a substitute for reviewing the original source.

An **Insert research note** button is a separate second click. It inserts editable native Paragraph blocks containing a clearly labelled research note, the bounded source excerpt, creator attribution, and original source link. It deliberately does not create a quotation block or claim that the excerpt is verbatim. A Base2026 source-record link is optional and is never inserted unless the editor checks the opt-in control.

== Installation ==

1. Download a reviewed plugin ZIP containing the `base2026-evidence-sidebar` directory.
2. In WordPress, open **Plugins > Add New > Upload Plugin** and upload the ZIP, or copy the directory into `wp-content/plugins/`.
3. Activate **Base2026 Evidence Sidebar**.
4. Open a block-editor post or page as a user who can edit posts. Open the Base2026 Evidence panel from the editor sidebar or its More menu item.

This is a manual-install beta. Try it on a staging site first. The source repository contains the four plugin files; the release builder packages those exact reviewed files into the installable ZIP. WordPress.org directory acceptance is a separate step. Plugin homepage: https://base2026.dev/tools/wordpress-evidence-sidebar/. Source: https://github.com/offflinerpsy/base2026/tree/main/plugins/wordpress/base2026-evidence-sidebar. Support: hello@base2026.dev or https://github.com/offflinerpsy/base2026/issues.

== External service, privacy, and limits ==

The first-search notice links to the live [Base2026 Privacy page](https://base2026.dev/privacy), [public API boundary and limits](https://base2026.dev/api), and [Source & Content Policy](https://base2026.dev/source-policy). These links describe the public service's current boundary; Base2026 does not provide a WordPress account or API key for this plugin. Do not enter confidential information.

After an editor clicks **Search Base2026**, the browser sends the short query and the WordPress REST nonce to this installation's authenticated local REST route; the nonce is used locally and is not forwarded upstream. The route requires a valid WordPress REST nonce and `edit_posts`. The WordPress server then sends the short query to `https://base2026.dev/api/evidence-brief/v2`, the existing bounded Evidence Brief v2 endpoint, with the per-request user-agent `Base2026-Evidence-Sidebar/0.1.1`. Base2026 and Cloudflare may observe ordinary server-network metadata, including the WordPress server's IP address. The public brief returns at most five attributed findings with an `evidence_excerpt` when available; no hit body or full transcript field is requested.

The plugin does not send the full post, post ID, record IDs, referrer, WordPress credentials, REST nonce, browser cookies, or account data to Base2026. The application query sent upstream is the short topic you submit, including selected-block text if you explicitly copy it into the topic field and then search; the request also carries the plugin user-agent and ordinary server-network metadata described above. The plugin does not set or inspect cookies for tracking or plugin storage; the authenticated browser request may use the site's normal WordPress session credentials locally, and no browser cookies are forwarded upstream. It does not use local storage, fingerprinting, a separate analytics request, a Base2026 login, or persistent plugin storage, and it adds no persistent query storage or analytics. The public service may cache responses under its service policy. External operational logging follows Base2026/Cloudflare service policy; Cloudflare operational-metadata logging and retention for these requests have not yet been verified, so no zero-logging or retention-duration guarantee is made. The fixed server request has a finite timeout and response-size limit. Unknown request fields, oversized bodies, invalid query text, non-HTTP(S) source links, malformed responses, upstream errors, and rate limits are handled as errors rather than silently treated as evidence. Do not enter confidential information.

The public response is reduced to short display fields. The plugin does not request or return raw media or full private transcripts. A returned `evidence_excerpt` is preserved as a bounded public-source excerpt, but the plugin does not assert that it is a verbatim quotation; the insertion action creates a labelled research note instead. When no excerpt is returned, the card shows only the source claim/title label and insertion is disabled. Review the original source and Base2026 policy before publishing a note.

== Scope and limitations ==

* Search is limited to the public expert-video corpus returned by the fixed Base2026 endpoint; it is not a whole-web search.
* An empty result is not proof that a topic has no evidence. A displayed result is not proof that a recommendation works.
* A missing creator, date, original URL, or Base2026 record is shown as unavailable. The research-note button is disabled when an original source link or a bounded evidence excerpt is unavailable.
* Inserted content is a draft editing aid. It is not automatically saved or published, and the plugin does not add a backlink without an explicit opt-in.
* The WordPress route is intentionally editor-authenticated. Site administrators should review their own WordPress access controls and outbound HTTP policy.

== Changelog ==

= 0.1.1 =
* Use an explicit neutral plugin user-agent for the bounded server request.
* Clarify local nonce handling, ordinary server-network metadata, service caching, and operational logging/retention boundaries.
* Use a neutral inserted-note heading while keeping the optional Base2026 source link opt-in.
* Add the short summary, public source/homepage links, and support route.

= 0.1.0 =
* Initial bounded Gutenberg sidebar with explicit query, source attribution, privacy notice, honest result boundaries, and optional labelled research-note insertion.
