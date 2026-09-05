(() => {
  "use strict";
  const root = document.querySelector("[data-page-readiness]");
  if (!root) return;
  const find = (selector) => root.querySelector(selector);
  const form = find("[data-check-form]"), source = find("[data-html]"), url = find("[data-url]");
  const file = find("[data-file]"), submit = find("[data-submit]"), status = find("[data-status]");
  const results = find("[data-results]");
  const encoder = new TextEncoder();
  let previous = null, controller = null, revision = 0;
  const example = (fixed) => `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>${fixed ? "Boiler servicing in Bristol | Example Heating" : ""}</title>
  <link rel="canonical" href="https://example.com/boiler-servicing">
</head>
<body>
  <h1>Boiler servicing in Bristol</h1>
  <p>Arrange an annual service with our local heating team.</p>
  <a href="/contact">Ask about a boiler service</a>
</body>
</html>`;
  const labels = { title: "Page title", h1: "Main heading", robots: "Robots meta", canonical: "Canonical", links: "HTML links", jsonld: "Structured data syntax", network: "Live page state" };
  const states = { observed: "Observed", review: "Review", unknown: "Unknown" };
  const line = (parent, text, tag = "p") => { const node = document.createElement(tag); node.textContent = text; parent.append(node); return node; };
  const invalidate = () => { revision++; controller?.abort(); results.hidden = true; status.textContent = "Source changed. Check it to see updated observations."; };
  source.addEventListener("input", invalidate);
  url.addEventListener("input", invalidate);
  for (const [selector, fixed] of [["[data-example]", false], ["[data-fixed]", true]]) {
    find(selector).addEventListener("click", () => {
      invalidate(); source.value = example(fixed); url.value = "https://example.com/boiler-servicing"; file.value = "";
      status.textContent = `${fixed ? "Corrected" : "Original"} fictional example loaded. You can edit it before checking.`;
      source.focus();
    });
  }
  file.addEventListener("change", async () => {
    invalidate(); const ticket = revision; const selected = file.files?.[0];
    source.value = "";
    if (!selected) return;
    if (selected.size > 256 * 1024) { status.textContent = "File exceeds 256 KiB. Use a complete smaller public page, not a truncated file."; return; }
    try {
      const text = await selected.text();
      if (ticket !== revision) return;
      source.value = text; status.textContent = "File loaded into the editor. Review it, then choose Check to send it for analysis.";
    } catch { if (ticket === revision) status.textContent = "File could not be read. Try pasting the public source."; }
  });
  find("[data-clear]").addEventListener("click", () => {
    invalidate(); previous = null; source.value = ""; url.value = ""; file.value = "";
    find("[data-checks]").replaceChildren(); find("[data-next]").replaceChildren();
    find("[data-provenance]").textContent = ""; find("[data-comparison]").textContent = "";
    status.textContent = "Source and results cleared from this tab.";
  });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (controller) return;
    if (encoder.encode(source.value).length > 256 * 1024) { status.textContent = "HTML exceeds 256 KiB. A partial source check would be incomplete."; return; }
    const body = JSON.stringify({ html: source.value, ...(url.value.trim() ? { url: url.value.trim() } : {}) });
    if (encoder.encode(body).length > 320 * 1024) { status.textContent = "Encoded request exceeds 320 KiB. Use a complete smaller public page."; return; }
    const context = url.value.trim(); const ticket = revision;
    controller = new AbortController(); const timer = setTimeout(() => controller?.abort(), 7000);
    submit.disabled = true; results.hidden = true; status.textContent = "Checking supplied HTML…";
    try {
      const response = await fetch("/api/page-readiness/v1", { method: "POST", headers: { "Content-Type": "application/json" }, credentials: "omit", cache: "no-store", referrerPolicy: "no-referrer", body, signal: controller.signal });
      const result = await response.json();
      if (ticket !== revision) return;
      if (!response.ok || result.state !== "observed") { status.textContent = `Unknown — ${result.message || "The source could not be checked. Try again."}`; return; }
      find("[data-provenance]").textContent = `${result.provenance} Checked ${new Date(result.checkedAt).toLocaleString()}.${result.facts.textClipped ? " Displayed metadata text is shortened to 512 characters; inspect the full source before interpreting directives." : ""}`;
      const comparable = previous && previous.context === context;
      const changed = comparable ? result.checks.filter((check) => { const old = previous.checks.find((item) => item.id === check.id); return old?.observation !== check.observation || old?.state !== check.state; }).map((check) => labels[check.id]) : [];
      find("[data-comparison]").textContent = comparable ? (changed.length ? `Changed since the last source check: ${changed.join(", ")}. This is a source comparison, not verification of a live change.` : "No observed change since the last source check in this tab.") : "First check for this URL context. Supply fresh source after a correction to compare.";
      previous = { context, checks: result.checks };
      const next = find("[data-next]"); next.replaceChildren();
      const priority = result.checks.find((check) => check.state === "review");
      line(next, priority ? `Start here: ${labels[priority.id]}` : "Next: verify this against your live page", "h3");
      line(next, priority ? priority.action : "Review the title and content for accuracy, then verify the public response and crawler controls separately. Observed source elements are not a page-wide pass.");
      const checks = find("[data-checks]"); checks.replaceChildren();
      for (const check of result.checks) {
        const section = document.createElement("section"); section.className = "b26-page-readiness__finding"; section.dataset.state = check.state;
        line(section, `${labels[check.id]} · ${states[check.state]}`, "h3");
        for (const [label, value] of [["Observed", check.observation], ["Why it matters", check.why], ["Next action", check.action], ["Repeat check", check.recheck]]) line(section, `${label}: ${value}`);
        if (check.id === "robots" && result.facts.robots.length) line(section, result.facts.robots.map((item) => `${item.agent}: ${item.content}`).join("\n"), "pre");
        if (check.id === "canonical" && result.facts.canonical.length) line(section, result.facts.canonical.join("\n"), "pre");
        checks.append(section);
      }
      results.hidden = false; status.textContent = "Source checked. Live network and indexing facts remain unknown."; results.focus({ preventScroll: true }); results.scrollIntoView({ block: "start" });
    } catch { if (ticket === revision) status.textContent = "Unknown — the check timed out or could not be reached. Try again. This does not mean the page is bad."; }
    finally { clearTimeout(timer); controller = null; submit.disabled = false; }
  });
  submit.disabled = false;
})();
