from __future__ import annotations

import re
import subprocess
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "base2026-my-research.html"
SCRIPT = ROOT / "templates" / "base2026-members.js"
STYLES = ROOT / "templates" / "base2026-members.css"
HEADER = ROOT / "templates" / "base2026-startup-header.html"


def test_shared_header_exposes_sign_in_without_gating_public_search() -> None:
    soup = BeautifulSoup(HEADER.read_text(encoding="utf-8"), "html.parser")

    desktop = soup.select_one('nav[aria-label="Primary navigation"]')
    mobile = soup.select_one('nav[aria-label="Mobile navigation"]')
    assert desktop is not None
    assert mobile is not None
    assert desktop.select_one('a[href="/workspace/"]') is not None
    assert mobile.select_one('a[href="/workspace/"]') is not None
    desktop_account = desktop.select_one('a[href="/my-research/"][data-members-account-link]')
    mobile_account = mobile.select_one('a[href="/my-research/"][data-members-account-link]')
    assert desktop_account is not None
    assert mobile_account is not None
    assert desktop_account.get_text(strip=True) == "Sign in"
    assert mobile_account.get_text(strip=True) == "Sign in"


def test_my_research_template_is_private_and_uses_the_shared_shell() -> None:
    source = TEMPLATE.read_text(encoding="utf-8")
    soup = BeautifulSoup(source, "html.parser")

    assert soup.select_one('meta[name="robots"]')['content'] == "noindex,nofollow"
    assert source.count("{{STARTUP_HEADER}}") == 1
    assert source.count("{{STARTUP_FOOTER}}") == 1
    assert soup.select_one('main[data-members-page]#main-content[tabindex="-1"]') is not None
    assert soup.select_one('nav[aria-label="Research workspace"] a[href="/workspace/"]') is not None
    assert soup.select_one('nav[aria-label="Research workspace"] a[href="/my-research/"]') is not None
    assert soup.select_one("#members-signed-out [data-members-sign-in]") is not None
    signed_out_copy = soup.select_one("#members-signed-out").get_text(" ", strip=True)
    assert "Public search remains open without an account." in signed_out_copy
    assert "basic Google identity details" in signed_out_copy
    assert soup.select_one("#members-signed-in [data-members-export]") is not None
    assert soup.select_one("#members-signed-in [data-members-sign-out]") is not None
    assert soup.select_one("#members-signed-in [data-members-revoke]") is not None
    assert soup.select_one("#members-signed-in [data-members-delete-account]") is not None
    assert soup.select_one('dialog#members-sign-in-dialog[aria-labelledby][aria-describedby]') is not None
    assert soup.select_one('dialog#members-collection-dialog[aria-labelledby][aria-describedby]') is not None
    assert soup.select_one('dialog#members-delete-dialog[aria-labelledby][aria-describedby]') is not None
    assert soup.select_one('[data-members-reauth][hidden]') is not None
    assert soup.select_one('a.b26-members-skip-link[href="#main-content"]') is not None
    assert soup.select_one('label[for="members-collection-name"]') is not None
    assert soup.select_one('label[for="members-dialog-collection-name"]') is not None
    assert soup.select_one('label[for="members-delete-confirmation"]') is not None


def test_member_script_keeps_routes_and_storage_bounded() -> None:
    source = SCRIPT.read_text(encoding="utf-8")

    assert 'const PENDING_STORAGE_KEY = "base2026.pendingResearchSave"' in source
    assert "const PENDING_TTL_MS = 30 * 60 * 1000" in source
    assert "sessionStorage" in source
    assert "const VIDEO_ID_PATTERN = /^tiktok-video-(\\d{10,30})$/" in source
    assert 'return videoId ? `/sources/tiktok-video-${videoId}` : "";' in source
    assert 'const ALLOWED_CALLBACK_PATHS = ["/workspace/", "/my-research/"]' in source
    assert "ALLOWED_CALLBACK_PATHS.includes(pathname)" in source
    assert "return `${pathname}${String(window.location.search || \"\")}${String(window.location.hash || \"\")}`" in source
    assert "Object.keys" not in source
    assert "localStorage" not in source
    assert "setInterval" not in source
    assert "innerHTML" not in source
    assert "textContent" in source
    assert "replaceChildren" in source
    assert 'const row = document.createElement("div")' in source
    assert 'row.setAttribute("role", "listitem")' in source
    assert 'option.setAttribute("role", "listitem")' not in source


def test_member_script_uses_safe_auth_and_private_api_requests() -> None:
    source = SCRIPT.read_text(encoding="utf-8")

    assert 'const AUTH_SOCIAL_PATH = "/api/auth/sign-in/social"' in source
    assert 'const AUTH_SIGN_OUT_PATH = "/api/auth/sign-out"' in source
    assert 'body: JSON.stringify({ provider: "google", callbackURL })' in source
    assert 'parsed.origin === "https://accounts.google.com"' in source
    assert 'window.location.assign(authorizationURL)' in source
    assert 'credentials: "same-origin"' in source
    assert 'cache: "no-store"' in source
    assert 'headers.set("Cache-Control", "no-store")' in source
    assert 'body: JSON.stringify({ kind: "evidence", referenceId: intent.referenceId })' in source
    assert 'body: JSON.stringify({ confirmation: "DELETE" })' in source
    assert 'body: JSON.stringify({})' in source


def test_google_authorization_url_guard_accepts_generated_shape_and_rejects_tampering() -> None:
    node_script = r'''
globalThis.window = {
  location: { origin: "https://base2026.dev", pathname: "/workspace/", search: "", hash: "" },
};
globalThis.document = {
  readyState: "complete",
  querySelector() { return null; },
};
require("./templates/base2026-members.js");
const validate = window.Base2026Members.isGoogleAuthorizationURL;
const generated = new URL("https://accounts.google.com/o/oauth2/v2/auth");
generated.search = new URLSearchParams({
  response_type: "code",
  client_id: "synthetic-google-client-id.apps.googleusercontent.com",
  state: "synthetic-state",
  scope: "openid email profile",
  redirect_uri: "https://base2026.dev/api/auth/callback/google",
  access_type: "online",
  code_challenge_method: "S256",
  code_challenge: "synthetic-code-challenge",
}).toString();
const acceptedWithExplicitFalse = new URL(generated);
acceptedWithExplicitFalse.searchParams.set("include_granted_scopes", "false");
const cases = {
  generated: [generated.toString(), true],
  explicitFalse: [acceptedWithExplicitFalse.toString(), true],
  wrongPath: [generated.toString().replace("/o/oauth2/v2/auth", "/o/oauth2/auth"), false],
  missingState: [generated.toString().replace("&state=synthetic-state", ""), false],
  missingPkce: [generated.toString().replace(/&code_challenge=[^&]+/u, ""), false],
  wrongPkceMethod: [generated.toString().replace("code_challenge_method=S256", "code_challenge_method=plain"), false],
  extraScope: [generated.toString().replace("openid+email+profile", "openid+email+profile+drive.readonly"), false],
  duplicateScope: [generated.toString().replace("scope=openid+email+profile", "scope=openid+email+profile&scope=openid"), false],
  offline: [generated.toString().replace("access_type=online", "access_type=offline"), false],
  wrongRedirect: [generated.toString().replace("https%3A%2F%2Fbase2026.dev%2Fapi%2Fauth%2Fcallback%2Fgoogle", "https%3A%2F%2Fevil.example%2Fcallback"), false],
  incremental: [generated.toString() + "&include_granted_scopes=true", false],
  wrongResponse: [generated.toString().replace("response_type=code", "response_type=token"), false],
  userInfo: [generated.toString().replace("https://accounts.google.com/", "https://evil@accounts.google.com/"), false],
  hash: [generated.toString() + "#fragment", false],
};
for (const [name, [url, expected]] of Object.entries(cases)) {
  if (validate(url) !== expected) throw new Error(`${name} validation mismatch`);
}
'''
    result = subprocess.run(
        ["node", "-e", node_script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_search_enhancement_is_narrow_and_progressive() -> None:
    source = SCRIPT.read_text(encoding="utf-8")

    assert 'document.querySelector("#hits")' in source
    assert 'function syncAccountLinks()' in source
    assert 'state.sessionKnown && state.user ? "My Research" : "Sign in"' in source
    assert 'document.querySelectorAll("[data-members-account-link], [data-members-toolbar-link]")' in source
    assert 'refreshSession({ resume: isResearchPage || Boolean(state.pendingIntent) })' in source
    assert 'querySelectorAll(".result .result-actions")' in source
    assert '.view-source-detail[data-item-id]' in source
    assert 'setAttribute("data-members-save", "true")' in source
    assert "MutationObserver" in source
    assert "observer.disconnect()" in source
    assert 'node.matches?.(".result, .result-actions")' in source
    assert re.search(r"slice\(0, 100\).*actions", source, re.DOTALL)
    assert "web/static/meili.js" not in source


def test_member_styles_preserve_tokens_and_accessibility_targets() -> None:
    source = STYLES.read_text(encoding="utf-8")

    assert "var(--b26-line)" in source
    assert "var(--b26-surface)" in source
    assert "min-height: 44px" in source
    assert "dialog::backdrop" in source
    assert "prefers-reduced-motion: reduce" in source
    assert "overflow-wrap: anywhere" in source
    assert ".b26-members-page [hidden]" in source
    assert "display: none !important" in source
    assert ".b26-members-page .b26-members-action" in source
    assert ".b26-members-page .b26-members-dialog-actions .b26-members-action" in source
    assert ".b26-members-skip-link:focus" in source


def test_member_script_handles_stale_collection_loads_and_fresh_delete_reauth() -> None:
    source = SCRIPT.read_text(encoding="utf-8")

    assert "selectedCollectionRequest" in source
    assert "requestId !== state.selectedCollectionRequest" in source
    assert 'state.enabled = false' in source
    assert 'state.session.fresh === false' in source
    assert 'data-members-reauth' in source
    assert 'Sign out and sign in again' in TEMPLATE.read_text(encoding="utf-8")
    assert 'function openSignIn(trigger, message = "", status = "")' in source
    assert 'setInlineStatus("members-sign-in-status", message, status)' in source
