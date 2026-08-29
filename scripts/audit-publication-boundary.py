from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


FORBIDDEN_PREFIXES = {
    ".github/workflows/",
    ".planning/",
    ".playwright-mcp/",
    ".github/workflows/",
    "00_sources/",
    "01_core-methodology/",
    "02_factor-maps/",
    "03_sops/",
    "04_checklists/",
    "05_templates/",
    "06_prompt-bank/",
    "07_client-workspaces/",
    "08_experiments/",
    "09_sales-packaging/",
    "11_dreamwood_offer/",
    "12_knowledge-base/indexes/",
    "12_knowledge-base/sources/",
    "12_knowledge-base/canonical/",
    "12_knowledge-base/reports/",
    "99_original_research/",
    "meili_data/",
    "output/",
    "public-data/",
    "tests/fixtures/public-export-auto-promote/",
}

GENERATED_STATIC_PREFIXES = {
    "web/static/compare/",
    "web/static/creators/",
    "web/static/sitemaps/",
    "web/static/sources/",
    "web/static/topics/",
}

GENERATED_STATIC_EXACT = {
    "web/static/analytics_summary.json",
    "web/static/base2026_analytics.json",
    "web/static/sitemap.xml",
    "web/static/topic_signal_briefs.jsonl",
}

FORBIDDEN_EXACT = {"manifest.json", ".github/dependabot.yml", *GENERATED_STATIC_EXACT}

FORBIDDEN_PATTERNS = [
    re.compile(r"^\.env(?:\.|$)"),
    re.compile(r"^audio_.*\.ogg$"),
    re.compile(r"^base2026-.*\.(?:png|md)$"),
    re.compile(r"^config/(?:tiktok-intake-queue|release-target).*\.json$"),
    re.compile(r"^\.github/dependabot\.ya?ml$"),
    re.compile(r".*\.(?:log|zip)$"),
]

PUBLIC_SAFE_PREFIXES = {
    ".github/ISSUE_TEMPLATE/",
    "10_agent-instructions/",
    "cloudflare/base2026-worker/",
    "cloudflare/base2026-www-redirect/",
    "contracts/",
    "docs/",
    "static/brand/",
    "templates/base2026-",
    "tests/fixtures/public-export-leaky/",
    "tests/fixtures/public-export-valid/",
}

PUBLIC_SAFE_EXACT = {
    ".env.example",
    ".gitignore",
    ".agents/product-marketing.md",
    "AGENTS.md",
    "README.md",
    "ROADMAP.md",
    "CHANGELOG.md",
    "GOVERNANCE.md",
    "requirements-local-worker.txt",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "LICENSE",
    "LICENSE.md",
    ".github/pull_request_template.md",
    ".github/FUNDING.yml",
    "config/creator-profiles.json",
    "config/creators.example.json",
    "data/ai_visibility_pages_batch01.json",
    "data/ai_visibility_pages_bing_batch02.json",
    "data/ai_visibility_pages_bing_batch04.json",
    "data/ai_visibility_pages_master.json",
    "data/base2026_ai_recommends_solutions_pilot.json",
    "data/base2026_topic_traffic_pages.json",
    "examples/base2026-public-dataset-catalog.json",
    "examples/query_public_evidence.py",
    "scripts/apply-base2026-editorial-decisions.py",
    "scripts/apply-license.ps1",
    "scripts/base2026-apply-chatgpt-review.py",
    "scripts/base2026-build-chatgpt-review-packet.py",
    "scripts/base2026-check-insight-batch.py",
    "scripts/base2026-generate-rule-insight-batch.py",
    "scripts/base2026-run-rule-insight-batches.py",
    "scripts/base2026-solution-backlog-portfolio.py",
    "scripts/base2026-tiktok-pipeline-v2.py",
    "scripts/base2026-tiktok-repair-queue.py",
    "scripts/base2026_ai_recommends_core.py",
    "scripts/audit-publication-boundary.py",
    "scripts/build-base2026-cloudflare-release.py",
    "scripts/check-cloudflare-public-artifact-policy.py",
    "scripts/check-base2026-design-authority.py",
    "scripts/base2026-build-backfill-queue.py",
    "scripts/base2026-claim-extract-local.py",
    "scripts/base2026-controller.py",
    "scripts/base2026-daily-digest.py",
    "scripts/base2026-evidence-verify.py",
    "scripts/base2026-import-claim-candidates.py",
    "scripts/base2026-prepare-needs-human-review.py",
    "scripts/base2026-promote-insight-candidates.py",
    "scripts/base2026-resolve-candidate-decisions.py",
    "scripts/base2026-release-gate.ps1",
    "scripts/base2026-review-legacy-insights.py",
    "scripts/base2026-review-insight-candidates.py",
    "scripts/check-public-export-policy.py",
    "scripts/check-public-content-readiness.py",
    "scripts/deploy-public-vps.ps1",
    "scripts/export-public-tiktok.py",
    "scripts/fetch-tiktok-avatars.py",
    "scripts/generate-base2026-sitemap.py",
    "scripts/generate-base2026-analytics.py",
    "scripts/generate-public-analytics.py",
    "scripts/generate-topic-signal-briefs.py",
    "scripts/generate-public-pages.py",
    "scripts/generate-info-pages.py",
    "scripts/generate-ai-visibility-pages.py",
    "scripts/generate-ai-recommends-solutions.py",
    "scripts/alex_v4_static_shell.py",
    "scripts/base2026_source_detail_v2.css",
    "scripts/base2026_source_detail_v2.js",
    "scripts/build-source-detail-v2-full-candidate.py",
    "scripts/template_migration/__init__.py",
    "scripts/template_migration/jinja_env.py",
    "scripts/template_migration/source_detail.py",
    "scripts/template_migration/templates/base_page.html.j2",
    "scripts/template_migration/templates/families/source_detail.html.j2",
    "scripts/template_migration/templates/macros/platform_actions.html.j2",
    "scripts/validate-source-detail-v2-full-candidate.py",
    "templates/shared/alex-home-v4-footer.html",
    "requirements-template-migration.txt",
    "scripts/generate-alex-base2026-native-site.py",
    "scripts/generate-alex-static-site.py",
    "scripts/hermes-tiktok-refresh.ps1",
    "scripts/import-social-discovery-to-tiktok-csv.py",
    "scripts/live-seo-crawl-gate.mjs",
    "scripts/meili-index-public.py",
    "scripts/mobile-visual-qa.mjs",
    "scripts/package-public-hotfix-from-export.ps1",
    "scripts/package-public-release.ps1",
    "scripts/preflight-github-launch.ps1",
    "scripts/prepare-indexnow-payload.py",
    "scripts/public_manifest_contract.py",
    "scripts/register-hermes-tiktok-check-task.ps1",
    "scripts/run-hermes-polish-worker.ps1",
    "scripts/server-patch-nginx-base2026.py",
    "scripts/social-discover.py",
    "scripts/stage-public-files.ps1",
    "scripts/tiktok-backfill-inventory.ps1",
    "scripts/base2026-worker.py",
    "scripts/build-kb-sqlite.py",
    "scripts/import-tiktok-staging-to-kb.py",
    "scripts/kb-audit.py",
    "scripts/tiktok-polish-runner.ps1",
    "scripts/tiktok-polish-audit.py",
    "scripts/tiktok-qa-triage.py",
    "scripts/tiktok-qa-review-apply.py",
    "scripts/tiktok-caption-browser-extract.mjs",
    "scripts/tiktok-clear-reviewed-source-rows.py",
    "scripts/tiktok-apply-qa-gates.py",
    "scripts/tiktok-faithful-polish-local.py",
    "scripts/tiktok-normalize-polished-entities.py",
    "scripts/tiktok-polish-status.py",
    "scripts/tiktok-process-transcripts.ps1",
    "scripts/tiktok-source-review-audit.py",
    "scripts/tiktok-source-review-queue.py",
    "scripts/tiktok-ytdlp-metadata-extract.py",
    "scripts/validate-public-release-contract.py",
    "scripts/validate-ai-recommends-html.py",
    "scripts/validate-ai-recommends-solutions.py",
    "scripts/repair-public-text-excerpts.py",
    "scripts/validate-public-text-excerpts.py",
    "scripts/validate-github-metadata.py",
    "tests/test_ai_recommends_solutions.py",
    "tests/test_apply_base2026_editorial_decisions.py",
    "tests/test_base2026_apply_chatgpt_review.py",
    "tests/test_base2026_apply_chatgpt_transcript_status.py",
    "tests/test_base2026_pipeline_controller.py",
    "tests/test_base2026_review_insight_candidates.py",
    "tests/test_base2026_solution_backlog_portfolio.py",
    "tests/test_base2026_tiktok_pipeline_v2.py",
    "tests/test_base2026_tiktok_repair_queue.py",
    "tests/test_build_kb_reviewed_candidate_replay.py",
    "tests/test_build_base2026_cloudflare_release.py",
    "tests/test_base2026_homepage_motion.py",
    "tests/test_base2026_live_stats.py",
    "tests/test_base2026_public_dataset.py",
    "tests/test_base2026_roadmap.py",
    "tests/test_base2026_journal_article.py",
    "tests/test_cloudflare_public_artifact_policy.py",
    "tests/test_base2026_design_authority.py",
    "tests/test_check_public_content_readiness.py",
    "tests/test_export_public_tiktok_admission.py",
    "tests/test_generate_public_pages_indexability.py",
    "tests/test_generate_info_pages.py",
    "tests/test_hermes_tiktok_refresh_atomicity.py",
    "tests/test_public_dataset_manifest_contract.py",
    "tests/test_tiktok_faithful_polish_local.py",
    "web/ARCHITECTURE.md",
    "web/KNOWLEDGE_UI_GUIDE.md",
    "web/README.md",
    "web/UI_AUDIT.md",
    "web/server.py",
    "static/base2026-mark.svg",
    "static/assets/alex-yarosh-founder-step-wall.webp",
    # Reviewed operational/build assets. They are source code or templates only;
    # the audit still scans them for secrets and never treats source data as safe.
    "requirements-base2026-cloud-transcription.txt",
    "scripts/alex-personal-shell-v1.css",
    "scripts/base2026-groq-video-intake.py",
    "scripts/base2026-apply-chatgpt-transcript-status.py",
    "scripts/base2026-apply-media-stage-status.py",
    "scripts/base2026-pipeline-controller.py",
    "scripts/base2026-import-chatgpt-production-packet.py",
    "scripts/base2026-normalize-chatgpt-json.py",
    "scripts/base2026-refresh-public-export.py",
    "scripts/base2026-select-queue-batch.py",
    "scripts/base2026-stage-tiktok-media.py",
    "scripts/base2026-store-chatgpt-stage-output.py",
    "scripts/base2026_detail_v4.css",
    "scripts/base2026_search_v1.css",
    "scripts/base2026_search_v3.js",
    "scripts/build-source-detail-canary-selection.py",
    "scripts/build-template-migration-inventory.py",
    "scripts/generate-base2026-detail-v4-pilot.py",
    "scripts/generate-base2026-search-v1.py",
    "scripts/generate-base2026-source-detail-v2.py",
    "scripts/materialize-legacy-public-aliases.py",
    "scripts/normalize-wordpress-v4-shell-release.py",
    "scripts/render-base2026-template-canary.py",
    "scripts/restore-wordpress-v4-footer-release.py",
    "scripts/template_migration/contracts.py",
    "scripts/template_migration/inventory.py",
    "scripts/tiktok-create-polish-batches.ps1",
    "scripts/wordpress-v4-footer.css",
    "scripts/wordpress-v4-header.css",
    "templates/shared/alex-home-v4-header.html",
}

SECRET_PATTERNS = [
    ("private_key", re.compile(r"-----BEGIN (?:OPENSSH|RSA|EC|DSA)? ?PRIVATE KEY-----")),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("bearer_token", re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]{20,}")),
    ("tavily_key", re.compile(r"\btvly-[A-Za-z0-9_-]{20,}\b")),
    ("v0_key", re.compile(r"\bv1:[A-Za-z0-9_-]{10,}:[A-Za-z0-9_-]{20,}\b")),
]


@dataclass
class Finding:
    path: str
    reason: str


def run_git(args: list[str]) -> list[str]:
    raw = subprocess.check_output(
        ["git", *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stderr=subprocess.DEVNULL,
    )
    return [line.strip() for line in raw.splitlines() if line.strip()]


def normalize(path: str) -> str:
    normalized = path.replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def changed_files() -> list[str]:
    staged = run_git(["diff", "--cached", "--name-only"])
    modified = run_git(["diff", "--name-only"])
    untracked = run_git(["ls-files", "--others", "--exclude-standard"])
    return sorted({normalize(path) for path in [*staged, *modified, *untracked]})


def staged_deletions() -> set[str]:
    deleted: set[str] = set()
    for line in run_git(["diff", "--cached", "--name-status"]):
        if not line.startswith("D\t"):
            continue
        deleted.add(normalize(line.split("\t", 1)[1]))
    return deleted


def is_generated_static_artifact(path: str) -> bool:
    return path in GENERATED_STATIC_EXACT or any(path.startswith(prefix) for prefix in GENERATED_STATIC_PREFIXES)


def is_forbidden(path: str) -> str | None:
    if path == ".env.example":
        return None
    if path in FORBIDDEN_EXACT:
        return "forbidden exact path"
    if any(path.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
        return "forbidden private/generated directory"
    if any(path.startswith(prefix) for prefix in GENERATED_STATIC_PREFIXES):
        return "forbidden generated static artifact"
    for pattern in FORBIDDEN_PATTERNS:
        if pattern.match(path):
            return "forbidden private/generated pattern"
    return None


def is_public_safe_candidate(path: str) -> bool:
    if path in PUBLIC_SAFE_EXACT:
        return True
    if path.startswith("web/static/") and not is_generated_static_artifact(path):
        return True
    return any(path.startswith(prefix) for prefix in PUBLIC_SAFE_PREFIXES)


def scan_file(path: str) -> list[Finding]:
    full_path = ROOT / path
    findings: list[Finding] = []
    if not full_path.exists() or not full_path.is_file():
        return findings
    try:
        text = full_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        findings.append(Finding(path, f"unable to read file: {exc}"))
        return findings
    for label, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            findings.append(Finding(path, f"possible secret pattern: {label}"))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Base2026 changed files before public GitHub staging.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of human-readable text.")
    args = parser.parse_args()

    files = changed_files()
    forbidden: list[Finding] = []
    needs_review: list[str] = []
    public_safe: list[str] = []
    secret_findings: list[Finding] = []
    index_cleanup = staged_deletions()

    for path in files:
        generated_index_cleanup = path in index_cleanup and is_generated_static_artifact(path)
        reason = is_forbidden(path)
        if reason:
            if generated_index_cleanup:
                public_safe.append(path)
                continue
            forbidden.append(Finding(path, reason))
            continue
        if is_public_safe_candidate(path):
            public_safe.append(path)
            if not generated_index_cleanup:
                secret_findings.extend(scan_file(path))
        else:
            needs_review.append(path)

    report = {
        "changed_files": len(files),
        "public_safe_candidates": len(public_safe),
        "public_safe_files": public_safe,
        "needs_review": needs_review,
        "forbidden": [finding.__dict__ for finding in forbidden],
        "secret_findings": [finding.__dict__ for finding in secret_findings],
        "ok_to_stage_public_safe_candidates": not forbidden and not secret_findings and not needs_review,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"changed_files={report['changed_files']}")
        print(f"public_safe_candidates={report['public_safe_candidates']}")
        print(f"needs_review={len(needs_review)}")
        print(f"forbidden={len(forbidden)}")
        print(f"secret_findings={len(secret_findings)}")
        print(f"ok_to_stage_public_safe_candidates={str(report['ok_to_stage_public_safe_candidates']).lower()}")
        if needs_review:
            print("needs_review_paths=" + ",".join(needs_review[:12]))
        if forbidden:
            print("forbidden_paths=" + ",".join(item.path for item in forbidden[:12]))
        if secret_findings:
            print("secret_paths=" + ",".join(item.path for item in secret_findings[:12]))

    return 0 if report["ok_to_stage_public_safe_candidates"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
