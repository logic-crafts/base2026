/* Optional private research controls. This file is deliberately usable from
   both /my-research/ and the public search workspace. It does not replace or
   patch the search renderer. */
(function base2026MembersIife() {
  "use strict";

  if (typeof window === "undefined" || typeof document === "undefined") return;

  const API_ROOT = "/api/my-research";
  const AUTH_SOCIAL_PATH = "/api/auth/sign-in/social";
  const AUTH_SIGN_OUT_PATH = "/api/auth/sign-out";
  const OAUTH_ERROR_QUERY_PARAMS = ["error", "error_description", "state", "code"];
  const GENERIC_OAUTH_ERROR_MESSAGE = "Google sign-in could not be completed. Your saved research is unchanged.";
  const OAUTH_ERROR_MESSAGES = Object.freeze({
    account_not_linked: "Google sign-in could not match this account to the existing Base2026 account. Your saved research is intact. Contact Hello support for account help instead of retrying sign-in.",
    state_not_found: "This Google sign-in link has expired. Start sign-in again from Base2026.",
    state_mismatch: "This Google sign-in link could not be verified. Start sign-in again from Base2026.",
    access_denied: "Google sign-in was canceled. Your saved research is unchanged.",
    invalid_code: GENERIC_OAUTH_ERROR_MESSAGE,
    no_code: GENERIC_OAUTH_ERROR_MESSAGE,
    oauth_provider_not_found: GENERIC_OAUTH_ERROR_MESSAGE,
    unable_to_get_user_info: GENERIC_OAUTH_ERROR_MESSAGE,
    email_not_found: "Google did not provide the verified email needed for sign-in. Your saved research is unchanged.",
    email_not_verified: "Google did not provide a verified email for sign-in. Your saved research is unchanged.",
    internal_server_error: GENERIC_OAUTH_ERROR_MESSAGE,
  });
  const PENDING_STORAGE_KEY = "base2026.pendingResearchSave";
  const PENDING_VERSION = 1;
  const PENDING_TTL_MS = 30 * 60 * 1000;
  const MAX_COLLECTIONS = 50;
  const MAX_ITEMS = 500;
  const MAX_NAME_LENGTH = 80;
  const MAX_NOTE_LENGTH = 2000;
  const VIDEO_ID_PATTERN = /^tiktok-video-(\d{10,30})$/;
  const VIDEO_REFERENCE_PATTERN = /^\d{10,30}$/;
  const ALLOWED_CALLBACK_PATHS = ["/workspace/", "/my-research/"];
  const GOOGLE_AUTHORIZATION_PATH = "/o/oauth2/v2/auth";
  const GOOGLE_REDIRECT_URI = "https://base2026.dev/api/auth/callback/google";
  const GOOGLE_SCOPE_SET = new Set(["openid", "email", "profile"]);
  const GOOGLE_AUTHORIZATION_KEYS = new Set([
    "response_type",
    "client_id",
    "state",
    "scope",
    "redirect_uri",
    "access_type",
    "code_challenge_method",
    "code_challenge",
    "include_granted_scopes",
  ]);

  const page = (document.querySelector("#members-signed-out") || document.querySelector("#members-signed-in"))
    ? document.querySelector(".b26-members-main")
    : null;
  const isResearchPage = Boolean(page);
  const state = {
    enabled: true,
    sessionKnown: false,
    user: null,
    session: null,
    collections: [],
    collectionsLoaded: false,
    selectedCollectionId: "",
    selectedItems: [],
    selectedItemsLoading: false,
    selectedItemsError: "",
    selectedCollectionRequest: 0,
    pendingIntent: null,
    saveBusy: false,
    oauthBusy: false,
    oauthRedirecting: false,
    lastSaveTrigger: null,
    resumedPendingKey: "",
  };
  const dialogFocus = new WeakMap();
  const dialogClosePolicy = new WeakMap();
  const registeredDialogs = new WeakSet();

  class MembersApiError extends Error {
    constructor(message, status = 0, code = "request_failed") {
      super(message);
      this.name = "MembersApiError";
      this.status = status;
      this.code = code;
    }
  }

  function trimText(value, max = 1000) {
    return String(value == null ? "" : value).trim().slice(0, max);
  }

  function strictVideoIdFromItemId(itemId) {
    const match = VIDEO_ID_PATTERN.exec(String(itemId == null ? "" : itemId));
    return match ? match[1] : "";
  }

  function normalizeVideoReference(value) {
    const raw = trimText(value, 80);
    const itemIdVideoId = strictVideoIdFromItemId(raw);
    if (itemIdVideoId) return itemIdVideoId;
    return VIDEO_REFERENCE_PATTERN.test(raw) ? raw : "";
  }

  function canonicalSourcePath(referenceId) {
    const videoId = normalizeVideoReference(referenceId);
    return videoId ? `/sources/tiktok-video-${videoId}` : "";
  }

  function isAllowedCallbackPath(pathname) {
    return ALLOWED_CALLBACK_PATHS.includes(pathname);
  }

  function buildCallbackURL() {
    const currentPath = String(window.location.pathname || "");
    const pathname = isAllowedCallbackPath(currentPath) ? currentPath : "/workspace/";
    return `${pathname}${String(window.location.search || "")}${String(window.location.hash || "")}`;
  }

  function isSafeRelativeCallback(callbackURL) {
    const value = String(callbackURL || "");
    if (!value.startsWith("/") || value.startsWith("//") || /[\u0000-\u001f]/.test(value)) return false;
    try {
      const parsed = new URL(value, window.location.origin);
      return parsed.origin === window.location.origin && isAllowedCallbackPath(parsed.pathname);
    } catch (_error) {
      return false;
    }
  }

  function hasSingleNonEmptyParam(params, name) {
    const values = params.getAll(name);
    return values.length === 1 && values[0].trim().length > 0;
  }

  function hasSingleExactParam(params, name, expected) {
    const values = params.getAll(name);
    return values.length === 1 && values[0] === expected;
  }

  function hasExactGoogleScope(params) {
    const values = params.getAll("scope");
    if (values.length !== 1 || values[0].trim() !== values[0]) return false;
    const scopes = values[0].split(/\s+/u);
    if (scopes.length !== GOOGLE_SCOPE_SET.size || new Set(scopes).size !== scopes.length) return false;
    return scopes.every((scope) => GOOGLE_SCOPE_SET.has(scope));
  }

  function isGoogleAuthorizationURL(value) {
    try {
      const parsed = new URL(String(value || ""));
      const isGoogleOrigin = parsed.origin === "https://accounts.google.com";
      if (
        parsed.protocol !== "https:" ||
        !isGoogleOrigin ||
        parsed.pathname !== GOOGLE_AUTHORIZATION_PATH ||
        parsed.username ||
        parsed.password ||
        parsed.hash
      ) return false;
      for (const key of parsed.searchParams.keys()) {
        if (!GOOGLE_AUTHORIZATION_KEYS.has(key)) return false;
      }
      return (
        hasSingleExactParam(parsed.searchParams, "response_type", "code") &&
        hasSingleNonEmptyParam(parsed.searchParams, "client_id") &&
        hasSingleNonEmptyParam(parsed.searchParams, "state") &&
        hasExactGoogleScope(parsed.searchParams) &&
        hasSingleExactParam(parsed.searchParams, "redirect_uri", GOOGLE_REDIRECT_URI) &&
        hasSingleExactParam(parsed.searchParams, "access_type", "online") &&
        hasSingleExactParam(parsed.searchParams, "code_challenge_method", "S256") &&
        hasSingleNonEmptyParam(parsed.searchParams, "code_challenge") &&
        (parsed.searchParams.getAll("include_granted_scopes").length === 0 ||
          hasSingleExactParam(parsed.searchParams, "include_granted_scopes", "false"))
      );
    } catch (_error) {
      return false;
    }
  }

  function safeSessionStorage() {
    try {
      return window.sessionStorage;
    } catch (_error) {
      return null;
    }
  }

  function readPendingIntent() {
    const storage = safeSessionStorage();
    if (!storage) return null;
    let parsed;
    try {
      parsed = JSON.parse(storage.getItem(PENDING_STORAGE_KEY) || "null");
    } catch (_error) {
      try { storage.removeItem(PENDING_STORAGE_KEY); } catch (_ignored) { /* unavailable storage */ }
      return null;
    }
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return null;
    const referenceId = normalizeVideoReference(parsed.referenceId);
    const createdAt = Number(parsed.createdAt);
    const now = Date.now();
    const age = now - createdAt;
    if (
      parsed.version !== PENDING_VERSION ||
      parsed.kind !== "evidence" ||
      !referenceId ||
      !Number.isFinite(createdAt) ||
      age < 0 ||
      age >= PENDING_TTL_MS
    ) {
      try { storage.removeItem(PENDING_STORAGE_KEY); } catch (_ignored) { /* unavailable storage */ }
      return null;
    }
    return { version: PENDING_VERSION, kind: "evidence", referenceId, createdAt };
  }

  function writePendingIntent(referenceId) {
    const videoId = normalizeVideoReference(referenceId);
    if (!videoId) return null;
    const intent = { version: PENDING_VERSION, kind: "evidence", referenceId: videoId, createdAt: Date.now() };
    const storage = safeSessionStorage();
    if (!storage) return null;
    try {
      storage.setItem(PENDING_STORAGE_KEY, JSON.stringify(intent));
      state.pendingIntent = intent;
      return intent;
    } catch (_error) {
      return null;
    }
  }

  function clearPendingIntent() {
    const storage = safeSessionStorage();
    try { storage?.removeItem(PENDING_STORAGE_KEY); } catch (_error) { /* unavailable storage */ }
    state.pendingIntent = null;
    state.resumedPendingKey = "";
  }

  function normalizeUser(value) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return null;
    const id = trimText(value.id, 200);
    const name = trimText(value.name, 200);
    const email = trimText(value.email, 254);
    if (!id && !name && !email) return null;
    return { id, name, email };
  }

  function normalizeCollection(value) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return null;
    const id = trimText(value.id, 240);
    if (!id) return null;
    const itemCount = Number(value.itemCount);
    return {
      id,
      name: trimText(value.name, MAX_NAME_LENGTH) || "Untitled collection",
      createdAt: trimText(value.createdAt, 80),
      updatedAt: trimText(value.updatedAt, 80),
      itemCount: Number.isFinite(itemCount) && itemCount >= 0 ? Math.min(MAX_ITEMS, itemCount) : 0,
    };
  }

  function normalizeItem(value) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return null;
    const id = trimText(value.id, 240);
    const collectionId = trimText(value.collectionId, 240);
    const referenceId = normalizeVideoReference(value.referenceId);
    if (!id || !collectionId || !referenceId || value.kind !== "evidence") return null;
    return {
      id,
      collectionId,
      kind: "evidence",
      referenceId,
      title: trimText(value.title, 320) || "Saved evidence source",
      note: String(value.note == null ? "" : value.note).slice(0, MAX_NOTE_LENGTH),
      createdAt: trimText(value.createdAt, 80),
      updatedAt: trimText(value.updatedAt, 80),
    };
  }

  function apiURL(path) {
    const value = String(path || "");
    if (!value.startsWith("/")) throw new MembersApiError("Invalid private research path.", 0, "invalid_path");
    if (value === AUTH_SOCIAL_PATH || value === AUTH_SIGN_OUT_PATH) return value;
    if (value === API_ROOT || value.startsWith(`${API_ROOT}/`)) return value;
    throw new MembersApiError("Invalid private research path.", 0, "invalid_path");
  }

  async function requestJSON(path, options = {}) {
    const request = { ...options, credentials: "same-origin", cache: "no-store" };
    const headers = new Headers(options.headers || {});
    headers.set("Accept", "application/json");
    headers.set("Cache-Control", "no-store");
    if (options.body !== undefined) headers.set("Content-Type", "application/json");
    request.headers = headers;
    let response;
    try {
      response = await fetch(apiURL(path), request);
    } catch (_error) {
      throw new MembersApiError("Private research service is unavailable.", 503, "unavailable");
    }
    let payload = null;
    try {
      payload = await response.json();
    } catch (_error) {
      payload = null;
    }
    if (!response.ok) {
      const error = payload && typeof payload.error === "object" ? payload.error : {};
      throw new MembersApiError(trimText(error.message, 240) || "Private research request failed.", response.status, trimText(error.code, 100) || "request_failed");
    }
    return payload && typeof payload === "object" ? payload : {};
  }

  async function requestExport() {
    let response;
    try {
      response = await fetch(apiURL(`${API_ROOT}/export`), {
        credentials: "same-origin",
        cache: "no-store",
        headers: { Accept: "application/json", "Cache-Control": "no-store" },
      });
    } catch (_error) {
      throw new MembersApiError("Private research service is unavailable.", 503, "unavailable");
    }
    if (!response.ok) {
      let payload = null;
      try { payload = await response.json(); } catch (_error) { /* response is not JSON */ }
      const error = payload && typeof payload.error === "object" ? payload.error : {};
      throw new MembersApiError(trimText(error.message, 240) || "Export could not be prepared.", response.status, trimText(error.code, 100) || "request_failed");
    }
    return response.blob();
  }

  function getStatusRegion() {
    const existing = document.querySelector("#members-status");
    if (existing) return existing;
    let region = document.querySelector("[data-members-workspace-status]");
    if (region) return region;
    region = document.createElement("p");
    region.className = "b26-members-sr-status";
    region.setAttribute("data-members-workspace-status", "true");
    region.setAttribute("role", "status");
    region.setAttribute("aria-live", "polite");
    region.setAttribute("aria-atomic", "true");
    document.body.append(region);
    return region;
  }

  function announce(message, status = "") {
    const region = getStatusRegion();
    region.textContent = trimText(message, 500);
    if (status) region.setAttribute("data-state", status);
    else region.removeAttribute("data-state");
  }

  function setInlineStatus(id, message, status = "") {
    const region = document.getElementById(id);
    if (!region) return;
    region.textContent = trimText(message, 500);
    if (status) region.setAttribute("data-state", status);
    else region.removeAttribute("data-state");
  }

  function oauthErrorMessage(code) {
    const key = trimText(code, 100);
    return Object.prototype.hasOwnProperty.call(OAUTH_ERROR_MESSAGES, key)
      ? OAUTH_ERROR_MESSAGES[key]
      : GENERIC_OAUTH_ERROR_MESSAGE;
  }

  function currentPageURL() {
    const location = window.location || {};
    const origin = String(location.origin || "https://base2026.dev");
    const fallback = `${origin}${String(location.pathname || "/")}${String(location.search || "")}${String(location.hash || "")}`;
    return new URL(String(location.href || fallback), origin);
  }

  function scrubOAuthCallbackQuery(url) {
    let changed = false;
    OAUTH_ERROR_QUERY_PARAMS.forEach((name) => {
      if (!url.searchParams.has(name)) return;
      url.searchParams.delete(name);
      changed = true;
    });
    if (!changed) return false;
    try {
      if (window.history && typeof window.history.replaceState === "function") {
        window.history.replaceState(window.history.state || null, document.title, `${url.pathname}${url.search}${url.hash}`);
      }
    } catch (_error) {
      // A restricted history object must not prevent the safe message.
    }
    return true;
  }

  function consumeOAuthCallbackError() {
    if (!isResearchPage || String(window.location?.pathname || "") !== "/my-research/") return "";
    let url;
    try {
      url = currentPageURL();
    } catch (_error) {
      return "";
    }
    if (!url.searchParams.has("error")) return "";
    const message = oauthErrorMessage(url.searchParams.get("error"));
    scrubOAuthCallbackQuery(url);
    return message;
  }

  function reportOAuthCallbackError() {
    const message = consumeOAuthCallbackError();
    if (!message) return false;
    announce(message, "error");
    return true;
  }

  function userFacingError(error, fallback = "Private research request failed. Try again.") {
    if (!(error instanceof MembersApiError)) return fallback;
    if (error.status === 503 || error.code === "unavailable") return "Private research is temporarily unavailable. Public search is still available.";
    if (error.status === 401) return "Your private session has expired. Sign in again to retry.";
    if (error.status === 403) return "This action needs a fresh sign-in. Retry with Google to continue.";
    if (error.status === 404) return "That private research record is no longer available.";
    if (error.status === 409) return "That change conflicts with the current collection. Refresh and try again.";
    return fallback;
  }

  function syncAccountLinks() {
    const label = state.sessionKnown && state.user ? "My Research" : "Sign in";
    document.querySelectorAll("[data-members-account-link], [data-members-toolbar-link]").forEach((link) => {
      link.href = "/my-research/";
      link.textContent = label;
    });
  }

  function ensureToolbarLink() {
    const hits = document.querySelector("#hits");
    if (!hits) return;
    const scope = hits.closest(".app-shell") || hits.parentElement || document.body;
    const toolbar = scope.querySelector(".content-toolbar, [data-content-toolbar]");
    if (scope.querySelector("[data-members-toolbar-link]") || toolbar?.querySelector('a[href="/my-research/"]')) return;
    const link = document.createElement("a");
    link.className = "b26-button--secondary b26-members-toolbar-link";
    link.href = "/my-research/";
    link.setAttribute("data-members-toolbar-link", "true");
    link.textContent = "Sign in";
    if (toolbar) {
      toolbar.append(link);
      syncAccountLinks();
      return;
    }
    const anchor = scope.querySelector(".workspace-hero .hero-actions, .hero-actions, .breadcrumbs");
    if (!anchor || !anchor.parentNode) return;
    const createdToolbar = document.createElement("nav");
    createdToolbar.className = "b26-content-toolbar b26-members-content-toolbar";
    createdToolbar.setAttribute("aria-label", "Research workspace");
    createdToolbar.append(link);
    anchor.parentNode.insertBefore(createdToolbar, anchor);
    syncAccountLinks();
  }

  function createDialogElement(kind) {
    const dialog = document.createElement("dialog");
    dialog.className = "b26-members-dialog";
    dialog.id = kind === "sign-in" ? "members-sign-in-dialog" : "members-collection-dialog";
    const body = document.createElement("div");
    body.className = "b26-members-dialog__body";
    const eyebrow = document.createElement("p");
    eyebrow.className = "b26-eyebrow";
    eyebrow.textContent = kind === "sign-in" ? "Optional sign-in" : "Save evidence";
    const title = document.createElement("h2");
    title.id = kind === "sign-in" ? "members-sign-in-title" : "members-collection-dialog-title";
    title.textContent = kind === "sign-in" ? "Continue with Google" : "Choose a collection";
    const description = document.createElement("p");
    description.id = kind === "sign-in" ? "members-sign-in-description" : "members-collection-dialog-description";
    description.textContent = kind === "sign-in"
      ? "Google provides only the basic identity details needed for sign-in. You will return to the same Base2026 workspace, and no search history is stored here."
      : "Keep this public source in one private collection. Duplicate saves are safe.";
    dialog.setAttribute("aria-labelledby", title.id);
    dialog.setAttribute("aria-describedby", description.id);
    body.append(eyebrow, title, description);
    if (kind === "sign-in") {
      const form = document.createElement("form");
      form.id = "members-sign-in-form";
      form.className = "b26-members-dialog-form";
      form.setAttribute("novalidate", "true");
      const actions = document.createElement("div");
      actions.className = "b26-members-dialog-actions";
      const submit = createButton("b26-button--primary b26-members-action", "Continue with Google", "submit");
      submit.setAttribute("data-members-sign-in-submit", "true");
      const cancel = createButton("b26-button--secondary b26-members-action", "Cancel");
      cancel.setAttribute("data-members-dialog-close", "sign-in");
      actions.append(submit, cancel);
      const status = document.createElement("p");
      status.id = "members-sign-in-status";
      status.className = "b26-members-inline-status";
      status.setAttribute("role", "status");
      status.setAttribute("aria-live", "polite");
      form.append(actions, status);
      body.append(form);
    } else {
      appendChooserBody(body);
    }
    dialog.append(body);
    document.body.append(dialog);
    return dialog;
  }

  function createButton(className, label, type = "button") {
    const button = document.createElement("button");
    button.type = type;
    button.className = className;
    button.textContent = label;
    return button;
  }

  function appendChooserBody(body) {
    const list = document.createElement("div");
    list.id = "members-collection-dialog-list";
    list.className = "b26-members-dialog-list";
    list.setAttribute("role", "list");
    const form = document.createElement("form");
    form.id = "members-dialog-create-form";
    form.className = "b26-members-create-form";
    form.setAttribute("novalidate", "true");
    const field = document.createElement("div");
    field.className = "b26-members-field";
    const label = document.createElement("label");
    label.htmlFor = "members-dialog-collection-name";
    label.textContent = "Or create a collection";
    const input = document.createElement("input");
    input.id = "members-dialog-collection-name";
    input.name = "name";
    input.type = "text";
    input.maxLength = MAX_NAME_LENGTH;
    input.autocomplete = "off";
    input.required = true;
    field.append(label, input);
    const actions = document.createElement("div");
    actions.className = "b26-members-form-actions";
    actions.append(
      createButton("b26-button--secondary b26-members-action", "Create and save", "submit"),
      createButton("b26-button--secondary b26-members-action", "Cancel"),
    );
    actions.lastElementChild.setAttribute("data-members-dialog-close", "collection");
    const status = document.createElement("p");
    status.id = "members-collection-dialog-status";
    status.className = "b26-members-inline-status";
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");
    form.append(field, actions);
    body.append(list, form, status);
  }

  function dialogFor(kind) {
    const id = kind === "sign-in" ? "members-sign-in-dialog" : kind === "delete" ? "members-delete-dialog" : "members-collection-dialog";
    let dialog = document.getElementById(id);
    if (!dialog && (kind === "sign-in" || kind === "collection")) dialog = createDialogElement(kind);
    if (dialog) registerDialog(dialog, kind);
    return dialog;
  }

  function isDialogOpen(dialog) {
    return Boolean(dialog && (dialog.open || dialog.hasAttribute("open")));
  }

  function restoreDialogFocus(dialog) {
    const trigger = dialogFocus.get(dialog);
    dialogFocus.delete(dialog);
    if (trigger && trigger.isConnected && !trigger.disabled) {
      try { trigger.focus({ preventScroll: true }); } catch (_error) { trigger.focus(); }
    }
  }

  function registerDialog(dialog, kind) {
    if (!dialog || registeredDialogs.has(dialog)) return;
    registeredDialogs.add(dialog);
    dialog.addEventListener("cancel", () => {
      dialogClosePolicy.set(dialog, true);
    });
    dialog.addEventListener("close", () => {
      const clearPending = dialogClosePolicy.has(dialog) ? dialogClosePolicy.get(dialog) : kind === "sign-in" || kind === "collection";
      dialogClosePolicy.delete(dialog);
      if (clearPending && (kind === "sign-in" || kind === "collection")) clearPendingIntent();
      restoreDialogFocus(dialog);
    });
  }

  function openDialog(kind, trigger = null) {
    const dialog = dialogFor(kind);
    if (!dialog) return null;
    dialogFocus.set(dialog, trigger || document.activeElement);
    if (!isDialogOpen(dialog)) {
      try {
        if (typeof dialog.showModal === "function") dialog.showModal();
        else dialog.setAttribute("open", "true");
      } catch (_error) {
        dialog.setAttribute("open", "true");
      }
    }
    const first = dialog.querySelector("[autofocus], input, button");
    if (first) {
      try { first.focus({ preventScroll: true }); } catch (_error) { first.focus(); }
    }
    return dialog;
  }

  function closeDialog(kind, options = {}) {
    const dialog = dialogFor(kind);
    if (!dialog) return;
    const clearPending = options.clearPending !== false;
    dialogClosePolicy.set(dialog, clearPending);
    if (isDialogOpen(dialog) && typeof dialog.close === "function") dialog.close();
    else {
      dialog.removeAttribute("open");
      if (clearPending && (kind === "sign-in" || kind === "collection")) clearPendingIntent();
      restoreDialogFocus(dialog);
    }
  }

  function setDialogButtonsDisabled(dialog, disabled) {
    if (!dialog) return;
    dialog.querySelectorAll("button").forEach((button) => { button.disabled = disabled; });
  }

  function renderMemberPage() {
    syncAccountLinks();
    if (!isResearchPage) return;
    const loading = document.querySelector("#members-loading");
    const signedOut = document.querySelector("#members-signed-out");
    const signedIn = document.querySelector("#members-signed-in");
    if (loading) loading.hidden = state.sessionKnown;
    if (signedOut) signedOut.hidden = !state.sessionKnown || Boolean(state.user);
    if (signedIn) signedIn.hidden = !state.sessionKnown || !Boolean(state.user);
    if (!state.sessionKnown) return;
    const signIn = document.querySelector("[data-members-sign-in]");
    if (signIn) signIn.disabled = !state.enabled;
    if (!state.user) {
      if (!state.enabled) announce("Private research is not enabled yet. Public search is still available.");
      return;
    }
    const name = document.querySelector("#members-identity-name");
    const email = document.querySelector("#members-identity-email");
    if (name) name.textContent = state.user.name || "Google account";
    if (email) email.textContent = state.user.email || "Signed-in account";
    renderCollections();
    renderSelectedItems();
  }

  function renderCollections() {
    const list = document.querySelector("#members-collections-list");
    if (!list) return;
    list.replaceChildren();
    state.collections.slice(0, MAX_COLLECTIONS).forEach((collection) => {
      const row = document.createElement("div");
      row.className = "b26-members-collection";
      row.setAttribute("role", "listitem");
      if (collection.id === state.selectedCollectionId) row.classList.add("is-selected");
      const select = createButton("b26-members-collection-select", "");
      select.setAttribute("data-members-select-collection", collection.id);
      select.setAttribute("aria-pressed", collection.id === state.selectedCollectionId ? "true" : "false");
      const collectionName = document.createElement("span");
      collectionName.className = "b26-members-collection-name";
      collectionName.textContent = collection.name;
      const collectionCount = document.createElement("span");
      collectionCount.className = "b26-members-collection-count";
      collectionCount.textContent = `${collection.itemCount} saved`;
      select.append(collectionName, collectionCount);
      row.append(select);
      list.append(row);
    });
  }

  function formatItemDate(value) {
    const date = new Date(value);
    if (!value || Number.isNaN(date.getTime())) return "";
    try { return new Intl.DateTimeFormat("en", { year: "numeric", month: "short", day: "numeric" }).format(date); } catch (_error) { return ""; }
  }

  function renderSelectedItems() {
    const list = document.querySelector("#members-items-list");
    const title = document.querySelector("#members-items-title");
    const meta = document.querySelector("#members-selected-collection-meta");
    if (!list) return;
    const selected = state.collections.find((collection) => collection.id === state.selectedCollectionId);
    if (title) title.textContent = selected ? selected.name : "Select a collection";
    if (meta) meta.textContent = selected ? `${state.selectedItems.length} saved source${state.selectedItems.length === 1 ? "" : "s"}` : "Choose a collection to see saved evidence.";
    list.replaceChildren();
    if (!selected) return;
    if (state.selectedItemsLoading) {
      const loading = document.createElement("p");
      loading.className = "b26-members-section-meta";
      loading.textContent = "Loading saved evidence…";
      list.append(loading);
      return;
    }
    if (state.selectedItemsError) {
      const error = document.createElement("p");
      error.className = "b26-members-inline-status";
      error.setAttribute("data-state", "error");
      error.textContent = state.selectedItemsError;
      list.append(error);
      return;
    }
    state.selectedItems.slice(0, MAX_ITEMS).forEach((item) => {
      const article = document.createElement("article");
      article.className = "b26-members-item";
      article.setAttribute("role", "listitem");
      const heading = document.createElement("div");
      heading.className = "b26-members-item-heading";
      const sourcePath = canonicalSourcePath(item.referenceId);
      if (sourcePath) {
        const link = document.createElement("a");
        link.className = "b26-members-item-title";
        link.href = sourcePath;
        link.textContent = item.title;
        heading.append(link);
      } else {
        const titleText = document.createElement("span");
        titleText.className = "b26-members-item-title";
        titleText.textContent = item.title;
        heading.append(titleText);
      }
      const date = document.createElement("time");
      date.className = "b26-members-item-date";
      date.dateTime = item.createdAt || "";
      date.textContent = formatItemDate(item.createdAt);
      heading.append(date);
      const noteLabel = document.createElement("label");
      noteLabel.className = "b26-members-note-label";
      noteLabel.textContent = "Private note";
      const note = document.createElement("textarea");
      note.className = "b26-members-note";
      note.maxLength = MAX_NOTE_LENGTH;
      note.value = item.note;
      note.setAttribute("data-members-note", item.id);
      noteLabel.append(note);
      const actions = document.createElement("div");
      actions.className = "b26-members-item-actions";
      const saveNote = createButton("b26-members-item-save", "Save note");
      saveNote.setAttribute("data-members-save-note", item.id);
      const remove = createButton("b26-members-item-remove", "Remove");
      remove.setAttribute("data-members-remove-item", item.id);
      actions.append(saveNote, remove);
      article.append(heading, noteLabel, actions);
      list.append(article);
    });
  }

  function renderChooser() {
    const dialog = dialogFor("collection");
    if (!dialog) return;
    const list = dialog.querySelector("#members-collection-dialog-list");
    if (!list) return;
    list.replaceChildren();
    state.collections.slice(0, MAX_COLLECTIONS).forEach((collection) => {
      const row = document.createElement("div");
      row.setAttribute("role", "listitem");
      const option = createButton("b26-members-chooser-option", "");
      option.setAttribute("data-members-choose-collection", collection.id);
      const name = document.createElement("span");
      name.textContent = collection.name;
      const count = document.createElement("small");
      count.textContent = `${collection.itemCount} saved`;
      option.append(name, count);
      row.append(option);
      list.append(row);
    });
    const createForm = dialog.querySelector("#members-dialog-create-form");
    if (createForm) createForm.hidden = state.collections.length >= MAX_COLLECTIONS;
  }

  async function loadCollections(options = {}) {
    if (state.collectionsLoaded && !options.force) {
      renderCollections();
      renderChooser();
      return state.collections;
    }
    const payload = await requestJSON(`${API_ROOT}/collections`, { method: "GET" });
    state.collections = Array.isArray(payload.collections)
      ? payload.collections.map(normalizeCollection).filter(Boolean).slice(0, MAX_COLLECTIONS)
      : [];
    state.collectionsLoaded = true;
    if (!state.collections.some((collection) => collection.id === state.selectedCollectionId)) {
      state.selectedCollectionId = state.collections[0]?.id || "";
    }
    renderCollections();
    renderChooser();
    return state.collections;
  }

  async function loadSelectedCollection(collectionId) {
    const id = trimText(collectionId, 240);
    const requestId = ++state.selectedCollectionRequest;
    if (!id) {
      state.selectedItems = [];
      state.selectedItemsError = "";
      renderSelectedItems();
      return;
    }
    state.selectedItemsLoading = true;
    state.selectedItemsError = "";
    renderSelectedItems();
    try {
      const payload = await requestJSON(`${API_ROOT}/collections/${encodeURIComponent(id)}`, { method: "GET" });
      if (requestId !== state.selectedCollectionRequest || id !== state.selectedCollectionId) return;
      const collection = payload.collection && typeof payload.collection === "object" ? payload.collection : {};
      const items = Array.isArray(payload.items) ? payload.items : collection.items;
      state.selectedItems = Array.isArray(items)
        ? items.map(normalizeItem).filter(Boolean).slice(0, MAX_ITEMS)
        : [];
      const listed = state.collections.find((entry) => entry.id === id);
      if (listed && Number.isFinite(Number(collection.itemCount))) listed.itemCount = Math.min(MAX_ITEMS, Math.max(0, Number(collection.itemCount)));
      state.selectedItemsLoading = false;
      renderCollections();
      renderSelectedItems();
    } catch (error) {
      if (requestId !== state.selectedCollectionRequest || id !== state.selectedCollectionId) return;
      state.selectedItemsLoading = false;
      state.selectedItemsError = userFacingError(error, "Saved evidence could not be loaded. Try again.");
      renderSelectedItems();
    }
  }

  async function refreshSession(options = {}) {
    try {
      const payload = await requestJSON(`${API_ROOT}/session`, { method: "GET" });
      state.enabled = payload.enabled !== false;
      state.user = normalizeUser(payload.user);
      state.session = payload.session && typeof payload.session === "object" ? {
        expiresAt: trimText(payload.session.expiresAt, 80),
        fresh: Boolean(payload.session.fresh),
      } : null;
      state.sessionKnown = true;
      renderMemberPage();
      reportOAuthCallbackError();
      if (state.user && state.enabled && isResearchPage) {
        try {
          await loadCollections();
          if (state.selectedCollectionId) await loadSelectedCollection(state.selectedCollectionId);
        } catch (error) {
          announce(userFacingError(error, "Collections could not be loaded. Try again."), "error");
        }
      }
      if (state.user && options.resume !== false) await resumePendingSave();
      if (!state.user && state.pendingIntent && options.resume !== false) {
        announce("One selected evidence source is waiting for sign-in.");
      }
      return state.user;
    } catch (error) {
      if (error.status === 503 || error.code === "unavailable" || error.code === "MEMBER_AUTH_DISABLED" || error.code === "AUTH_UNAVAILABLE") {
        state.enabled = false;
      }
      state.sessionKnown = true;
      state.user = null;
      state.session = null;
      renderMemberPage();
      if (!reportOAuthCallbackError()) announce(userFacingError(error, "Private research session could not be checked."), "error");
      return null;
    }
  }

  async function ensureSession() {
    if (state.sessionKnown) return state.user;
    return refreshSession({ resume: false });
  }

  async function resumePendingSave() {
    const intent = readPendingIntent();
    state.pendingIntent = intent;
    if (!intent || !state.user || !state.enabled) return;
    const key = `${intent.referenceId}:${intent.createdAt}`;
    if (state.resumedPendingKey === key || state.saveBusy) return;
    state.resumedPendingKey = key;
    await openCollectionChooser(intent, null);
  }

  async function openCollectionChooser(intent, trigger) {
    if (!state.user || !state.enabled) {
      openSignIn(trigger);
      return;
    }
    state.pendingIntent = intent || readPendingIntent();
    if (!state.pendingIntent) return;
    state.lastSaveTrigger = trigger || state.lastSaveTrigger;
    const dialog = openDialog("collection", trigger);
    if (!dialog) return;
    renderChooser();
    setInlineStatus("members-collection-dialog-status", "Loading collections…");
    try {
      await loadCollections({ force: true });
      renderChooser();
      setInlineStatus("members-collection-dialog-status", state.collections.length ? "Choose where to save this source." : "Create a collection to save this source.");
    } catch (error) {
      setInlineStatus("members-collection-dialog-status", userFacingError(error, "Collections could not be loaded. Try again."), "error");
    }
  }

  function openSignIn(trigger, message = "", status = "") {
    const dialog = openDialog("sign-in", trigger);
    if (!dialog) return;
    if (message) setInlineStatus("members-sign-in-status", message, status);
    else if (!state.enabled) setInlineStatus("members-sign-in-status", "Private research is not enabled yet.", "error");
    else setInlineStatus("members-sign-in-status", "");
  }

  async function beginSave(referenceId, trigger, button = null) {
    const videoId = normalizeVideoReference(referenceId);
    if (!videoId) return false;
    if (!state.enabled) {
      announce("Private research is not enabled yet. Public search is still available.", "error");
      return false;
    }
    const intent = writePendingIntent(videoId);
    if (!intent) {
      announce("This browser could not keep the pending save. Nothing was sent.", "error");
      return false;
    }
    state.lastSaveTrigger = button || trigger || null;
    await ensureSession();
    if (state.user) {
      await openCollectionChooser(intent, button || trigger);
    } else {
      openSignIn(button || trigger, "Sign in to choose a private collection.");
    }
    return true;
  }

  function markSaveButtonSaved(button) {
    if (!button || !button.isConnected) return;
    button.dataset.membersSaved = "true";
    button.disabled = true;
    button.textContent = "Saved";
  }

  function enhanceSearchResults() {
    const hits = document.querySelector("#hits");
    if (!hits || !document.documentElement.contains(hits)) return;
    const actions = [...hits.querySelectorAll(".result .result-actions")].slice(0, 100);
    actions.forEach((action) => {
      if (action.querySelector("[data-members-save]")) return;
      const openSource = action.querySelector('.view-source-detail[data-item-id]');
      const videoId = strictVideoIdFromItemId(openSource?.getAttribute("data-item-id") || "");
      if (!openSource || !videoId) return;
      const button = createButton("button-link", "Save");
      button.setAttribute("data-members-save", "true");
      button.setAttribute("data-video-id", videoId);
      button.setAttribute("aria-label", "Save this evidence to My Research");
      button.addEventListener("click", async () => {
        if (button.disabled || button.dataset.membersSaved === "true") return;
        button.disabled = true;
        button.textContent = "Saving…";
        try {
          await beginSave(videoId, button, button);
        } finally {
          if (button.isConnected && button.dataset.membersSaved !== "true") {
            button.disabled = false;
            button.textContent = "Save";
          }
        }
      });
      action.append(button);
    });
  }

  function installSearchEnhancements() {
    const hits = document.querySelector("#hits");
    if (!hits) return;
    ensureToolbarLink();
    enhanceSearchResults();
    if (typeof MutationObserver === "undefined") return;
    const observer = new MutationObserver((records) => {
      if (!document.documentElement.contains(hits)) {
        observer.disconnect();
        return;
      }
      const relevant = records.some((record) => [...record.addedNodes].some((node) => {
        if (node.nodeType !== 1) return false;
        return node.matches?.(".result, .result-actions") || Boolean(node.closest?.(".result")) || Boolean(node.querySelector?.(".result, .result-actions"));
      }));
      if (relevant) enhanceSearchResults();
    });
    observer.observe(hits, { childList: true, subtree: true });
  }

  async function handleSignInSubmit(event) {
    event.preventDefault();
    if (state.oauthBusy || !state.enabled) return;
    const callbackURL = buildCallbackURL();
    if (!isSafeRelativeCallback(callbackURL)) {
      setInlineStatus("members-sign-in-status", "This return path is not available. Open the workspace and try again.", "error");
      return;
    }
    state.oauthBusy = true;
    const dialog = dialogFor("sign-in");
    const submit = dialog?.querySelector("[data-members-sign-in-submit]");
    if (submit) {
      submit.disabled = true;
      submit.textContent = "Connecting…";
    }
    setInlineStatus("members-sign-in-status", "Opening Google authorization…");
    try {
      const payload = await requestJSON(AUTH_SOCIAL_PATH, {
        method: "POST",
        body: JSON.stringify({ provider: "google", callbackURL }),
      });
      const authorizationURL = String(payload.url || "");
      if (payload.redirect !== undefined && payload.redirect !== true) throw new MembersApiError("Authorization redirect was not accepted.", 502, "invalid_authorization_redirect");
      if (!isGoogleAuthorizationURL(authorizationURL)) throw new MembersApiError("Authorization URL was not accepted.", 502, "invalid_authorization_url");
      state.oauthRedirecting = true;
      window.location.assign(authorizationURL);
    } catch (error) {
      state.oauthRedirecting = false;
      setInlineStatus("members-sign-in-status", userFacingError(error, "Google sign-in could not start. Try again."), "error");
      if (submit) {
        submit.disabled = false;
        submit.textContent = "Continue with Google";
      }
    } finally {
      state.oauthBusy = false;
    }
  }

  async function handleCreateCollection(form, targetStatusId = "members-collection-form-status", chooser = false) {
    const input = form.querySelector('input[name="name"]');
    const name = trimText(input?.value || "", MAX_NAME_LENGTH);
    if (!name) {
      setInlineStatus(targetStatusId, "Enter a collection name.", "error");
      input?.focus();
      return;
    }
    if (state.collections.length >= MAX_COLLECTIONS) {
      setInlineStatus(targetStatusId, "You have reached the 50-collection limit.", "error");
      return;
    }
    const submit = form.querySelector('button[type="submit"]');
    if (submit) submit.disabled = true;
    setInlineStatus(targetStatusId, "Creating collection…");
    try {
      const payload = await requestJSON(`${API_ROOT}/collections`, {
        method: "POST",
        body: JSON.stringify({ name }),
      });
      const collection = normalizeCollection(payload.collection);
      if (!collection) throw new MembersApiError("Collection response was incomplete.", 502, "invalid_response");
      state.collections = [collection, ...state.collections].slice(0, MAX_COLLECTIONS);
      state.collectionsLoaded = true;
      state.selectedCollectionId = collection.id;
      form.reset();
      renderCollections();
      renderChooser();
      setInlineStatus(targetStatusId, "Collection created.", "success");
      if (chooser && state.pendingIntent) {
        await savePendingToCollection(collection.id);
      } else {
        form.hidden = true;
        const toggle = document.querySelector("[data-members-toggle-create]");
        toggle?.setAttribute("aria-expanded", "false");
        await loadSelectedCollection(collection.id);
        announce("Collection created.", "success");
      }
    } catch (error) {
      setInlineStatus(targetStatusId, userFacingError(error, "Collection could not be created. Try again."), "error");
    } finally {
      if (submit) submit.disabled = false;
    }
  }

  async function savePendingToCollection(collectionId) {
    if (state.saveBusy) return false;
    const intent = state.pendingIntent || readPendingIntent();
    if (!intent || !state.user) {
      openSignIn(state.lastSaveTrigger, "Sign in to save this source.");
      return false;
    }
    const totalItems = state.collections.reduce((total, collection) => total + Math.max(0, Number(collection.itemCount) || 0), 0);
    if (totalItems >= MAX_ITEMS) {
      setInlineStatus("members-collection-dialog-status", "You have reached the 500-item limit.", "error");
      return false;
    }
    state.saveBusy = true;
    const dialog = dialogFor("collection");
    setDialogButtonsDisabled(dialog, true);
    setInlineStatus("members-collection-dialog-status", "Saving evidence…");
    try {
      const payload = await requestJSON(`${API_ROOT}/collections/${encodeURIComponent(collectionId)}/items`, {
        method: "POST",
        body: JSON.stringify({ kind: "evidence", referenceId: intent.referenceId }),
      });
      const created = payload.created !== false;
      clearPendingIntent();
      closeDialog("collection", { clearPending: false });
      markSaveButtonSaved(state.lastSaveTrigger);
      announce(created ? "Evidence saved to your private collection." : "Evidence was already in that collection.", "success");
      const selectedCollection = state.collections.find((collection) => collection.id === collectionId);
      if (selectedCollection) selectedCollection.itemCount = Math.min(MAX_ITEMS, selectedCollection.itemCount + (created ? 1 : 0));
      if (isResearchPage && state.selectedCollectionId === collectionId) await loadSelectedCollection(collectionId);
      return true;
    } catch (error) {
      if (error.status === 401 || error.status === 403) {
        closeDialog("collection", { clearPending: false });
        state.user = null;
        state.session = null;
        state.sessionKnown = true;
        renderMemberPage();
        openSignIn(state.lastSaveTrigger, userFacingError(error, "Sign in again to retry this save."), "error");
      } else {
        setInlineStatus("members-collection-dialog-status", userFacingError(error, "Evidence could not be saved. Try again."), "error");
      }
      return false;
    } finally {
      state.saveBusy = false;
      setDialogButtonsDisabled(dialog, false);
    }
  }

  async function handleNoteSave(itemId, textarea, button) {
    const id = trimText(itemId, 240);
    if (!id || !textarea || !state.user || button?.disabled) return;
    const note = String(textarea.value || "").slice(0, MAX_NOTE_LENGTH);
    if (button) button.disabled = true;
    try {
      await requestJSON(`${API_ROOT}/items/${encodeURIComponent(id)}`, {
        method: "PATCH",
        body: JSON.stringify({ note }),
      });
      const item = state.selectedItems.find((entry) => entry.id === id);
      if (item) item.note = note;
      announce("Private note updated.", "success");
    } catch (error) {
      announce(userFacingError(error, "Private note could not be updated."), "error");
    } finally {
      if (button) button.disabled = false;
    }
  }

  async function handleRemoveItem(itemId, button) {
    const id = trimText(itemId, 240);
    if (!id || !state.user || button?.disabled) return;
    if (button) button.disabled = true;
    try {
      await requestJSON(`${API_ROOT}/items/${encodeURIComponent(id)}`, { method: "DELETE" });
      state.selectedItems = state.selectedItems.filter((item) => item.id !== id);
      const collection = state.collections.find((entry) => entry.id === state.selectedCollectionId);
      if (collection) collection.itemCount = Math.max(0, collection.itemCount - 1);
      renderCollections();
      renderSelectedItems();
      announce("Evidence removed from the collection.", "success");
    } catch (error) {
      announce(userFacingError(error, "Evidence could not be removed."), "error");
      if (button) button.disabled = false;
    }
  }

  async function handleExport(button) {
    if (!state.user || button?.disabled) return;
    if (button) button.disabled = true;
    announce("Preparing your private export…");
    try {
      const blob = await requestExport();
      if (!window.URL?.createObjectURL) throw new MembersApiError("Export download is unavailable.", 0, "download_unavailable");
      const objectURL = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = objectURL;
      link.download = "base2026-my-research.json";
      link.hidden = true;
      document.body.append(link);
      link.click();
      link.remove();
      window.setTimeout(() => window.URL.revokeObjectURL(objectURL), 1000);
      announce("Private export downloaded.", "success");
    } catch (error) {
      announce(userFacingError(error, "Export could not be prepared."), "error");
    } finally {
      if (button) button.disabled = false;
    }
  }

  function resetSignedOut(message = "") {
    clearPendingIntent();
    state.user = null;
    state.session = null;
    state.collections = [];
    state.collectionsLoaded = false;
    state.selectedCollectionId = "";
    state.selectedItems = [];
    state.selectedItemsError = "";
    state.sessionKnown = true;
    renderMemberPage();
    if (message) announce(message, "success");
  }

  async function handleSignOut(button) {
    if (button?.disabled) return;
    if (button) button.disabled = true;
    try {
      await requestJSON(AUTH_SIGN_OUT_PATH, { method: "POST", body: JSON.stringify({}) });
      resetSignedOut("Signed out. Your pending save was cleared.");
    } catch (error) {
      if (error.status === 401) resetSignedOut("Your session has already ended.");
      else announce(userFacingError(error, "Sign out could not be completed."), "error");
    } finally {
      if (button) button.disabled = false;
    }
  }

  async function handleRevoke(button) {
    if (!state.user || button?.disabled) return;
    if (button) button.disabled = true;
    try {
      await requestJSON(`${API_ROOT}/revoke-sessions`, { method: "POST", body: JSON.stringify({}) });
      resetSignedOut("All sessions were revoked. You are signed out.");
    } catch (error) {
      announce(userFacingError(error, "Sessions could not be revoked."), "error");
    } finally {
      if (button) button.disabled = false;
    }
  }

  async function handleDeleteAccount(event) {
    event.preventDefault();
    if (!state.user) return;
    const input = document.querySelector("#members-delete-confirmation");
    const button = event.currentTarget.querySelector('button[type="submit"]');
    if (String(input?.value || "").trim() !== "DELETE") {
      setInlineStatus("members-delete-status", "Type DELETE exactly to confirm.", "error");
      input?.focus();
      return;
    }
    if (state.session && state.session.fresh === false) {
      showDeleteReauth("This account action needs a fresh Google sign-in. Sign out, then sign in again to continue.");
      return;
    }
    if (button?.disabled) return;
    if (button) button.disabled = true;
    setInlineStatus("members-delete-status", "Deleting account…");
    try {
      await requestJSON(`${API_ROOT}/delete-account`, {
        method: "POST",
        body: JSON.stringify({ confirmation: "DELETE" }),
      });
      closeDialog("delete", { clearPending: true });
      resetSignedOut("Account deleted. Public search remains available.");
    } catch (error) {
      if (error.status === 403 || (state.session && state.session.fresh === false)) {
        showDeleteReauth("This account action needs a fresh Google sign-in. Sign out, then sign in again to continue.");
      } else {
        setInlineStatus("members-delete-status", userFacingError(error, "Account could not be deleted. Try again."), "error");
      }
    } finally {
      if (button) button.disabled = false;
    }
  }

  function showDeleteReauth(message) {
    const reauth = document.querySelector("[data-members-reauth]");
    if (reauth) reauth.hidden = false;
    setInlineStatus("members-delete-status", message, "error");
  }

  async function handleReauthenticate(button) {
    if (button?.disabled) return;
    if (button) button.disabled = true;
    setInlineStatus("members-delete-status", "Signing out so you can sign in again…");
    try {
      await requestJSON(AUTH_SIGN_OUT_PATH, { method: "POST", body: JSON.stringify({}) });
      closeDialog("delete", { clearPending: true });
      resetSignedOut("Signed out. Sign in again with Google to continue.");
      openSignIn(null, "Sign in again with Google to continue.");
    } catch (error) {
      if (error.status === 401) {
        closeDialog("delete", { clearPending: true });
        resetSignedOut("Your session has already ended. Sign in again with Google to continue.");
        openSignIn(null, "Sign in again with Google to continue.");
      } else {
        setInlineStatus("members-delete-status", userFacingError(error, "Sign out could not be completed. Try again."), "error");
      }
    } finally {
      if (button) button.disabled = false;
    }
  }

  function toggleCreateCollection() {
    const form = document.querySelector("#members-create-collection");
    const toggle = document.querySelector("[data-members-toggle-create]");
    if (!form || !toggle) return;
    const open = form.hidden;
    form.hidden = !open;
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    if (open) form.querySelector("input")?.focus();
  }

  function setupPageEvents() {
    ["sign-in", "collection", "delete"].forEach((kind) => dialogFor(kind));
    document.addEventListener("submit", (event) => {
      const form = event.target instanceof HTMLFormElement ? event.target : null;
      if (!form) return;
      if (form.id === "members-sign-in-form") {
        handleSignInSubmit(event);
      } else if (form.id === "members-create-collection") {
        event.preventDefault();
        handleCreateCollection(form);
      } else if (form.id === "members-dialog-create-form") {
        event.preventDefault();
        handleCreateCollection(form, "members-collection-dialog-status", true);
      } else if (form.id === "members-delete-form") {
        handleDeleteAccount(event);
      }
    });
    document.addEventListener("click", (event) => {
      const target = event.target instanceof Element ? event.target : null;
      if (!target) return;
      const signIn = target.closest("[data-members-sign-in]");
      if (signIn) {
        openSignIn(signIn);
        return;
      }
      const close = target.closest("[data-members-dialog-close]");
      if (close) {
        closeDialog(close.getAttribute("data-members-dialog-close") || "sign-in");
        return;
      }
      const choose = target.closest("[data-members-choose-collection]");
      if (choose) {
        savePendingToCollection(choose.getAttribute("data-members-choose-collection") || "");
        return;
      }
      const select = target.closest("[data-members-select-collection]");
      if (select) {
        state.selectedCollectionId = select.getAttribute("data-members-select-collection") || "";
        renderCollections();
        loadSelectedCollection(state.selectedCollectionId);
        return;
      }
      const saveNote = target.closest("[data-members-save-note]");
      if (saveNote) {
        const id = saveNote.getAttribute("data-members-save-note") || "";
        const note = [...document.querySelectorAll("[data-members-note]")]
          .find((entry) => entry.getAttribute("data-members-note") === id);
        handleNoteSave(id, note, saveNote);
        return;
      }
      const remove = target.closest("[data-members-remove-item]");
      if (remove) {
        handleRemoveItem(remove.getAttribute("data-members-remove-item") || "", remove);
        return;
      }
      const toggle = target.closest("[data-members-toggle-create]");
      if (toggle) {
        toggleCreateCollection();
        return;
      }
      const cancelCreate = target.closest("[data-members-cancel-create]");
      if (cancelCreate) {
        const form = document.querySelector("#members-create-collection");
        if (form) form.hidden = true;
        document.querySelector("[data-members-toggle-create]")?.setAttribute("aria-expanded", "false");
        return;
      }
      const exportButton = target.closest("[data-members-export]");
      if (exportButton) {
        handleExport(exportButton);
        return;
      }
      const signOut = target.closest("[data-members-sign-out]");
      if (signOut) {
        handleSignOut(signOut);
        return;
      }
      const revoke = target.closest("[data-members-revoke]");
      if (revoke) {
        handleRevoke(revoke);
        return;
      }
      const deleteAccount = target.closest("[data-members-delete-account]");
      if (deleteAccount) {
        const dialog = openDialog("delete", deleteAccount);
        const input = dialog?.querySelector("#members-delete-confirmation");
        const status = dialog?.querySelector("#members-delete-status");
        const reauth = dialog?.querySelector("[data-members-reauth]");
        if (input) input.value = "";
        if (status) status.textContent = "";
        if (reauth) reauth.hidden = true;
        return;
      }
      const reauth = target.closest("[data-members-reauth]");
      if (reauth) {
        handleReauthenticate(reauth);
      }
    });
  }

  function init() {
    const hasSearchWorkspace = Boolean(document.querySelector("#hits"));
    if (!isResearchPage && !hasSearchWorkspace) return;
    state.pendingIntent = readPendingIntent();
    setupPageEvents();
    installSearchEnhancements();
    renderMemberPage();
    refreshSession({ resume: isResearchPage || Boolean(state.pendingIntent) });
  }

  window.Base2026Members = {
    strictVideoIdFromItemId,
    normalizeVideoReference,
    canonicalSourcePath,
    buildCallbackURL,
    isSafeRelativeCallback,
    isGoogleAuthorizationURL,
    oauthErrorMessage,
    consumeOAuthCallbackError,
    PENDING_STORAGE_KEY,
    PENDING_TTL_MS,
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init, { once: true });
  else init();
})();
