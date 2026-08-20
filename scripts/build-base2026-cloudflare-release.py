#!/usr/bin/env python3
"""Build a deterministic, root-mounted Cloudflare copy of the public Base2026 web tree.

The input to this script is an already-reviewed public web artifact.  It does
not run the Base2026 private build, inspect a database, contact Cloudflare, or
deploy anything.  Its only job is to copy that artifact into a separate output
tree and make the URL boundary explicit:

* Base2026's old ``/knowledge`` origin becomes ``https://base2026.dev``;
* the old search prefix becomes ``/api/search``;
* standalone startup releases do not retain the founder's personal-site shell;
* binary files are copied byte-for-byte.

The implementation deliberately stages the output in a newly-created sibling
directory and atomically renames it only after all checks pass.  Existing
output directories are refused so a dirty release cannot be overwritten.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Sequence
from urllib.parse import urlsplit, urlunsplit


SCHEMA = "base2026.cloudflare-public-release-receipt/v1"
RECEIPT_FILENAME = ".base2026-cloudflare-release-receipt.json"
ASSETSIGNORE_FILENAME = ".assetsignore"
ROBOTS_FILENAME = "robots.txt"
HEADERS_FILENAME = "_headers"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HOMEPAGE_TEMPLATE = PROJECT_ROOT / "templates" / "base2026-startup-homepage.html"
DEFAULT_HOMEPAGE_STYLESHEET = PROJECT_ROOT / "templates" / "base2026-startup-homepage.css"
DEFAULT_STARTUP_HEADER = PROJECT_ROOT / "templates" / "base2026-startup-header.html"
DEFAULT_STARTUP_FOOTER = PROJECT_ROOT / "templates" / "base2026-startup-footer.html"
DEFAULT_STARTUP_SHELL_STYLESHEET = PROJECT_ROOT / "templates" / "base2026-startup-shell.css"
DEFAULT_SUPPORT_TEMPLATE = PROJECT_ROOT / "templates" / "base2026-support.html"
DEFAULT_PARTNER_TEMPLATE = PROJECT_ROOT / "templates" / "base2026-partner.html"
DEFAULT_PRIVACY_TEMPLATE = PROJECT_ROOT / "templates" / "base2026-privacy.html"
DEFAULT_ABOUT_TEMPLATE = PROJECT_ROOT / "templates" / "base2026-about.html"
DEFAULT_FORMS_SCRIPT = PROJECT_ROOT / "templates" / "base2026-forms.js"
DEFAULT_GITHUB_ICON = PROJECT_ROOT / "static" / "brand" / "github.svg"
DEFAULT_X_ICON = PROJECT_ROOT / "static" / "brand" / "x.svg"
DEFAULT_MARK_ICON = PROJECT_ROOT / "static" / "base2026-mark.svg"

OLD_WORDPRESS_ORIGIN = "https://aggressorbulkit.online"
BASE2026_ORIGIN = "https://base2026.dev"
OLD_BASE2026_PREFIX = "/knowledge"
NEW_BASE2026_PREFIX = ""
OLD_SEARCH_PREFIX = "/knowledge-search"
NEW_SEARCH_PREFIX = "/api/search"
ASSET_VERSION = "base2026-cloudflare-20260819-01"

# Public web text is intentionally broader than the sample's extension set so
# this remains useful for future static assets.  Content-based detection below
# still protects arbitrary binary files with a non-standard extension.
TEXT_EXTENSIONS = {
    ".cjs",
    ".css",
    ".csv",
    ".html",
    ".htm",
    ".ini",
    ".js",
    ".json",
    ".jsonl",
    ".map",
    ".md",
    ".rss",
    ".svg",
    ".toml",
    ".txt",
    ".webmanifest",
    ".xhtml",
    ".xml",
    ".yaml",
    ".yml",
}
KNOWN_BINARY_EXTENSIONS = {
    ".7z",
    ".avif",
    ".bmp",
    ".eot",
    ".gif",
    ".gz",
    ".ico",
    ".jpeg",
    ".jpg",
    ".mp3",
    ".mp4",
    ".ogg",
    ".otf",
    ".pdf",
    ".png",
    ".tar",
    ".tgz",
    ".tif",
    ".tiff",
    ".ttf",
    ".wasm",
    ".wav",
    ".webp",
    ".woff",
    ".woff2",
    ".zip",
}

# Files/directories with these names cannot be part of a public web artifact.
# Failing closed is preferable to silently copying a private checkout when a
# caller accidentally points --source-web at a broad directory.
PRIVATE_PATH_PARTS = {
    ".env",
    ".git",
    ".planning",
    ".playwright-mcp",
    "00_sources",
    "01_core-methodology",
    "02_factor-maps",
    "03_sops",
    "04_checklists",
    "05_templates",
    "06_prompt-bank",
    "07_client-workspaces",
    "08_experiments",
    "09_sales-packaging",
    "11_dreamwood_offer",
    "12_knowledge-base",
    "99_original_research",
    "meili_data",
    "private",
    "secrets",
}
PRIVATE_SUFFIXES = {".db", ".db3", ".log", ".sqlite", ".sqlite3", ".zip"}
EXCLUDED_SOURCE_EXACT = {"manifest.json"}
EXCLUDED_SOURCE_PREFIXES = {"knowledge"}
STARTUP_PERSONAL_ASSET_PATHS = {
    "alex-v4-static-shell.css",
    "alex-v4-static-shell.js",
    "static/alex-personal-shell-v1.css",
    "static/alex-v4-static-shell.css",
    "static/alex-v4-static-shell.js",
    "static/base2026-personal-v4-presentation.css",
    "static/wordpress-v4-footer.css",
    "static/wordpress-v4-header.css",
    "static/wordpress-v4-header.js",
}

# These markers are unsafe in a public static tree even when they occur in a
# file with an otherwise harmless extension.  The root generated manifest is
# handled by the explicit exclusion above because it is a known local release
# index; the final artifact must still be clean.
LOCAL_PATH_PATTERNS = (
    re.compile(r"/Users/[A-Za-z0-9._+@-]+(?:/|$)"),
    re.compile(r"/private/var/"),
    re.compile(r"/var/www/"),
    re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]"),
    re.compile(r"file://", re.IGNORECASE),
    re.compile(r"https?://(?:127\.0\.0\.1|localhost)(?::\d+)?", re.IGNORECASE),
)
PRIVATE_TOKEN_PATTERNS = (
    re.compile(r"(?:^|[\\/])\.planning(?:[\\/]|$)", re.IGNORECASE),
    re.compile(r"(?:^|[\\/])\.hermes(?:[\\/]|$)", re.IGNORECASE),
    re.compile(r"(?:^|[\\/])12_knowledge-base(?:[\\/]|$)", re.IGNORECASE),
    re.compile(r"PRIVATE_BASE2026_WORK_INBOX", re.IGNORECASE),
    re.compile(r"(?:^|[\\/])meili_data(?:[\\/]|$)", re.IGNORECASE),
)

# A redirect note may intentionally retain an old URL.  The marker is explicit
# rather than inferred from a filename, so an arbitrary stale canonical cannot
# evade the final scan merely by being called redirects.html.
INTENTIONAL_REDIRECT_MARKER = "base2026: intentional-old-domain-redirect-documentation"


class ReleaseBuildError(ValueError):
    """Raised for a fail-closed input, transformation, or verification error."""


@dataclass
class ReplacementCounts:
    """Aggregate replacement counters included in the machine receipt."""

    old_base2026_origin_to_root: int = 0
    old_search_prefix_to_api: int = 0
    internal_knowledge_paths_to_root: int = 0
    wordpress_routes_absolutized: int = 0
    redirect_documentation_preserved: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "old_base2026_origin_to_root": self.old_base2026_origin_to_root,
            "old_search_prefix_to_api": self.old_search_prefix_to_api,
            "internal_knowledge_paths_to_root": self.internal_knowledge_paths_to_root,
            "wordpress_routes_absolutized": self.wordpress_routes_absolutized,
            "redirect_documentation_preserved": self.redirect_documentation_preserved,
        }

    def add(self, other: "ReplacementCounts") -> None:
        for key in self.as_dict():
            setattr(self, key, getattr(self, key) + getattr(other, key))


@dataclass
class TransformResult:
    text: str
    replacements: ReplacementCounts = field(default_factory=ReplacementCounts)
    changed: bool = False


@dataclass(frozen=True)
class FileRecord:
    relative_path: str
    source_sha256: str
    artifact_sha256: str
    source_size: int
    artifact_size: int
    kind: str
    changed: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "path": self.relative_path,
            "source_sha256": self.source_sha256,
            "artifact_sha256": self.artifact_sha256,
            "source_bytes": self.source_size,
            "artifact_bytes": self.artifact_size,
            "kind": self.kind,
            "changed": self.changed,
        }


def _is_relative_to(path: Path, parent: Path) -> bool:
    """Python 3.9-compatible ``Path.is_relative_to``."""

    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _protected_ancestors() -> tuple[Path, ...]:
    """Return roots that are never safe as a source or output directory."""

    script_root = Path(__file__).resolve().parents[1]
    cwd = Path.cwd().resolve()
    roots = {
        Path("/").resolve(),
        Path.home().resolve(),
        script_root,
        cwd,
    }
    # If the repository itself is nested below a broad path, that ancestor is
    # also unsafe (for example passing the migration parent instead of DW/base2026).
    roots.update(script_root.parents)
    roots.update(cwd.parents)
    return tuple(sorted(roots, key=lambda item: (len(item.parts), str(item))))


def _reject_broad_path(path: Path, label: str) -> None:
    resolved = path.resolve(strict=False)
    if len(resolved.parts) <= 2:
        raise ReleaseBuildError(f"refusing broad {label} path: {resolved}")
    for protected in _protected_ancestors():
        if resolved == protected:
            raise ReleaseBuildError(f"refusing broad {label} path: {resolved}")


def validate_paths(source_web: Path | str, out: Path | str) -> tuple[Path, Path]:
    """Validate source/output boundaries before any output mutation."""

    source_input = Path(source_web).expanduser()
    output_input = Path(out).expanduser()
    if source_input.is_symlink():
        raise ReleaseBuildError(f"refusing symlink source-web directory: {source_input}")
    if output_input.is_symlink():
        raise ReleaseBuildError(f"refusing symlink output directory: {output_input}")
    source = source_input.resolve(strict=False)
    output = output_input.resolve(strict=False)

    _reject_broad_path(source, "source-web")
    _reject_broad_path(output, "output")

    if not source.exists() or not source.is_dir():
        raise ReleaseBuildError(f"--source-web must be an existing directory: {source}")
    if source == output:
        raise ReleaseBuildError("--source-web and --out must be different paths")
    if output.exists():
        raise ReleaseBuildError(
            f"refusing existing output directory (would overwrite data): {output}"
        )
    if not output.parent.exists() or not output.parent.is_dir():
        raise ReleaseBuildError(f"output parent must already exist: {output.parent}")

    # Same path, nested output, and source/output aliases are all unsafe.  The
    # nested checks also prevent an output tree from being walked as input.
    if _is_relative_to(output, source) or _is_relative_to(source, output):
        raise ReleaseBuildError("--source-web and --out must not be nested")

    # The output's parent may be a source sibling, but never the source itself.
    if output.parent == source:
        raise ReleaseBuildError("output parent must not be --source-web")
    return source, output


def _relative_files(root: Path) -> list[Path]:
    """Return regular files in deterministic order and reject symlinks."""

    files: list[Path] = []
    for current, directories, filenames in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        directories.sort()
        filenames.sort()
        for directory in tuple(directories):
            candidate = current_path / directory
            if candidate.is_symlink():
                raise ReleaseBuildError(f"refusing symlink in source-web: {candidate}")
        for filename in filenames:
            candidate = current_path / filename
            if candidate.is_symlink():
                raise ReleaseBuildError(f"refusing symlink in source-web: {candidate}")
            if not candidate.is_file():
                raise ReleaseBuildError(f"source-web entry is not a regular file: {candidate}")
            files.append(candidate.relative_to(root))
    if not files:
        raise ReleaseBuildError("--source-web contains no public files")
    return files


def _validate_public_relative_path(relative_path: Path) -> None:
    parts = relative_path.parts
    lowered_parts = {part.casefold() for part in parts}
    if lowered_parts & PRIVATE_PATH_PARTS:
        raise ReleaseBuildError(
            f"private path is not a public web artifact: {relative_path.as_posix()}"
        )
    name = relative_path.name.casefold()
    if name.startswith(".env") or name in {"credentials.json", "secrets.json"}:
        raise ReleaseBuildError(
            f"private file is not a public web artifact: {relative_path.as_posix()}"
        )
    if relative_path.suffix.casefold() in PRIVATE_SUFFIXES:
        raise ReleaseBuildError(
            f"private/database/archive file is not a public web artifact: {relative_path.as_posix()}"
        )


def _is_excluded_source_path(relative_path: Path) -> bool:
    if relative_path.as_posix() in EXCLUDED_SOURCE_EXACT:
        return True
    return bool(relative_path.parts) and relative_path.parts[0].casefold() in EXCLUDED_SOURCE_PREFIXES


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _is_text_file(relative_path: Path, payload: bytes) -> bool:
    """Classify text conservatively while allowing arbitrary binary assets."""

    if relative_path.suffix.casefold() in KNOWN_BINARY_EXTENSIONS:
        return False
    if b"\x00" in payload:
        return False
    try:
        payload.decode("utf-8")
    except UnicodeDecodeError:
        return False
    if relative_path.suffix.casefold() in TEXT_EXTENSIONS:
        return True
    # Unknown extensions are accepted as text only when they are overwhelmingly
    # printable UTF-8.  This keeps a .bin/image fixture byte-preserving.
    if not payload:
        return True
    controls = sum(1 for byte in payload if byte < 9 or 13 < byte < 32)
    return controls / len(payload) < 0.01


def _route_parts(token: str) -> tuple[str, str]:
    """Split a URL path token into route path and query/fragment suffix."""

    candidates = [index for index in (token.find("?"), token.find("#")) if index >= 0]
    if not candidates:
        return token, ""
    index = min(candidates)
    return token[:index], token[index:]


def _map_product_path(path: str) -> str | None:
    """Map a path beginning at the old Base2026 mount to root."""

    if path == OLD_BASE2026_PREFIX:
        return "/"
    if path.startswith(OLD_BASE2026_PREFIX + "/"):
        remainder = path[len(OLD_BASE2026_PREFIX) :]
        return remainder or "/"
    return None


def _map_search_path(path: str) -> str | None:
    if path == OLD_SEARCH_PREFIX:
        return NEW_SEARCH_PREFIX
    if path.startswith(OLD_SEARCH_PREFIX + "/"):
        return NEW_SEARCH_PREFIX + path[len(OLD_SEARCH_PREFIX) :]
    return None


def _map_old_origin_url(full_url: str, counts: ReplacementCounts) -> str:
    """Transform one old-host URL, leaving old WordPress URLs absolute."""

    parsed = urlsplit(full_url)
    if parsed.hostname is None or parsed.hostname.casefold() != "aggressorbulkit.online":
        return full_url

    product_path = _map_product_path(parsed.path)
    if product_path is not None:
        counts.old_base2026_origin_to_root += 1
        return urlunsplit(("https", "base2026.dev", product_path, parsed.query, parsed.fragment))

    search_path = _map_search_path(parsed.path)
    if search_path is not None:
        counts.old_search_prefix_to_api += 1
        return urlunsplit(("https", "base2026.dev", search_path, parsed.query, parsed.fragment))

    # A scheme-relative WordPress route would otherwise resolve against
    # base2026.dev after deployment; make it intentionally absolute.
    if full_url.startswith("//"):
        return urlunsplit(("https", "aggressorbulkit.online", parsed.path, parsed.query, parsed.fragment))
    return full_url


# Match an old-host URL up to normal text/markup delimiters.  The callback then
# uses urllib's parser, avoiding accidental substring replacements in external
# creator URLs.
OLD_ORIGIN_URL_RE = re.compile(
    r"(?P<url>(?:https?:)?//aggressorbulkit\.online(?:/[^\s\"'<>]*)?)",
    re.IGNORECASE,
)
MARKDOWN_WRAPPED_URL_RE = re.compile(
    r"\[(?P<url>https?://[^\]\s()]+)\]\((?P=url)\)",
    re.IGNORECASE,
)


def _base_root_segments(public_root_names: Iterable[str] | None) -> set[str]:
    # These are stable public route families in the current artifact.  A build
    # also adds the actual source root names, making the transformer generic for
    # future static routes without treating every unknown root path as Base2026.
    names = {
        "api.html",
        "api-index.json",
        "analytics.html",
        "ai-visibility-pages",
        "compare",
        "creators",
        "index.html",
        "llms.txt",
        "methodology.html",
        "root-llms.txt",
        "search",
        "search.html",
        "sitemap.xml",
        "sitemaps",
        "solutions",
        "sources",
        "static",
        "topics",
    }
    if public_root_names:
        names.update(str(name).casefold() for name in public_root_names)
    return names


def _looks_like_base_root_path(path: str, base_segments: set[str]) -> bool:
    if path in {"/api", "/api/"} or path.startswith("/api/"):
        return True
    segment = path[1:].split("/", 1)[0].casefold() if path.startswith("/") else ""
    return segment in base_segments


# Product/search paths are safe to replace anywhere in a text artifact (for
# example in the JS runtime config or a JSON URL).  WordPress paths are handled
# only in URL-bearing HTML/CSS contexts below; a broad slash regex would corrupt
# JavaScript regular expressions, CSS arithmetic, and closing HTML tags.
ROOT_PRODUCT_URL_RE = re.compile(
    r"(?<![A-Za-z0-9_:/<])(?P<path>/(?:knowledge-search|knowledge)(?:[^\s\"'<>]*)?)",
    re.IGNORECASE,
)
HTML_ROOT_ATTRIBUTE_RE = re.compile(
    r"(?P<prefix>\b(?:href|src|action|formaction|poster|cite)\s*=\s*)"
    r"(?P<quote>[\"'])(?P<path>/[^\s\"'<>]*)(?P=quote)",
    re.IGNORECASE,
)
CSS_ROOT_URL_RE = re.compile(
    r"(?P<prefix>\burl\(\s*)(?P<quote>[\"']?)(?P<path>/[^\s\"'<>)]*)"
    r"(?P=quote)(?P<suffix>\s*\))",
    re.IGNORECASE,
)


def transform_text(
    text: str,
    *,
    public_root_names: Iterable[str] | None = None,
    intentional_redirect_documentation: bool = False,
    standalone_startup: bool = False,
) -> TransformResult:
    """Transform public text and return replacement counters.

    ``intentional_redirect_documentation`` is only enabled for a file carrying
    :data:`INTENTIONAL_REDIRECT_MARKER`; such a file is copied verbatim and is
    the sole documented exception to the old-domain post-build scan.
    """

    if intentional_redirect_documentation:
        return TransformResult(
            text=text,
            replacements=ReplacementCounts(redirect_documentation_preserved=1),
            changed=False,
        )

    counts = ReplacementCounts()

    def replace_old_origin(match: re.Match[str]) -> str:
        mapped = _map_old_origin_url(match.group("url"), counts)
        if standalone_startup and "aggressorbulkit.online" in mapped.casefold():
            counts.wordpress_routes_absolutized += 1
            return BASE2026_ORIGIN + "/"
        return mapped

    transformed = OLD_ORIGIN_URL_RE.sub(replace_old_origin, text)
    transformed = MARKDOWN_WRAPPED_URL_RE.sub(lambda match: match.group("url"), transformed)
    transformed = re.sub(
        r'(window\.BASE2026_ASSET_VERSION\s*=\s*")[^"]+("\s*;)',
        rf'\g<1>{ASSET_VERSION}\g<2>',
        transformed,
    )
    transformed = re.sub(
        r'(meili\.js\?v=)[^"\'&<\s]+',
        rf'\g<1>{ASSET_VERSION}',
        transformed,
    )
    base_segments = _base_root_segments(public_root_names)

    # First handle attributes/functions so a mapped Base2026 path is not
    # mistaken for an unknown WordPress path in a later pass.
    def replace_attribute(match: re.Match[str]) -> str:
        path = match.group("path")
        route_path, suffix = _route_parts(path)
        product_path = _map_product_path(route_path)
        if product_path is not None:
            counts.internal_knowledge_paths_to_root += 1
            mapped = product_path + suffix
        else:
            search_path = _map_search_path(route_path)
            if search_path is not None:
                counts.old_search_prefix_to_api += 1
                mapped = search_path + suffix
            elif _looks_like_base_root_path(route_path, base_segments):
                mapped = path
            elif standalone_startup:
                mapped = path
            else:
                counts.wordpress_routes_absolutized += 1
                mapped = OLD_WORDPRESS_ORIGIN + path
        return match.group("prefix") + match.group("quote") + mapped + match.group("quote")

    transformed = HTML_ROOT_ATTRIBUTE_RE.sub(replace_attribute, transformed)

    def replace_css_url(match: re.Match[str]) -> str:
        path = match.group("path")
        route_path, suffix = _route_parts(path)
        product_path = _map_product_path(route_path)
        if product_path is not None:
            counts.internal_knowledge_paths_to_root += 1
            mapped = product_path + suffix
        else:
            search_path = _map_search_path(route_path)
            if search_path is not None:
                counts.old_search_prefix_to_api += 1
                mapped = search_path + suffix
            elif _looks_like_base_root_path(route_path, base_segments):
                mapped = path
            elif standalone_startup:
                mapped = path
            else:
                counts.wordpress_routes_absolutized += 1
                mapped = OLD_WORDPRESS_ORIGIN + path
        return match.group("prefix") + match.group("quote") + mapped + match.group("quote") + match.group("suffix")

    transformed = CSS_ROOT_URL_RE.sub(replace_css_url, transformed)

    def replace_product_path(match: re.Match[str]) -> str:
        token = match.group("path")
        # Scheme-relative URLs are external URLs, not root-relative paths.
        if token.startswith("//"):
            return token
        route_path, suffix = _route_parts(token)
        product_path = _map_product_path(route_path)
        if product_path is not None:
            counts.internal_knowledge_paths_to_root += 1
            return product_path + suffix
        search_path = _map_search_path(route_path)
        if search_path is not None:
            counts.old_search_prefix_to_api += 1
            return search_path + suffix
        return token

    transformed = ROOT_PRODUCT_URL_RE.sub(replace_product_path, transformed)
    return TransformResult(
        text=transformed,
        replacements=counts,
        changed=transformed != text,
    )


OLD_BASE2026_CANONICAL_RE = re.compile(
    r"(?:https?:)?//aggressorbulkit\.online/knowledge(?:[/ ?#]|$)",
    re.IGNORECASE,
)
BROKEN_KNOWLEDGE_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9._-])/(?:knowledge)(?:/|[?#]|$)",
    re.IGNORECASE,
)


def scan_for_broken_paths(
    text: str, *, intentional_redirect_documentation: bool = False
) -> dict[str, int]:
    """Return old-domain/product path counts found in a final text artifact."""

    if intentional_redirect_documentation:
        return {"old_base2026_canonical_origin": 0, "broken_knowledge_product_path": 0}
    return {
        "old_base2026_canonical_origin": len(OLD_BASE2026_CANONICAL_RE.findall(text)),
        "broken_knowledge_product_path": len(BROKEN_KNOWLEDGE_PATH_RE.findall(text)),
    }


def _tree_digest(records: Sequence[FileRecord], *, source: bool) -> str:
    digest = hashlib.sha256()
    for record in records:
        digest.update(record.relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update((record.source_sha256 if source else record.artifact_sha256).encode("ascii"))
        digest.update(b"\0")
        digest.update(str(record.source_size if source else record.artifact_size).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _write_bytes(path: Path, payload: bytes, source_mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    # Keep executable/static permissions where the source explicitly has them,
    # without copying timestamps or other host-specific metadata.
    path.chmod(stat.S_IMODE(source_mode))


def _format_json(payload: Mapping[str, object]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


ROBOTS_PAYLOAD = "User-agent: *\nAllow: /\n\nSitemap: https://base2026.dev/sitemap.xml\n"
HEADERS_PAYLOAD = """/*
  Cache-Control: no-cache
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  X-Frame-Options: SAMEORIGIN
  Permissions-Policy: accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()

/static/*
  Cache-Control: no-cache
"""


def _rewrite_public_api_docs(relative_path: Path, text: str) -> str:
    """Make the small public API docs match the Cloudflare search contract."""

    path = relative_path.as_posix()
    if path == "static/meili.js":
        return text.replace(
            'window.BASE2026_MEILI_URL || "http://127.0.0.1:7700"',
            'window.BASE2026_MEILI_URL || "/api/search"',
        )

    if path == "ai-visibility-resources.html":
        return text.replace(
            "topics/content-strategy.html",
            "topics/ai-visibility-content-strategy.html",
        )

    if path == "static/manifest.json":
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ReleaseBuildError(f"static/manifest.json is not valid JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise ReleaseBuildError("static/manifest.json must contain a JSON object")
        # Keep the public manifest truthful to the files that are actually
        # present in this static artifact; never invent private/legacy dataset
        # files from the source release's local bookkeeping.
        payload["files"] = [
            "documents.jsonl",
            "insight_cards.jsonl",
            "passages.jsonl",
            "topic_signal_briefs.jsonl",
        ]
        return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    if path == "search/index.html":
        # This is a legacy no-index alias.  Its relative links must work at
        # /search/ and /search/index.html on a root-mounted static host.
        return text.replace('href="./', 'href="/').replace('src="../static/', 'src="/static/')

    if path == "llms.txt":
        text = text.replace(
            "- Search proxy: https://base2026.dev/api/search/multi-search",
            "- Search API: https://base2026.dev/api/search/multi-search",
        )
        text = text.replace(
            "Use the search workspace for exploration, topic pages for canonical topic evidence, source pages for source-level attribution, and topic signal briefs for compact summaries of repeated creator signals. Use the public JSONL files for offline analysis and the search proxy only when live Meilisearch ranking is needed. Cite the canonical source or topic page when referencing Base2026 evidence.",
            "Use the search workspace for exploration, topic pages for canonical topic evidence, source pages for source-level attribution, and topic signal briefs for compact summaries of repeated creator signals. Use the public JSONL files for offline analysis or the read-only Meilisearch-compatible Worker API backed by D1 FTS5 when live search ranking is needed; no browser key is required. Cite the canonical source or topic page when referencing Base2026 evidence.",
        )
        return text

    if path == "api.html":
        old = (
            "<h2>Search endpoint</h2><p>The public UI searches through a server-side Meilisearch proxy:</p>"
            "<p><code>POST /api/search/multi-search</code></p>"
            "<p>The proxy injects the public search key server-side. Do not call Meilisearch directly and do not expect private data, raw captions, or write access. External integrations should prefer the static JSONL files unless they need live search ranking.</p>"
        )
        new = (
            "<h2>Search endpoint</h2><p>The public UI and compatible integrations use a read-only Meilisearch-compatible Cloudflare Worker API backed by D1 FTS5:</p>"
            "<p><code>POST /api/search/multi-search</code></p>"
            "<p>No browser key is required. The endpoint does not expose Meilisearch credentials, private data, raw captions, or write access. External integrations should prefer the static JSONL files unless they need live search ranking.</p>"
        )
        if old not in text:
            # Keep the build fail-closed if the source contract changes and this
            # migration-specific wording silently stops being updated.
            if "server-side Meilisearch proxy" in text or "injects the public search key" in text:
                raise ReleaseBuildError("api.html contains an unhandled legacy search-proxy contract")
        return text.replace(old, new)

    if path == "api-index.json":
        old_description = (
            '"description": "Server-side Meilisearch multi-search proxy used by the public UI. Prefer static JSONL for bulk/offline analysis; use this endpoint when live search ranking is needed."'
        )
        new_description = (
            '"description": "Read-only Meilisearch-compatible Cloudflare Worker API backed by D1 FTS5. No browser key is required; prefer static JSONL for bulk/offline analysis and use this endpoint when live search ranking is needed.",\n'
            '      "backend": "cloudflare_worker_d1_fts5",\n'
            '      "browser_key_required": false'
        )
        if old_description not in text:
            if "Server-side Meilisearch multi-search proxy" in text:
                raise ReleaseBuildError("api-index.json contains an unhandled legacy search-proxy contract")
            return text
        return text.replace(old_description, new_description)

    return text


STARTUP_HEADER_RE = re.compile(
    r'<header\b[^>]*class=["\'][^"\']*(?:site-header|ay-v2-header)[^"\']*["\'][^>]*>.*?</header>',
    re.IGNORECASE | re.DOTALL,
)
STARTUP_FOOTER_RE = re.compile(
    r'<footer\b[^>]*class=["\'][^"\']*site-footer[^"\']*["\'][^>]*>.*?</footer>',
    re.IGNORECASE | re.DOTALL,
)
STARTUP_SHELL_LINK = '<link rel="stylesheet" href="/static/base2026-startup-shell.css?v=20260820-02">'
STARTUP_FAVICON_LINK = '<link rel="icon" href="/static/base2026-mark.svg" type="image/svg+xml">'
PERSONAL_ASSET_TAG_RE = re.compile(
    r'\s*<(?:link|script)\b[^>]*(?:wordpress-v4|alex-v4-static-shell|base2026-personal-v4-presentation|data-shell-authority|data-presentation-authority)[^>]*>(?:\s*</script>)?',
    re.IGNORECASE,
)
PERSONAL_IMAGE_TAG_RE = re.compile(
    r'\s*<(?:meta|link)\b[^>]*alex-yarosh[^>]*>', re.IGNORECASE
)
PERSONAL_ROUTE_ATTRIBUTE_RE = re.compile(
    r'(?P<prefix>\b(?:href|action|formaction)\s*=\s*["\'])'
    r'/(?:services|pricing|about|research|results|insights|ai-visibility-audit|ai-visibility-diagnostic-audit|ai-visibility-source-footprint|answer-ready-service-pages|entity-trust-source-intelligence|technical-seo-geo-foundation|wp-admin)(?:/[^"\']*)?'
    r'(?P<suffix>["\'])',
    re.IGNORECASE,
)
LEGACY_RESEARCH_NAV_RE = re.compile(
    r'<nav\b[^>]*class=["\'][^"\']*b26-research-nav[^"\']*["\'][^>]*>.*?</nav>',
    re.IGNORECASE | re.DOTALL,
)
LEGACY_COOKIE_UI_RE = re.compile(
    r'<(?:section|dialog)\b[^>]*class=["\'][^"\']*cookie-(?:banner|dialog)[^"\']*["\'][^>]*>.*?</(?:section|dialog)>',
    re.IGNORECASE | re.DOTALL,
)
LEGACY_COOKIE_SCRIPT_RE = re.compile(
    r'\s*<script\b[^>]*src=["\'][^"\']*cookie-consent\.js[^"\']*["\'][^>]*>\s*</script>',
    re.IGNORECASE,
)


def _apply_startup_shell(text: str, header_html: str, footer_html: str) -> str:
    """Replace the inherited personal-site chrome on a public HTML page."""

    if STARTUP_SHELL_LINK not in text:
        if "</head>" in text:
            text = text.replace("</head>", f"  {STARTUP_SHELL_LINK}\n</head>", 1)
        else:
            text = STARTUP_SHELL_LINK + "\n" + text
    text = PERSONAL_ASSET_TAG_RE.sub("", text)
    text = PERSONAL_IMAGE_TAG_RE.sub("", text)
    text = LEGACY_RESEARCH_NAV_RE.sub("", text)
    text = LEGACY_COOKIE_UI_RE.sub("", text)
    text = LEGACY_COOKIE_SCRIPT_RE.sub("", text)
    if STARTUP_FAVICON_LINK not in text and "</head>" in text:
        text = text.replace("</head>", f"  {STARTUP_FAVICON_LINK}\n</head>", 1)
    text = re.sub(
        r'(<a\b[^>]*href=["\'])/ai-visibility-audit/(?:[^"\']*)?(["\'][^>]*>)\s*Get free snapshot\s*</a>',
        r'\1/methodology.html\2Read the methodology</a>',
        text,
        flags=re.IGNORECASE,
    )
    text = PERSONAL_ROUTE_ATTRIBUTE_RE.sub(r'\g<prefix>/solutions/\g<suffix>', text)
    for old_class in ("ay-alex-v4-static", "ay-stitch-home-v3", "ay-stitch-home-v4"):
        text = text.replace(old_class, "")
    text, header_count = STARTUP_HEADER_RE.subn(header_html, text, count=1)
    text, footer_count = STARTUP_FOOTER_RE.subn(footer_html, text, count=1)
    if "Alex Yarosh primary header" in text or "Get Free Snapshot" in text:
        raise ReleaseBuildError("HTML contains an unhandled personal-site header")
    if header_count != footer_count:
        raise ReleaseBuildError("HTML shell replacement was incomplete")
    return text.replace("Alex Yarosh profile photo", "Base2026 project preview")


def _render_startup_page(template: str, header_html: str, footer_html: str) -> bytes:
    if template.count("{{STARTUP_HEADER}}") != 1 or template.count("{{STARTUP_FOOTER}}") != 1:
        raise ReleaseBuildError("startup page template must contain one header and footer placeholder")
    if STARTUP_FAVICON_LINK not in template and "</head>" in template:
        template = template.replace("</head>", f"{STARTUP_FAVICON_LINK}</head>", 1)
    return template.replace("{{STARTUP_HEADER}}", header_html).replace(
        "{{STARTUP_FOOTER}}", footer_html
    ).encode("utf-8")


def _public_route_for_file(relative_path: Path) -> str:
    path = relative_path.as_posix()
    if path == "index.html":
        return "/"
    if path.endswith("/index.html"):
        return "/" + path[: -len("index.html")]
    return "/" + path


def _remove_excluded_startup_route_references(text: str, routes: Iterable[str]) -> str:
    """Remove retired personal-service pages from sitemaps and internal links."""

    for route in sorted(routes, key=len, reverse=True):
        escaped_url = re.escape(BASE2026_ORIGIN + route)
        if "<urlset" in text:
            text = re.sub(
                rf"\s*<url>.*?<loc>{escaped_url}</loc>.*?</url>",
                "",
                text,
                flags=re.IGNORECASE | re.DOTALL,
            )
        text = text.replace(f'href="{route}"', 'href="/solutions/"')
        text = text.replace(f"href='{route}'", "href='/solutions/'")
        text = text.replace(BASE2026_ORIGIN + route, BASE2026_ORIGIN + "/solutions/")
    return text


def _rewrite_workspace_html(text: str) -> str:
    """Move the former root search UI to /workspace/ without breaking assets or SEO."""

    text = text.replace(
        "<title>Base2026 SEO, GEO &amp; AEO Source Library</title>",
        "<title>Base2026 Search Workspace | SEO, GEO &amp; AEO Sources</title>",
    )
    if '<base href="/">' not in text:
        if "</title>" in text:
            text = text.replace("</title>", '</title>\n    <base href="/">', 1)
        elif "<head>" in text:
            text = text.replace("<head>", '<head>\n    <base href="/">', 1)
        else:
            text = '<base href="/">\n' + text
    text = re.sub(
        r'<link rel="canonical" href="https://base2026\.dev/"\s*/?>',
        '<link rel="canonical" href="https://base2026.dev/workspace/" />',
        text,
    )
    text = text.replace(
        '<meta property="og:url" content="https://base2026.dev/" />',
        '<meta property="og:url" content="https://base2026.dev/workspace/" />',
    )
    text = text.replace("https://base2026.dev/#website", "https://base2026.dev/workspace/#website")
    text = text.replace("https://base2026.dev/#collection", "https://base2026.dev/workspace/#collection")
    text = text.replace(
        '"url": "https://base2026.dev/"',
        '"url": "https://base2026.dev/workspace/"',
    )
    text = text.replace(
        '"target": "https://base2026.dev/?q={search_term_string}"',
        '"target": "https://base2026.dev/workspace/?q={search_term_string}"',
    )
    # The legacy root uses both HTML attributes and JavaScript fetch() strings
    # for static assets.  Once the page lives at /workspace/, every quoted
    # relative static path must be rooted or the browser requests
    # /workspace/static/* instead of /static/*.
    for quote in ('"', "'"):
        text = text.replace(f"{quote}./static/", f"{quote}/static/")
        text = text.replace(f"{quote}static/", f"{quote}/static/")
    text = text.replace('href="./story.html"', 'href="/about.html"')
    text = text.replace("href='./story.html'", "href='/about.html'")
    return text


def _public_safety_findings(text: str) -> dict[str, int]:
    """Count local/private path markers that must never reach the artifact."""

    return {
        "local_path_markers": sum(len(pattern.findall(text)) for pattern in LOCAL_PATH_PATTERNS),
        "private_token_markers": sum(len(pattern.findall(text)) for pattern in PRIVATE_TOKEN_PATTERNS),
    }


def _artifact_files(root: Path, excluded: set[str]) -> list[Path]:
    return sorted(
        (
            candidate.relative_to(root)
            for candidate in root.rglob("*")
            if candidate.is_file() and candidate.relative_to(root).as_posix() not in excluded
        ),
        key=lambda item: item.as_posix(),
    )


def _receipt(
    *,
    source_scanned_file_count: int,
    source_records: Sequence[FileRecord],
    artifact_records: Sequence[FileRecord],
    excluded_source_files: Sequence[str],
    source_bytes: int,
    artifact_bytes: int,
    replacements: ReplacementCounts,
    verification: Mapping[str, object],
    output_file_count: int,
) -> dict[str, object]:
    source_file_count = source_scanned_file_count
    source_public_file_count = len(source_records)
    artifact_file_count = len(artifact_records)
    changed_files = sum(1 for record in artifact_records if record.changed)
    text_files = sum(1 for record in artifact_records if record.kind == "text")
    binary_files = sum(1 for record in artifact_records if record.kind == "binary")
    binary_preserved = sum(
        1
        for record in artifact_records
        if record.kind == "binary" and not record.changed and record.source_sha256 == record.artifact_sha256
    )
    source_tree_sha256 = _tree_digest(source_records, source=True)
    artifact_tree_sha256 = _tree_digest(artifact_records, source=False)
    file_entries = [record.as_dict() for record in artifact_records]

    return {
        "schema": SCHEMA,
        "source": {
            "file_count": source_file_count,
            "public_file_count": source_public_file_count,
            "excluded_file_count": len(excluded_source_files),
            "byte_count": source_bytes,
            "tree_sha256": source_tree_sha256,
        },
        "artifact": {
            "file_count": artifact_file_count,
            "byte_count": artifact_bytes,
            "tree_sha256": artifact_tree_sha256,
        },
        "output": {
            "file_count": output_file_count,
            "metadata_files": [ASSETSIGNORE_FILENAME, RECEIPT_FILENAME],
            "served_file_count": artifact_file_count,
        },
        "counts": {
            "source_files": source_file_count,
            "source_public_files": source_public_file_count,
            "excluded_source_files": len(excluded_source_files),
            "artifact_files": artifact_file_count,
            "output_files": output_file_count,
            "text_files": text_files,
            "binary_files": binary_files,
            "changed_files": changed_files,
            "source_bytes": source_bytes,
            "artifact_bytes": artifact_bytes,
            "binary_files_byte_preserved": binary_preserved,
        },
        "hashes": {
            "source_tree_sha256": source_tree_sha256,
            "artifact_tree_sha256": artifact_tree_sha256,
        },
        "replacements": replacements.as_dict(),
        "verification": dict(verification),
        "excluded_source_paths": list(excluded_source_files),
        "files": file_entries,
    }


def build_release(
    source_web: Path | str,
    out: Path | str,
    homepage_template: Path | str | None = None,
    homepage_stylesheet: Path | str | None = None,
) -> dict[str, object]:
    """Build and verify a release; return the deterministic JSON receipt."""

    source, output = validate_paths(source_web, out)
    if bool(homepage_template) != bool(homepage_stylesheet):
        raise ReleaseBuildError("homepage template and stylesheet must be supplied together")
    homepage_template_path = Path(homepage_template).resolve(strict=True) if homepage_template else None
    homepage_stylesheet_path = (
        Path(homepage_stylesheet).resolve(strict=True) if homepage_stylesheet else None
    )
    standalone_startup = bool(homepage_template_path)
    startup_header = DEFAULT_STARTUP_HEADER.read_text(encoding="utf-8").strip() if standalone_startup else ""
    startup_footer = DEFAULT_STARTUP_FOOTER.read_text(encoding="utf-8").strip() if standalone_startup else ""
    startup_shell_css = DEFAULT_STARTUP_SHELL_STYLESHEET.read_bytes() if standalone_startup else b""
    scanned_files = _relative_files(source)
    for relative_path in scanned_files:
        _validate_public_relative_path(relative_path)
    startup_excluded_pages: set[Path] = set()
    if standalone_startup:
        for relative_path in scanned_files:
            if relative_path.suffix.casefold() not in {".html", ".htm", ".xhtml"}:
                continue
            payload = (source / relative_path).read_bytes()
            if len(relative_path.parts) > 1 and (
                b"wp-admin/admin-post.php" in payload or b"admin-post.php" in payload
            ):
                startup_excluded_pages.add(relative_path)
    startup_excluded_routes = {
        _public_route_for_file(relative_path) for relative_path in startup_excluded_pages
    }
    excluded_source_files = [
        relative_path.as_posix()
        for relative_path in scanned_files
        if _is_excluded_source_path(relative_path)
        or relative_path in startup_excluded_pages
        or (standalone_startup and relative_path.as_posix() in STARTUP_PERSONAL_ASSET_PATHS)
    ]
    relative_files = [
        relative_path
        for relative_path in scanned_files
        if relative_path.as_posix() not in set(excluded_source_files)
    ]
    if not relative_files:
        raise ReleaseBuildError("source-web contains no includable public files")

    public_root_names = {
        child.name.casefold()
        for child in source.iterdir()
        if not child.is_symlink()
        and (child.is_dir() or child.is_file())
        and not _is_excluded_source_path(Path(child.name))
    }

    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.build-", dir=str(output.parent)))
    records: list[FileRecord] = []
    replacements = ReplacementCounts()
    source_bytes = 0
    artifact_bytes = 0
    try:
        for relative_path in relative_files:
            source_path = source / relative_path
            source_payload = source_path.read_bytes()
            source_mode = source_path.stat().st_mode
            source_bytes += len(source_payload)
            is_text = _is_text_file(relative_path, source_payload)
            intentional_redirect = (
                is_text and INTENTIONAL_REDIRECT_MARKER in source_payload.decode("utf-8")
            )
            if is_text:
                source_text = source_payload.decode("utf-8")
                transformed = transform_text(
                    source_text,
                    public_root_names=public_root_names,
                    intentional_redirect_documentation=intentional_redirect,
                    standalone_startup=standalone_startup,
                )
                replacements.add(transformed.replacements)
                artifact_text = _rewrite_public_api_docs(relative_path, transformed.text)
                if standalone_startup:
                    artifact_text = _remove_excluded_startup_route_references(
                        artifact_text, startup_excluded_routes
                    )
                if standalone_startup and relative_path.suffix.casefold() in {".html", ".htm", ".xhtml"}:
                    artifact_text = _apply_startup_shell(
                        artifact_text, startup_header, startup_footer
                    )
                artifact_payload = artifact_text.encode("utf-8")
            else:
                artifact_payload = source_payload

            destination = stage / relative_path
            _write_bytes(destination, artifact_payload, source_mode)
            artifact_bytes += len(artifact_payload)
            records.append(
                FileRecord(
                    relative_path=relative_path.as_posix(),
                    source_sha256=_sha256(source_payload),
                    artifact_sha256=_sha256(artifact_payload),
                    source_size=len(source_payload),
                    artifact_size=len(artifact_payload),
                    kind="text" if is_text else "binary",
                    changed=artifact_payload != source_payload,
                )
            )

        def write_generated_public_file(relative_name: str, payload: bytes) -> None:
            """Write a required root file and update its audit record."""

            nonlocal artifact_bytes
            destination = stage / relative_name
            previous_size = 0
            for index, existing in enumerate(records):
                if existing.relative_path == relative_name:
                    previous_size = existing.artifact_size
                    records[index] = FileRecord(
                        relative_path=relative_name,
                        source_sha256=existing.source_sha256,
                        artifact_sha256=_sha256(payload),
                        source_size=existing.source_size,
                        artifact_size=len(payload),
                        kind="text",
                        changed=payload != (source / relative_name).read_bytes(),
                    )
                    break
            else:
                records.append(
                    FileRecord(
                        relative_path=relative_name,
                        source_sha256="",
                        artifact_sha256=_sha256(payload),
                        source_size=0,
                        artifact_size=len(payload),
                        kind="text",
                        changed=True,
                    )
                )
            artifact_bytes += len(payload) - previous_size
            _write_bytes(destination, payload, 0o644)

        write_generated_public_file(ROBOTS_FILENAME, ROBOTS_PAYLOAD.encode("utf-8"))
        write_generated_public_file(HEADERS_FILENAME, HEADERS_PAYLOAD.encode("utf-8"))

        if homepage_template_path and homepage_stylesheet_path:
            current_root = (stage / "index.html").read_text(encoding="utf-8")
            workspace_html = _rewrite_workspace_html(current_root).encode("utf-8")
            homepage_html = homepage_template_path.read_bytes()
            homepage_css = homepage_stylesheet_path.read_bytes()
            write_generated_public_file("workspace/index.html", workspace_html)
            write_generated_public_file("index.html", homepage_html)
            write_generated_public_file("static/base2026-startup-homepage.css", homepage_css)
            write_generated_public_file("static/base2026-startup-shell.css", startup_shell_css)
            write_generated_public_file("static/base2026-forms.js", DEFAULT_FORMS_SCRIPT.read_bytes())
            write_generated_public_file("static/brand/github.svg", DEFAULT_GITHUB_ICON.read_bytes())
            write_generated_public_file("static/brand/x.svg", DEFAULT_X_ICON.read_bytes())
            write_generated_public_file("static/base2026-mark.svg", DEFAULT_MARK_ICON.read_bytes())
            write_generated_public_file(
                "support.html",
                _render_startup_page(
                    DEFAULT_SUPPORT_TEMPLATE.read_text(encoding="utf-8"), startup_header, startup_footer
                ),
            )
            write_generated_public_file(
                "partner.html",
                _render_startup_page(
                    DEFAULT_PARTNER_TEMPLATE.read_text(encoding="utf-8"), startup_header, startup_footer
                ),
            )
            write_generated_public_file(
                "privacy.html",
                _render_startup_page(
                    DEFAULT_PRIVACY_TEMPLATE.read_text(encoding="utf-8"), startup_header, startup_footer
                ),
            )
            write_generated_public_file(
                "about.html",
                _render_startup_page(
                    DEFAULT_ABOUT_TEMPLATE.read_text(encoding="utf-8"), startup_header, startup_footer
                ),
            )

        assetsignore_payload = (
            "# Cloudflare Workers Static Assets metadata exclusions.\n"
            f"{ASSETSIGNORE_FILENAME}\n"
            f"{RECEIPT_FILENAME}\n"
        ).encode("utf-8")
        _write_bytes(stage / ASSETSIGNORE_FILENAME, assetsignore_payload, 0o644)

        # Verify the staged artifact, excluding only generated metadata.  The
        # marker exception is file-local and cannot hide stale paths elsewhere.
        remaining_old_origin = 0
        remaining_knowledge = 0
        redirect_docs = 0
        local_path_markers = 0
        private_token_markers = 0
        personal_site_markers = 0
        personal_shell_markers = 0
        wordpress_form_markers = 0
        personal_route_markers = 0
        manifest_files_match = True
        manifest_checked = False
        for relative_path in _artifact_files(stage, {ASSETSIGNORE_FILENAME, RECEIPT_FILENAME}):
            payload = (stage / relative_path).read_bytes()
            if not _is_text_file(relative_path, payload):
                continue
            text = payload.decode("utf-8")
            intentional = INTENTIONAL_REDIRECT_MARKER in text
            if intentional:
                redirect_docs += 1
            safety = _public_safety_findings(text)
            local_path_markers += safety["local_path_markers"]
            private_token_markers += safety["private_token_markers"]
            if standalone_startup:
                personal_site_markers += text.casefold().count("aggressorbulkit.online")
                if relative_path.suffix.casefold() in {".html", ".htm", ".xhtml"}:
                    personal_shell_markers += sum(
                        text.casefold().count(marker)
                        for marker in (
                            "wordpress-personal-v4",
                            "ay-v2-header",
                            "get free snapshot",
                            "base2026-personal-v4-presentation",
                        )
                    )
                    wordpress_form_markers += sum(
                        text.casefold().count(marker)
                        for marker in ("wp-admin/admin-post.php", "admin-post.php")
                    )
                    personal_route_markers += len(PERSONAL_ROUTE_ATTRIBUTE_RE.findall(text))
            findings = scan_for_broken_paths(
                text, intentional_redirect_documentation=intentional
            )
            remaining_old_origin += findings["old_base2026_canonical_origin"]
            remaining_knowledge += findings["broken_knowledge_product_path"]
            if relative_path.as_posix() == "static/manifest.json":
                manifest_checked = True
                try:
                    manifest = json.loads(text)
                    actual_jsonl = sorted(
                        candidate.name
                        for candidate in (stage / "static").glob("*.jsonl")
                        if candidate.is_file()
                    )
                    manifest_files_match = manifest.get("files") == actual_jsonl
                except (OSError, json.JSONDecodeError, AttributeError):
                    manifest_files_match = False
        if remaining_old_origin or remaining_knowledge:
            raise ReleaseBuildError(
                "final artifact contains stale Base2026 paths: "
                f"old_origin={remaining_old_origin}, knowledge_paths={remaining_knowledge}"
            )
        if local_path_markers or private_token_markers:
            raise ReleaseBuildError(
                "final artifact contains local/private path markers: "
                f"local={local_path_markers}, private={private_token_markers}"
            )
        if personal_site_markers:
            raise ReleaseBuildError(
                "standalone startup artifact contains personal-site origin markers: "
                f"count={personal_site_markers}"
            )
        if personal_shell_markers or wordpress_form_markers or personal_route_markers:
            raise ReleaseBuildError(
                "standalone startup artifact contains personal shell/form markers: "
                f"shell={personal_shell_markers}, forms={wordpress_form_markers}, "
                f"routes={personal_route_markers}"
            )
        if not manifest_files_match:
            raise ReleaseBuildError("static/manifest.json files[] does not match static/*.jsonl")

        # Binary records are checked against source hashes before publication.
        binary_records = [record for record in records if record.kind == "binary"]
        binary_preserved = all(
            record.source_sha256 == record.artifact_sha256 and not record.changed
            for record in binary_records
        )
        if not binary_preserved:
            raise ReleaseBuildError("one or more binary files changed during transformation")

        verification = {
            "old_base2026_canonical_origin_remaining": remaining_old_origin,
            "broken_knowledge_product_paths_remaining": remaining_knowledge,
            "local_path_markers_remaining": local_path_markers,
            "private_token_markers_remaining": private_token_markers,
            "personal_site_origin_markers_remaining": personal_site_markers,
            "personal_shell_markers_remaining": personal_shell_markers,
            "wordpress_form_markers_remaining": wordpress_form_markers,
            "personal_route_markers_remaining": personal_route_markers,
            "static_manifest_files_match": manifest_files_match,
            "static_manifest_checked": manifest_checked,
            "intentional_redirect_documentation_files": redirect_docs,
            "binary_bytes_preserved": binary_preserved,
            "artifact_files_include_required_root_metadata": all(
                (stage / required).is_file() for required in (ROBOTS_FILENAME, HEADERS_FILENAME)
            ),
        }
        receipt = _receipt(
            source_scanned_file_count=len(scanned_files),
            source_records=[
                record
                for record in records
                if record.source_sha256 and (source / record.relative_path).is_file()
            ],
            artifact_records=sorted(records, key=lambda record: record.relative_path),
            excluded_source_files=excluded_source_files,
            source_bytes=source_bytes,
            artifact_bytes=artifact_bytes,
            replacements=replacements,
            verification=verification,
            output_file_count=len(records) + 2,
        )
        _write_bytes(stage / RECEIPT_FILENAME, _format_json(receipt), 0o644)

        # The output did not exist when validated, so this rename cannot clobber
        # an existing user path.  It also ensures callers never see a partial tree.
        stage.replace(output)
        return receipt
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Transform a public Base2026 web artifact for root-domain Cloudflare hosting."
    )
    parser.add_argument("--source-web", required=True, type=Path, help="existing public web artifact directory")
    parser.add_argument("--out", required=True, type=Path, help="new output directory (must not already exist)")
    parser.add_argument(
        "--homepage-template",
        type=Path,
        default=DEFAULT_HOMEPAGE_TEMPLATE,
        help="approved startup homepage HTML overlay",
    )
    parser.add_argument(
        "--homepage-stylesheet",
        type=Path,
        default=DEFAULT_HOMEPAGE_STYLESHEET,
        help="compiled production CSS for the startup homepage",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        receipt = build_release(
            args.source_web,
            args.out,
            homepage_template=args.homepage_template,
            homepage_stylesheet=args.homepage_stylesheet,
        )
    except (OSError, ReleaseBuildError, UnicodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
