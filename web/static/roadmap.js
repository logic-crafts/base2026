const roadmapData = {
  statuses: ["Live", "Live, monitored", "Live foundation", "In progress", "Planned", "Research"],
  phases: [
    {
      id: "phase-1",
      label: "Phase 1",
      shortLabel: "Trust",
      title: "Public Trust Foundation",
      lane: "Foundation",
      status: "Live",
      purpose: "Keep the public project understandable and accountable while the database grows.",
      explanation: "The public layer has a live search workspace, source records, creator/topic pages, methodology, source policy, privacy notes, and correction/removal paths.",
      quarter: "Public layer",
      milestones: [
        { title: "Cloudflare public product", status: "Live" },
        { title: "D1 FTS5 search and source records", status: "Live" },
        { title: "Methodology and public roadmap", status: "Live" },
        { title: "Privacy and source policy", status: "Live" },
        { title: "Creator correction/removal path", status: "Live" },
        { title: "Public/private publication boundary", status: "Live" },
      ],
    },
    {
      id: "phase-2",
      label: "Phase 2",
      shortLabel: "Cloud pipeline",
      title: "Cloud Ingestion & Evidence Pipeline",
      lane: "Cloud",
      status: "Live, monitored",
      purpose: "Move bounded public sources through private evidence processing and strict public projection.",
      explanation: "Workers, D1, R2, Workers AI, Queues and Workflows operate the cloud pipeline. Ongoing work monitors source resilience, quality and budget efficiency.",
      quarter: "Cloud track",
      milestones: [
        { title: "Bounded Cloudflare discovery", status: "Live" },
        { title: "Private D1 dedupe and job state", status: "Live" },
        { title: "Private R2 media retention", status: "Live" },
        { title: "Workers AI transcription", status: "Live" },
        { title: "Queues and Workflows orchestration", status: "Live" },
        { title: "Receipt-gated public projection", status: "Live" },
        { title: "Source-platform resilience monitoring", status: "In progress" },
      ],
    },
    {
      id: "phase-3",
      label: "Phase 3",
      shortLabel: "Indexation",
      title: "Indexable Evidence Graph",
      lane: "Discovery",
      status: "Live, monitored",
      purpose: "Make the same public evidence discoverable to visitors, search engines and machines.",
      explanation: "Search, source/topic/creator pages, canonicals, sitemaps, structured data, dynamic projection pages and read-only API access are live. Google and Bing discovery are monitored.",
      quarter: "Discovery track",
      milestones: [
        { title: "D1 FTS5 search and filtering", status: "Live" },
        { title: "Source, topic and creator pages", status: "Live" },
        { title: "Canonical URLs and sitemaps", status: "Live" },
        { title: "Dynamic projection pages", status: "Live" },
        { title: "Google Search Console", status: "Live" },
        { title: "Bing Webmaster Tools", status: "Live" },
        { title: "Topic evidence maps", status: "In progress" },
      ],
    },
    {
      id: "phase-4",
      label: "Phase 4",
      shortLabel: "Rights",
      title: "Creator & Rights Controls",
      lane: "Now",
      status: "In progress",
      purpose: "Give creators and source owners a clear way to correct, update, remove, or claim materials.",
      explanation: "The public correction/removal page is live. Creator claims, automated request processing, and a public changelog are still planned.",
      quarter: "Trust track",
      milestones: [
        { title: "Creator claim workflow", status: "Planned" },
        { title: "Creator correction/removal page", status: "Live" },
        { title: "Automated request processing workflow", status: "Planned" },
        { title: "Public change log", status: "Planned" },
        { title: "Source dispute review process", status: "Research" },
      ],
    },
    {
      id: "phase-5",
      label: "Phase 5",
      shortLabel: "Distribution",
      title: "Developer & Research Distribution",
      lane: "Now",
      status: "Live foundation",
      purpose: "Make public-safe evidence reusable through stable human and machine interfaces.",
      explanation: "JSONL, a data dictionary, API index, llms.txt, D1 search API and GitHub source are live. Versioned samples, quickstarts and a read-only MCP contract remain in progress.",
      quarter: "Distribution track",
      milestones: [
        { title: "Public JSONL and data dictionary", status: "Live" },
        { title: "Read-only D1 search API", status: "Live" },
        { title: "llms.txt and API index", status: "Live" },
        { title: "GitHub source", status: "Live" },
        { title: "Versioned samples and quickstarts", status: "In progress" },
        { title: "Read-only MCP contract", status: "Planned" },
      ],
    },
    {
      id: "phase-6",
      label: "Phase 6",
      shortLabel: "Sustainability",
      title: "Sustainable Open Product",
      lane: "Later",
      status: "Research",
      purpose: "Test a sustainable operating model without weakening free access or source rights.",
      explanation: "Support, partnership and premium research ideas remain research until repeated public use provides evidence.",
      quarter: "Sustainability track",
      milestones: [
        { title: "Sponsorship / supporter model", status: "Research" },
        { title: "Premium research views", status: "Research" },
        { title: "Free public access boundary", status: "Live" },
        { title: "Partner and support paths", status: "Live" },
        { title: "Public revenue rules", status: "Planned" },
        { title: "Transparent commercial policy", status: "Planned" },
      ],
    },
  ],
  priorities: {
    Now: [
      { title: "Monitor Google and Bing discovery", status: "In progress" },
      { title: "Synchronize counters and D1 projections", status: "In progress" },
      { title: "Release-test canonicals and sitemaps", status: "In progress" },
    ],
    Next: [
      { title: "10–15 source-backed topic evidence maps", status: "In progress" },
      { title: "Versioned public dataset sample", status: "Planned" },
      { title: "API quickstart and corpus changelog", status: "Planned" },
      { title: "Creator claim and correction tracking", status: "Planned" },
    ],
    Later: [
      { title: "Read-only MCP contract", status: "Planned" },
      { title: "Citation-aware answers with sources", status: "Research" },
      { title: "Carefully reviewed source expansion", status: "Research" },
      { title: "Sustainability experiments", status: "Research" },
    ],
  },
  fundingTargets: [
    {
      title: "Trustworthy public layer",
      status: "Live",
      text: "Keep the public product accountable with source pages, policy pages, and correction paths.",
      items: ["Attribution", "Policies", "Opt-out/corrections", "Public roadmap"],
    },
    {
      title: "Reliable cloud pipeline",
      status: "Live, monitored",
      text: "Keep bounded discovery, evidence processing and automatic projection replay-safe and observable.",
      items: ["Workers", "D1 and R2", "Workers AI", "Queues and Workflows"],
    },
    {
      title: "Indexable distribution",
      status: "In progress",
      text: "Turn strong source evidence into discoverable pages and stable machine access.",
      items: ["Evidence maps", "Indexation monitoring", "API samples", "Creator controls"],
    },
  ],
};

let activePhaseId = roadmapData.phases[0].id;

function esc(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function statusSlug(status) {
  return String(status || "planned").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}

function statusLabel(status) {
  const raw = String(status || "Planned").trim();
  const normalized = raw.toLowerCase();
  if (normalized.includes("completed")) return "Done";
  if (normalized === "live, monitored") return "Live, monitored";
  if (normalized === "live foundation") return "Live foundation";
  if (normalized === "in progress") return "In progress";
  if (normalized === "research") return "Research";
  if (normalized === "planned") return "Planned";
  if (normalized === "live") return "Live";
  if (normalized === "next") return "Next";
  return raw;
}

function statusBadge(status) {
  const fullStatus = String(status || "Planned").trim();
  const label = statusLabel(fullStatus);
  return `<span class="status-badge status-${statusSlug(fullStatus)}" title="${esc(fullStatus)}" aria-label="Status: ${esc(fullStatus)}">${esc(label)}</span>`;
}

function list(items, limit = items.length) {
  return `<ul class="mini-list">${items.slice(0, limit).map((item) => `<li>${esc(item)}</li>`).join("")}</ul>`;
}

function renderMilestones(milestones) {
  return `<div class="milestone-grid">${milestones.map((milestone) => `
    <article class="milestone-card">
      <div class="milestone-card__head">
        <h3>${esc(milestone.title)}</h3>
        ${statusBadge(milestone.status)}
      </div>
    </article>`).join("")}</div>`;
}

function getActivePhase() {
  return roadmapData.phases.find((phase) => phase.id === activePhaseId) || roadmapData.phases[0];
}

function renderTabs() {
  const target = document.querySelector("#phase-tabs");
  if (!target) return;
  target.innerHTML = roadmapData.phases
    .map((phase) => `
      <button class="phase-tab ${phase.id === activePhaseId ? "is-active" : ""}" type="button" data-phase="${phase.id}" aria-pressed="${phase.id === activePhaseId ? "true" : "false"}">
        <span>${esc(phase.label)}</span>
        <strong>${esc(phase.shortLabel)}</strong>
        <small>${esc(phase.status)} · ${phase.milestones.length} milestones</small>
      </button>`)
    .join("");
  target.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      activePhaseId = button.dataset.phase;
      renderAll();
    });
  });
}

function renderFlow() {
  const target = document.querySelector("#roadmap-flow");
  if (!target) return;
  target.innerHTML = `
    <div class="phase-sequence" role="list" aria-label="Roadmap phase sequence">
      ${roadmapData.phases.map((phase, index) => `
        <button class="sequence-step ${phase.id === activePhaseId ? "is-active" : ""}" type="button" data-phase="${phase.id}" role="listitem" aria-pressed="${phase.id === activePhaseId ? "true" : "false"}">
          <span class="sequence-step__number">${String(index + 1).padStart(2, "0")}</span>
          <span class="sequence-step__body">
            <strong>${esc(phase.title)}</strong>
            <em>${esc(phase.lane)} · ${esc(phase.status)}</em>
            <small>${esc(phase.purpose)}</small>
          </span>
        </button>
      `).join("")}
    </div>`;
  target.querySelectorAll(".sequence-step").forEach((node) => {
    node.addEventListener("click", () => {
      activePhaseId = node.dataset.phase;
      renderAll();
    });
  });
}

function renderDetail() {
  const target = document.querySelector("#phase-detail");
  if (!target) return;
  const phase = getActivePhase();
  target.innerHTML = `
    <div class="phase-detail-card">
      <div class="detail-meta">
        <span class="pill pill-accent">${esc(phase.label)}</span>
        <span class="pill">${esc(phase.quarter)}</span>
        ${statusBadge(phase.status)}
      </div>
      <h2 class="phase-name">${esc(phase.title)}</h2>
      <p class="phase-purpose">${esc(phase.purpose)}</p>
      <p>${esc(phase.explanation)}</p>
      <h3>Milestones</h3>
      ${renderMilestones(phase.milestones)}
    </div>`;
}

function renderWorkload() {
  const target = document.querySelector("#workload-chart");
  if (!target) return;
  const max = Math.max(...roadmapData.phases.map((phase) => phase.milestones.length));
  target.innerHTML = roadmapData.phases.map((phase) => {
    const value = phase.milestones.length;
    return `<button class="bar-row ${phase.id === activePhaseId ? "is-active" : ""}" type="button" data-phase="${phase.id}">
      <span class="bar-label">${esc(phase.label)}</span>
      <span class="bar-track"><span class="bar-fill" style="width:${Math.round((value / max) * 100)}%"></span></span>
      <span class="bar-value">${value}</span>
    </button>`;
  }).join("");
  target.querySelectorAll(".bar-row").forEach((row) => {
    row.addEventListener("click", () => {
      activePhaseId = row.dataset.phase;
      renderAll();
    });
  });
}

function renderFunding() {
  const target = document.querySelector("#funding-grid");
  if (!target) return;
  target.innerHTML = roadmapData.fundingTargets.map((item) => `
    <article class="funding-card">
      ${statusBadge(item.status)}
      <h3>${esc(item.title)}</h3>
      <p>${esc(item.text)}</p>
      ${list(item.items)}
    </article>`).join("");
}

function renderPriorities() {
  const target = document.querySelector("#priority-stack");
  if (!target) return;
  target.innerHTML = Object.entries(roadmapData.priorities).map(([title, items]) => `
    <article class="priority-column">
      <span class="pill">${items.length} layers</span>
      <h3>${esc(title)}</h3>
      <ul class="mini-list priority-list">
        ${items.map((item) => `<li><span>${esc(item.title)}</span>${statusBadge(item.status)}</li>`).join("")}
      </ul>
    </article>`).join("");
}

function renderAll() {
  renderTabs();
  renderFlow();
  renderDetail();
  renderWorkload();
  renderFunding();
  renderPriorities();
  document.body.classList.add("roadmap-enhanced");
}

document.addEventListener("DOMContentLoaded", renderAll);
