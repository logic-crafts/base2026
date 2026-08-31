/* Optional tab-only decision record. No requests, persistence or input analytics.
   The server-rendered guide and empty printable fields also work without JS. */
(() => {
  "use strict";
  const decisions = Object.freeze({ add: "Add a link", context: "Improve its context", repair: "Repair an existing link", "no-change": "Make no change" });
  const keys = ["target", "source", "decision", "rationale", "verification"];

  // Quoting handles delimiters/newlines; the apostrophe also stops spreadsheet
  // formulas, including formulas preceded by whitespace or control characters.
  function csvCell(value) {
    const text = String(value);
    const safe = /^[\s\u0000-\u001f\u007f-\u009f]*[=+@-]/u.test(text) ? "'" + text : text;
    return '"' + safe.replace(/"/gu, '""') + '"';
  }

  document.querySelectorAll("[data-b26-guide-decision]").forEach((root) => {
    const fields = Object.fromEntries(keys.map((key) => [key, root.querySelector("#b26-guide-" + key)]));
    const copy = root.querySelector("[data-guide-copy]");
    const download = root.querySelector("[data-guide-download]");
    const status = root.querySelector("[data-guide-status]");
    const printable = root.querySelector("[data-guide-print]");
    const outputs = Object.fromEntries(keys.map((key) => [key, root.querySelector("[data-print-" + key + "]")]));
    if (!copy || !download || !status || !printable || keys.some((key) => !fields[key] || !outputs[key])) return;

    function values() {
      return Object.fromEntries(keys.map((key) => [key, fields[key].value.trim()]));
    }

    function updatePrint() {
      const record = values();
      keys.forEach((key) => { outputs[key].textContent = key === "decision" ? (decisions[record[key]] || "Not selected") : (record[key] || "Not entered"); });
    }

    function error(field, message) {
      field.setAttribute("aria-invalid", "true");
      status.textContent = message;
      field.focus();
      return null;
    }

    function checkedRecord() {
      keys.forEach((key) => fields[key].removeAttribute("aria-invalid"));
      const record = values();
      for (const key of ["target", "source"]) {
        try {
          const url = new URL(record[key]);
          if (record[key].length > 2048 || !["https:", "http:"].includes(url.protocol) || url.username || url.password) throw new Error("URL");
        } catch {
          return error(fields[key], "Enter a complete http or https " + (key === "target" ? "target" : "source") + " URL without sign-in details. It will not be visited.");
        }
      }
      if (!Object.hasOwn(decisions, record.decision)) return error(fields.decision, "Choose a decision before copying or downloading.");
      for (const key of ["rationale", "verification"]) {
        if (!record[key] || record[key].length > 1600) return error(fields[key], "Add " + key + " in 1–1600 characters. You can explicitly record what is still unknown.");
      }
      return record;
    }

    function context() {
      return [root.dataset.guideUrl, root.dataset.guideRevision, root.dataset.guideUpdated];
    }

    copy.addEventListener("click", () => {
      void (async () => {
        const record = checkedRecord();
        if (!record) return;
        const [url, revision, updated] = context();
        const text = ["Base2026 decision record", "Guide: " + url, "Guide revision: " + revision, "Guide updated: " + updated,
          "", "Target URL: " + record.target, "Proposed source URL: " + record.source, "Decision: " + decisions[record.decision],
          "Rationale: " + record.rationale, "Verification: " + record.verification].join("\n");
        copy.disabled = true;
        try {
          if (!navigator.clipboard || typeof navigator.clipboard.writeText !== "function") throw new Error("Clipboard unavailable");
          await navigator.clipboard.writeText(text);
          status.textContent = "Record copied. Your entries have not been sent to Base2026.";
        } catch {
          status.textContent = "Clipboard access is unavailable or denied. Copy the fields manually, or use Download CSV.";
        } finally { copy.disabled = false; }
      })();
    });

    download.addEventListener("click", () => {
      const record = checkedRecord();
      if (!record) return;
      let objectUrl;
      let link;
      try {
        const csv = [
          ["guide_url", "guide_revision", "guide_updated_at", "target_url", "proposed_source_url", "decision", "rationale", "verification"],
          [...context(), record.target, record.source, decisions[record.decision], record.rationale, record.verification],
        ].map((row) => row.map(csvCell).join(",")).join("\r\n") + "\r\n";
        objectUrl = URL.createObjectURL(new Blob(["\ufeff", csv], { type: "text/csv;charset=utf-8" }));
        link = document.createElement("a");
        link.href = objectUrl;
        link.download = "base2026-decision-record.csv";
        document.body.appendChild(link);
        link.click();
        status.textContent = "CSV download requested. Your entries have not been sent to Base2026.";
      } catch {
        status.textContent = "The CSV could not be created. Copy the record or print this page instead.";
      } finally {
        if (link) link.remove();
        if (objectUrl) setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
      }
    });

    keys.forEach((key) => {
      const changed = () => {
        fields[key].removeAttribute("aria-invalid");
        status.textContent = "";
        updatePrint();
      };
      fields[key].addEventListener("input", changed);
      fields[key].addEventListener("change", changed);
    });
    root.dataset.guideEnhanced = "true";
    printable.hidden = false;
    copy.hidden = false;
    download.hidden = false;
    updatePrint();
  });
})();
