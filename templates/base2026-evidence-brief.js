(() => {
  "use strict";

  const statsStatus = document.querySelector("[data-b26-stats-status]");
  const statNodes = [...document.querySelectorAll("[data-b26-public-stat]")];
  const loadPublicStats = async () => {
    if (!(statsStatus instanceof HTMLElement) || statNodes.length === 0) return;
    try {
      const response = await fetch("/api/stats", { headers: { Accept: "application/json" } });
      if (!response.ok) return;
      const payload = await response.json();
      const dataset = payload && typeof payload === "object" ? payload.dataset : null;
      if (!dataset || typeof dataset !== "object") return;
      for (const node of statNodes) {
        const key = node.getAttribute("data-b26-public-stat");
        const value = key ? Number(dataset[key]) : Number.NaN;
        if (Number.isSafeInteger(value) && value >= 0) node.textContent = value.toLocaleString("en-US");
      }
      const updated = new Date(typeof payload.generated_at === "string" ? payload.generated_at : "");
      const timestamp = Number.isNaN(updated.getTime())
        ? "just now"
        : `${updated.toISOString().slice(0, 16).replace("T", " ")} UTC`;
      statsStatus.textContent = `Live public D1 · updated ${timestamp}`;
    } catch {
      // Keep the verified release snapshot when the live read-only endpoint is unavailable.
    }
  };
  void loadPublicStats();

  const form = document.querySelector(".b26-brief-search");
  const input = document.querySelector("#b26-brief-query");
  const result = document.querySelector("#evidence-brief-result");
  const title = document.querySelector("#evidence-brief-title");
  const status = document.querySelector("#evidence-brief-status");
  const body = document.querySelector("#evidence-brief-body");
  const copyButton = document.querySelector("#evidence-brief-copy");
  const resetButton = document.querySelector("#evidence-brief-reset");
  if (!(form instanceof HTMLFormElement) || !(input instanceof HTMLInputElement) || !(result instanceof HTMLElement)
    || !(title instanceof HTMLElement) || !(status instanceof HTMLElement) || !(body instanceof HTMLElement) || !(copyButton instanceof HTMLButtonElement)
    || !(resetButton instanceof HTMLButtonElement)) return;

  let copyText = "";

  const element = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (typeof text === "string") node.textContent = text;
    return node;
  };

  const safeLink = (value, label, destination) => {
    if (typeof value !== "string" || !value) return null;
    let parsed;
    try {
      parsed = new URL(value, window.location.origin);
    } catch {
      return null;
    }
    const isBase2026 = parsed.origin === window.location.origin
      || (parsed.protocol === "https:" && parsed.hostname === "base2026.dev");
    const isTikTok = parsed.protocol === "https:" && ["tiktok.com", "www.tiktok.com"].includes(parsed.hostname);
    if (!isBase2026 && !isTikTok) return null;
    const link = element("a", "", label);
    link.href = parsed.toString();
    link.dataset.destination = destination;
    if (!isBase2026) {
      link.target = "_blank";
      link.rel = "nofollow noopener noreferrer";
    }
    return link;
  };

  const numberValue = (value) => Number.isFinite(Number(value)) ? Number(value) : 0;
  const stringValue = (value) => typeof value === "string" ? value : "";

  const renderCoverage = (coverage) => {
    const list = element("dl", "b26-brief-coverage");
    const values = [
      ["Matched sources", numberValue(coverage?.matched_records)],
      ["Selected evidence", numberValue(coverage?.selected_sources)],
      ["Distinct creators", numberValue(coverage?.distinct_creators)],
      ["Newest source", stringValue(coverage?.published_date_max) || "Not available"],
    ];
    for (const [label, value] of values) {
      const item = element("div", "");
      item.append(element("dt", "", String(label)), element("dd", "", String(value)));
      list.append(item);
    }
    return list;
  };

  const renderFinding = (finding, index) => {
    const card = element("article", "b26-brief-finding");
    const meta = element("div", "b26-brief-finding__meta");
    meta.append(
      element("span", "", `${index + 1}. ${stringValue(finding.creator_handle) || "Attributed creator"}`),
      element("span", "", stringValue(finding.published_date) || "Date unavailable"),
    );
    card.append(meta, element("h3", "", stringValue(finding.claim) || "Public evidence finding"));
    card.append(element("blockquote", "", stringValue(finding.evidence_excerpt)));
    if (Array.isArray(finding.topics) && finding.topics.length) {
      const topics = element("div", "b26-brief-finding__topics");
      for (const topic of finding.topics.slice(0, 6)) {
        if (typeof topic === "string" && topic.trim()) topics.append(element("span", "", topic.trim()));
      }
      if (topics.childElementCount) card.append(topics);
    }
    const links = element("div", "b26-brief-finding__links");
    const recordLink = safeLink(finding.base2026_url, "Open Base2026 record", "base2026");
    const sourceLink = safeLink(finding.original_source_url, "Verify original source", "original");
    if (recordLink) links.append(recordLink);
    if (sourceLink) links.append(sourceLink);
    if (links.childElementCount) card.append(links);
    return card;
  };

  const buildCopyText = (payload) => {
    const lines = [`Base2026 Evidence Brief`, `Question: ${stringValue(payload.question)}`, ""];
    for (const [index, finding] of (Array.isArray(payload.findings) ? payload.findings : []).entries()) {
      lines.push(`${index + 1}. ${stringValue(finding.claim)}`);
      lines.push(`Evidence: ${stringValue(finding.evidence_excerpt)}`);
      lines.push(`Creator: ${stringValue(finding.creator_handle)}`);
      lines.push(`Base2026 record: ${stringValue(finding.base2026_url)}`);
      lines.push(`Source: ${stringValue(finding.original_source_url)}`);
      lines.push("");
    }
    for (const limit of Array.isArray(payload.limits) ? payload.limits : []) {
      if (typeof limit === "string") lines.push(`Limit: ${limit}`);
    }
    return lines.join("\n").trim();
  };

  const renderBrief = (payload) => {
    const findings = Array.isArray(payload.findings) ? payload.findings.slice(0, 5) : [];
    const briefStatus = stringValue(payload.status);
    title.textContent = stringValue(payload.question)
      ? `Evidence for: ${stringValue(payload.question)}`
      : "Source-backed findings";
    body.replaceChildren(renderCoverage(payload.coverage));
    if (briefStatus === "no_evidence" || findings.length === 0) {
      body.append(element("p", "b26-brief-empty", "Not enough public evidence in Base2026 for this question. Try a narrower term or browse the full evidence library."));
      status.textContent = "No eligible public finding matched this question.";
      copyButton.hidden = true;
    } else {
      const findingList = element("div", "b26-brief-findings");
      for (const [index, finding] of findings.entries()) findingList.append(renderFinding(finding, index));
      body.append(findingList);
      const repeatedSignals = Array.isArray(payload.repeated_signals) ? payload.repeated_signals : [];
      if (repeatedSignals.length) {
        const signals = element("section", "b26-brief-signals");
        signals.append(element("h3", "", "Repeated signals across creators"));
        const signalList = element("div", "b26-brief-finding__topics");
        for (const signal of repeatedSignals.slice(0, 6)) {
          const topic = stringValue(signal?.topic);
          if (topic) signalList.append(element("span", "", `${topic} · ${numberValue(signal?.distinct_creators)} creators`));
        }
        if (signalList.childElementCount) signals.append(signalList);
        body.append(signals);
      }
      const limits = element("div", "b26-brief-limits");
      for (const limit of Array.isArray(payload.limits) ? payload.limits : []) {
        if (typeof limit === "string" && limit.trim()) limits.append(element("p", "", limit.trim()));
      }
      if (limits.childElementCount) body.append(limits);
      const corpusVersion = stringValue(payload.corpus_version);
      const rankingVersion = stringValue(payload.ranking_version);
      if (corpusVersion || rankingVersion) {
        body.append(element("p", "b26-brief-receipt", [
          corpusVersion ? `Corpus ${corpusVersion}` : "",
          rankingVersion ? `retrieval ${rankingVersion}` : "",
        ].filter(Boolean).join(" · ")));
      }
      status.textContent = briefStatus === "limited"
        ? "Limited evidence: inspect the source before treating this as a repeated signal."
        : "Multiple attributable sources found in the current public corpus.";
      copyText = buildCopyText(payload);
      copyButton.hidden = !copyText;
    }
    result.ariaBusy = "false";
  };

  const loadBrief = async (question) => {
    result.hidden = false;
    result.ariaBusy = "true";
    status.textContent = "Searching the public evidence index…";
    body.replaceChildren();
    copyButton.hidden = true;
    result.scrollIntoView({ behavior: "smooth", block: "start" });
    try {
      const response = await fetch(`/api/evidence-brief/v2?q=${encodeURIComponent(question)}`, {
        headers: { Accept: "application/json" },
      });
      if (!response.ok) throw new Error(`Evidence Brief request failed with ${response.status}`);
      const payload = await response.json();
      if (!payload || typeof payload !== "object") throw new Error("Evidence Brief response is invalid");
      renderBrief(payload);
    } catch {
      result.ariaBusy = "false";
      status.textContent = "The evidence brief could not be loaded.";
      body.replaceChildren(element("p", "b26-brief-error", "The public evidence index is temporarily unavailable. Your question was not submitted anywhere else; use the Workspace to continue searching."));
    }
  };

  form.addEventListener("submit", (event) => {
    if (!form.reportValidity()) return;
    const question = input.value.normalize("NFKC").replace(/\s+/gu, " ").trim();
    if (question.length < 3) return;
    event.preventDefault();
    void loadBrief(question);
  });

  document.querySelectorAll(".b26-suggested-queries a").forEach((link) => {
    link.addEventListener("click", (event) => {
      if (!(link instanceof HTMLAnchorElement)) return;
      const question = new URL(link.href, window.location.origin).searchParams.get("q");
      if (!question) return;
      event.preventDefault();
      input.value = question;
      form.requestSubmit();
    });
  });

  copyButton.addEventListener("click", async () => {
    if (!copyText || !navigator.clipboard) return;
    try {
      await navigator.clipboard.writeText(copyText);
      copyButton.textContent = "Copied";
      window.setTimeout(() => { copyButton.textContent = "Copy brief"; }, 1800);
    } catch {
      copyButton.textContent = "Copy unavailable";
    }
  });

  resetButton.addEventListener("click", () => {
    input.focus();
    input.select();
    window.scrollTo({ top: Math.max(0, form.getBoundingClientRect().top + window.scrollY - 100), behavior: "smooth" });
  });
})();
