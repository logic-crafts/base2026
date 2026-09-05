(function (wp, global) {
	"use strict";
	if (!wp || !global) return;

	var element = wp.element || {};
	var components = wp.components || {};
	var data = wp.data || {};
	var blocks = wp.blocks || {};
	var plugins = wp.plugins || {};
	var editPost = wp.editPost || {};
	var editor = wp.editor || {};
	var PluginSidebar = editPost.PluginSidebar || editor.PluginSidebar;
	var PluginSidebarMoreMenuItem = editPost.PluginSidebarMoreMenuItem || editor.PluginSidebarMoreMenuItem;

	if (
		!element.createElement ||
		!element.Fragment ||
		!element.useRef ||
		!element.useState ||
		!components.Button ||
		!components.CheckboxControl ||
		!components.Notice ||
		!components.PanelBody ||
		!components.Spinner ||
		!components.TextControl ||
		!data.select ||
		!data.dispatch ||
		!blocks.createBlock ||
		!plugins.registerPlugin ||
		!PluginSidebar ||
		!PluginSidebarMoreMenuItem
	) {
		return;
	}

	var createElement = element.createElement;
	var Fragment = element.Fragment;
	var useRef = element.useRef;
	var useState = element.useState;
	var Button = components.Button;
	var CheckboxControl = components.CheckboxControl;
	var Notice = components.Notice;
	var PanelBody = components.PanelBody;
	var Spinner = components.Spinner;
	var TextControl = components.TextControl;
	var config = global.Base2026EvidenceSidebarConfig || {};
	var MAX_QUERY_CHARS = Number(config.maxQueryChars) || 160;
	var DEFAULT_PRIVACY_URL = "https://base2026.dev/privacy";
	var DEFAULT_LIMITS_URL = "https://base2026.dev/api";
	var DEFAULT_SOURCE_POLICY_URL = "https://base2026.dev/source-policy";
	var QUALITY_NOTE = "This card shows what an attributed public source says. It is not independent verification, a consensus score, or a promise that the recommendation works.";

	function cleanText(value, limit) {
		if (typeof value !== "string") return "";
		var compact = value.replace(/\s+/g, " ").trim();
		if (!compact) return "";
		return compact.slice(0, limit);
	}

	function stripMarkup(value) {
		if (typeof value !== "string") return "";
		return value.replace(/<[^>]*>/g, " ").replace(/&nbsp;/gi, " ");
	}

	function escapeHtml(value) {
		return String(value).replace(/[&<>"']/g, function (character) {
			return {
				"&": "&amp;",
				"<": "&lt;",
				">": "&gt;",
				'"': "&quot;",
				"'": "&#039;"
			}[character];
		});
	}

	function safeHttpUrl(value) {
		if (typeof value !== "string" || !value.trim()) return "";
		try {
			var parsed = new global.URL(value.trim());
			if (parsed.protocol !== "http:" && parsed.protocol !== "https:") return "";
			if (parsed.username || parsed.password) return "";
			return parsed.href;
		} catch (error) {
			return "";
		}
	}

	function safeBase2026Url(value) {
		var safe = safeHttpUrl(value);
		if (!safe) return "";
		try {
			var parsed = new global.URL(safe);
			return parsed.protocol === "https:" && parsed.hostname === "base2026.dev" && parsed.pathname.indexOf("/sources/") === 0 ? safe : "";
		} catch (error) {
			return "";
		}
	}

	function docsUrl(value, fallback) {
		var safe = safeHttpUrl(typeof value === "string" ? value : "");
		return safe || fallback;
	}

	function isAllowedRestEndpoint(value) {
		if (typeof value !== "string" || !value.trim()) return false;
		try {
			var endpoint = new global.URL(value, global.location.href);
			var current = new global.URL(global.location.href);
			var configured = new global.URL(config.restUrl, global.location.href);
			if (endpoint.origin !== current.origin || configured.origin !== current.origin || endpoint.username || endpoint.password || endpoint.hash) return false;
			if (endpoint.pathname !== configured.pathname || endpoint.search !== configured.search) return false;
			var adminMarker = current.pathname.indexOf("/wp-admin/");
			var sitePrefix = adminMarker >= 0 ? current.pathname.slice(0, adminMarker) : "";
			var prettyPath = sitePrefix + "/wp-json/base2026/v1/search";
			if (endpoint.pathname === prettyPath || endpoint.pathname === prettyPath + "/") {
				return endpoint.search === "";
			}
			if (endpoint.pathname !== sitePrefix + "/" && endpoint.pathname !== sitePrefix + "/index.php") return false;
			var queryKeys = [];
			endpoint.searchParams.forEach(function (_value, key) { queryKeys.push(key); });
			return queryKeys.length === 1 && endpoint.searchParams.get("rest_route") === "/base2026/v1/search";
		} catch (error) {
			return false;
		}
	}

	function selectedBlockQuery() {
		var blockEditor = data.select("core/block-editor");
		if (!blockEditor || !blockEditor.getSelectedBlock) return "";
		var selected = blockEditor.getSelectedBlock();
		if (!selected || !selected.attributes) return "";
		var attributes = selected.attributes;
		var candidate = attributes.content || attributes.text || attributes.heading || "";
		return cleanText(stripMarkup(candidate), MAX_QUERY_CHARS);
	}

	function normalizeResults(payload) {
		if (!payload || !Array.isArray(payload.results)) {
			throw new Error("invalid_response");
		}

		var seen = {};
		return payload.results.reduce(function (output, item) {
			if (!item || typeof item !== "object") return output;
			var title = cleanText(item.title, 180);
			var excerpt = cleanText(stripMarkup(item.excerpt), 480);
			var excerptKind = item.excerpt_kind === "public_evidence_excerpt" && excerpt ? "public_evidence_excerpt" : "source_claim_only";
			var creator = cleanText(item.creator, 120);
			var originalUrl = safeHttpUrl(item.original_url);
			var base2026Url = safeBase2026Url(item.base2026_url);
			if (!title && !excerpt) return output;
			if (!title) title = "Source excerpt";

			var identity = base2026Url || originalUrl || title + "|" + creator;
			if (seen[identity]) return output;
			seen[identity] = true;
			output.push({
				title: title,
				titleKind: "source_claim_label",
				excerpt: excerpt,
				excerptKind: excerptKind,
				provenance: cleanText(item.provenance, 180) || "Base2026 Evidence Brief v2 · public source finding",
				creator: creator,
				published: cleanText(item.published, 30),
				originalUrl: originalUrl,
				base2026Url: base2026Url,
				qualityNote: cleanText(item.source_quality_note, 360) || QUALITY_NOTE,
				key: identity
			});
			return output;
		}, []);
	}

	function errorMessage(error) {
		if (error && error.message === "invalid_response") {
			return "The public evidence response could not be read. Try again shortly.";
		}
		if (error && error.message === "endpoint") {
			return "The local WordPress search route is not available. Reload the editor and try again.";
		}
		if (error && error.status === 403) {
			return "WordPress editor permission or nonce validation failed. Reload the editor and try again.";
		}
		if (error && error.status === 429) {
			return "The public Base2026 evidence brief is rate-limited. Wait a moment before trying again.";
		}
		return "The public Base2026 evidence brief could not be reached. Try again shortly.";
	}

	function makeResearchNoteBlocks(card, includeBase2026) {
		var note = blocks.createBlock("core/paragraph", {
			content: "<strong>Base2026 research note — bounded source excerpt (not a verbatim quotation or independent verification)</strong><br>" + escapeHtml(card.excerpt)
		});
		var attribution = "Source: " + escapeHtml(card.creator || "Public source") + " — <a href=\"" + escapeHtml(card.originalUrl) + "\" rel=\"nofollow noopener noreferrer\">Original source</a>";
		if (includeBase2026 && card.base2026Url) {
			attribution += " · <a href=\"" + escapeHtml(card.base2026Url) + "\" rel=\"noopener noreferrer\">Base2026 source record</a>";
		}
		var attributionBlock = blocks.createBlock("core/paragraph", {
			content: attribution
		});
		return [note, attributionBlock];
	}

	function Link(props) {
		return createElement(
			"a",
			{
				href: props.href,
				target: "_blank",
				rel: "noopener noreferrer"
			},
			props.children
		);
	}

	function PolicyNotice() {
		return createElement(
			Notice,
			{status: "warning", isDismissible: false},
			createElement(
				"p",
				null,
				"Before you search: this sends only the short topic you submit to Base2026's public search service. It does not send the rest of this post, a post ID, or account data to Base2026. Base2026 is free and read-only; its excerpts are attributed source claims, not whole-web verification. ",
				createElement(Link, {href: docsUrl(config.privacyUrl, DEFAULT_PRIVACY_URL)}, "Privacy"),
				" · ",
				createElement(Link, {href: docsUrl(config.serviceLimitsUrl, DEFAULT_LIMITS_URL)}, "API boundary & limits"),
				" · ",
				createElement(Link, {href: docsUrl(config.sourcePolicyUrl, DEFAULT_SOURCE_POLICY_URL)}, "Source policy")
			)
		);
	}

	function ResultCard(props) {
		var card = props.card;
		var canInsert = Boolean(card.originalUrl && card.excerpt && card.excerptKind === "public_evidence_excerpt");
		var creator = card.creator || "Creator attribution unavailable in this record.";
		var excerptContent = card.excerpt
			? createElement("p", null, createElement("strong", null, "Bounded source excerpt: "), card.excerpt)
			: createElement("p", null, "No bounded evidence excerpt was returned; this card shows the source title/claim label only.");
		return createElement(
			"article",
			{className: "b26-evidence-sidebar__card"},
			createElement("h3", null, "Source claim/title label"),
			createElement("p", null, card.title),
			createElement("p", {className: "b26-evidence-sidebar__provenance"}, card.provenance),
			createElement("p", null, createElement("strong", null, "Creator: "), creator),
			card.published ? createElement("p", null, createElement("strong", null, "Published: "), card.published) : null,
			excerptContent,
			createElement("p", {className: "b26-evidence-sidebar__quality-note"}, card.qualityNote),
			createElement(
				"p",
				null,
				card.originalUrl
					? createElement(Link, {href: card.originalUrl}, "Open original source ↗")
					: "Original source link unavailable in this record.",
				card.base2026Url ? [" · ", createElement(Link, {key: "base", href: card.base2026Url}, "Open Base2026 record")] : null
			),
			createElement(
				Button,
				{
					isSecondary: true,
					disabled: !canInsert || props.inserted,
					onClick: function () { props.onInsert(card); }
				},
				props.inserted ? "Inserted research note" : canInsert ? "Insert research note" : "No excerpt to insert"
			)
		);
	}

	function Sidebar() {
		var queryState = useState("");
		var query = queryState[0];
		var setQuery = queryState[1];
		var resultsState = useState([]);
		var results = resultsState[0];
		var setResults = resultsState[1];
		var statusState = useState({kind: "", text: ""});
		var status = statusState[0];
		var setStatus = statusState[1];
		var loadingState = useState(false);
		var loading = loadingState[0];
		var setLoading = loadingState[1];
		var searchedState = useState(false);
		var hasSearched = searchedState[0];
		var setHasSearched = searchedState[1];
		var includeBaseState = useState(false);
		var includeBase2026 = includeBaseState[0];
		var setIncludeBase2026 = includeBaseState[1];
		var insertedState = useState({});
		var inserted = insertedState[0];
		var setInserted = insertedState[1];
		var pending = useRef(false);
		var requestSequence = useRef(0);

		function useSelectedText() {
			var selected = selectedBlockQuery();
			if (!selected) {
				setStatus({kind: "error", text: "Select a short text block first; nothing in the post is read automatically."});
				return;
			}
			setQuery(selected);
			setStatus({kind: "info", text: "Selected block text copied into the short query field. Review it before searching."});
		}

		function insertResearchNote(card) {
			if (!card.originalUrl || !card.excerpt || card.excerptKind !== "public_evidence_excerpt" || inserted[card.key]) return;
			try {
				var blocksToInsert = makeResearchNoteBlocks(card, includeBase2026);
				data.dispatch("core/block-editor").insertBlocks(blocksToInsert);
				setInserted(Object.assign({}, inserted, {[card.key]: true}));
				setStatus({kind: "success", text: "Inserted an editable research note and attribution paragraphs. They are not a verbatim quotation; review them before publishing."});
			} catch (error) {
				setStatus({kind: "error", text: "WordPress could not insert the research note. The source card was not marked as inserted."});
			}
		}

		function search() {
			if (pending.current) return;
			var normalized = typeof query === "string" ? query.replace(/\s+/g, " ").trim() : "";
			if (!normalized || normalized.length > MAX_QUERY_CHARS) {
				setStatus({kind: "error", text: "Enter a short topic between 1 and " + MAX_QUERY_CHARS + " characters."});
				return;
			}
			if (!isAllowedRestEndpoint(config.restUrl)) {
				setStatus({kind: "error", text: errorMessage({message: "endpoint"})});
				return;
			}
			if (typeof global.fetch !== "function") {
				setStatus({kind: "error", text: "This browser cannot make the editor search request."});
				return;
			}

			pending.current = true;
			var requestId = requestSequence.current + 1;
			requestSequence.current = requestId;
			setHasSearched(true);
			setLoading(true);
			setResults([]);
			setStatus({kind: "loading", text: "Searching the bounded public corpus…"});
			var controller = global.AbortController ? new global.AbortController() : null;
			var timeoutId = global.setTimeout(function () {
				if (controller) controller.abort();
			}, 10000);
			var options = {
				method: "POST",
				credentials: "same-origin",
				headers: {
					"Content-Type": "application/json",
					"X-WP-Nonce": String(config.nonce || "")
				},
				body: JSON.stringify({query: normalized})
			};
			if (controller) options.signal = controller.signal;

			global.fetch(config.restUrl, options)
				.then(function (response) {
					return response.text().then(function (text) {
						var payload = null;
						try {
							payload = JSON.parse(text);
						} catch (error) {
							throw new Error("invalid_response");
						}
						if (!response.ok) {
							var httpError = new Error("http");
							httpError.status = response.status;
							throw httpError;
						}
						return normalizeResults(payload);
					});
				})
				.then(function (cards) {
					if (requestId !== requestSequence.current) return;
					setResults(cards);
					setStatus({
						kind: cards.length ? "result" : "empty",
						text: cards.length ? "Showing " + cards.length + " bounded public source cards. Inspect attribution before using a claim." : "No matching records were returned from the bounded public corpus."
					});
				})
				.catch(function (error) {
					if (requestId !== requestSequence.current) return;
					setResults([]);
					setStatus({kind: "error", text: errorMessage(error)});
				})
				.then(function () {
					global.clearTimeout(timeoutId);
					if (requestId === requestSequence.current) {
						pending.current = false;
						setLoading(false);
					}
				});
		}

		var hasBaseLink = results.some(function (card) { return Boolean(card.base2026Url); });
		return createElement(
			Fragment,
			null,
			createElement(PluginSidebarMoreMenuItem, {target: "base2026-evidence-sidebar"}, "Base2026 Evidence"),
			createElement(
				PluginSidebar,
				{name: "base2026-evidence-sidebar", title: "Base2026 Evidence", icon: "format-quote"},
				!hasSearched ? createElement(PolicyNotice) : null,
				createElement(
					"p",
					{className: "b26-evidence-sidebar__intro"},
					"Free SEO/GEO research from Base2026's bounded, curated expert-video evidence. This is not whole-web verification, an SEO score, or an automatic rewrite."
				),
				createElement(
					PanelBody,
					{title: "Search public evidence", initialOpen: true},
					createElement(TextControl, {
						label: "Short topic to research",
						value: query,
						onChange: function (value) { setQuery(value); },
						maxLength: MAX_QUERY_CHARS,
						help: "Type or paste up to " + MAX_QUERY_CHARS + " characters. The post is not read automatically."
					}),
					createElement(
						Button,
						{isSecondary: true, onClick: useSelectedText, disabled: loading},
						"Use selected block text"
					),
					createElement(
						Button,
						{isPrimary: true, isBusy: loading, onClick: search, disabled: loading || !query.trim()},
						loading ? "Searching…" : "Search Base2026"
					),
					status.text ? createElement("p", {"aria-live": "polite", className: "b26-evidence-sidebar__status"}, status.text) : null
				),
				results.length
					? createElement(
						PanelBody,
						{title: "Source cards", initialOpen: true},
						createElement(CheckboxControl, {
							label: hasBaseLink ? "Add an optional Base2026 source link when inserting" : "Add optional Base2026 source link (none returned)",
							checked: includeBase2026,
							onChange: setIncludeBase2026,
							disabled: !hasBaseLink
						}),
						results.map(function (card) {
							return createElement(ResultCard, {
								key: card.key,
								card: card,
								inserted: Boolean(inserted[card.key]),
								onInsert: insertResearchNote
							});
						})
					)
					: null,
				loading ? createElement(Spinner) : null
			)
		);
	}

	plugins.registerPlugin("base2026-evidence-sidebar", {
		render: Sidebar,
		icon: "format-quote"
	});
})(window.wp, window);
