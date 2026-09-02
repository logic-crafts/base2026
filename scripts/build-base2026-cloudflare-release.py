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
import html
import json
import os
import re
import shutil
import stat
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
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
DEFAULT_CORE_STYLESHEET = PROJECT_ROOT / "templates" / "base2026-core.css"
DEFAULT_SUPPORT_TEMPLATE = PROJECT_ROOT / "templates" / "base2026-support.html"
DEFAULT_PARTNER_TEMPLATE = PROJECT_ROOT / "templates" / "base2026-partner.html"
DEFAULT_PRIVACY_TEMPLATE = PROJECT_ROOT / "templates" / "base2026-privacy.html"
DEFAULT_ABOUT_TEMPLATE = PROJECT_ROOT / "templates" / "base2026-about.html"
DEFAULT_FOUNDER_TEMPLATE = PROJECT_ROOT / "templates" / "base2026-founder.html"
DEFAULT_DATASET_TEMPLATE = PROJECT_ROOT / "templates" / "base2026-dataset.html"
DEFAULT_JOURNAL_CLOUDFLARE_TEMPLATE = (
    PROJECT_ROOT / "templates" / "base2026-journal-cloudflare.html"
)
DEFAULT_JOURNAL_SOURCE_DIVERSITY_TEMPLATE = (
    PROJECT_ROOT / "templates" / "base2026-journal-source-diversity.html"
)
DEFAULT_JOURNAL_SOURCE_DIVERSITY_IMAGE = (
    PROJECT_ROOT / "static" / "assets" / "base2026-source-diversity.png"
)
DEFAULT_EDITORIAL_MEASUREMENT_IMAGE = (
    PROJECT_ROOT / "static" / "assets" / "base2026-ai-visibility-measurement.png"
)
DEFAULT_BLOG_TEMPLATE = PROJECT_ROOT / "templates" / "base2026-blog-index.html"
DEFAULT_BLOG_STYLESHEET = PROJECT_ROOT / "templates" / "base2026-blog.css"
DEFAULT_BLOG_ARTICLE_STYLESHEET = PROJECT_ROOT / "templates" / "base2026-blog-article.css"
DEFAULT_EVIDENCE_GUIDE_STYLESHEET = PROJECT_ROOT / "templates" / "base2026-evidence-guide.css"
DEFAULT_EVIDENCE_GUIDE_SCRIPT = PROJECT_ROOT / "templates" / "base2026-evidence-guide.js"
DEFAULT_EDITORIAL_CATALOG = (
    PROJECT_ROOT / "cloudflare" / "base2026-worker" / "src" / "editorial-catalog.json"
)
DEFAULT_FOUNDER_STYLESHEET = PROJECT_ROOT / "templates" / "base2026-founder.css"
DEFAULT_FOUNDER_HERO_IMAGE = (
    PROJECT_ROOT / "static" / "assets" / "alex-yarosh-founder-step-wall.webp"
)
DEFAULT_APPLY_RESEARCH_TEMPLATE = PROJECT_ROOT / "templates" / "base2026-apply-research.html"
DEFAULT_AI_VISIBILITY_RESOURCES_TEMPLATE = (
    PROJECT_ROOT / "templates" / "base2026-ai-visibility-resources.html"
)
DEFAULT_FORMS_SCRIPT = PROJECT_ROOT / "templates" / "base2026-forms.js"
DEFAULT_EVIDENCE_BRIEF_SCRIPT = PROJECT_ROOT / "templates" / "base2026-evidence-brief.js"
DEFAULT_MEMBERS_TEMPLATE = PROJECT_ROOT / "templates" / "base2026-my-research.html"
DEFAULT_MEMBERS_STYLESHEET = PROJECT_ROOT / "templates" / "base2026-members.css"
DEFAULT_MEMBERS_SCRIPT = PROJECT_ROOT / "templates" / "base2026-members.js"
DEFAULT_MEMBERS_PRIVACY = PROJECT_ROOT / "templates" / "base2026-members-privacy.html"
DEFAULT_ROADMAP_SCRIPT = PROJECT_ROOT / "web" / "static" / "roadmap.js"
DEFAULT_ROADMAP_PAGE = PROJECT_ROOT / "web" / "static" / "roadmap.html"
DEFAULT_ANALYTICS_PAGE = PROJECT_ROOT / "web" / "static" / "analytics.html"
DEFAULT_API_PAGE = PROJECT_ROOT / "web" / "static" / "api.html"
DEFAULT_API_INDEX = PROJECT_ROOT / "web" / "static" / "api-index.json"
DEFAULT_MCP_PAGE = PROJECT_ROOT / "web" / "static" / "mcp.html"
DEFAULT_INTEGRATIONS_PAGE = PROJECT_ROOT / "web" / "static" / "integrations.html"
DEFAULT_DATA_DICTIONARY = PROJECT_ROOT / "web" / "static" / "data-dictionary.json"
DEFAULT_LLMS = PROJECT_ROOT / "web" / "static" / "llms.txt"
DEFAULT_ROOT_LLMS = PROJECT_ROOT / "web" / "static" / "llms-root.txt"
DEFAULT_GITHUB_ICON = PROJECT_ROOT / "static" / "brand" / "github.svg"
DEFAULT_X_ICON = PROJECT_ROOT / "static" / "brand" / "x.svg"
DEFAULT_MARK_ICON = PROJECT_ROOT / "static" / "base2026-mark.svg"
DEFAULT_EVIDENCE_SEARCH_TEMPLATE = PROJECT_ROOT / "templates" / "base2026-evidence-search.html"
DEFAULT_EVIDENCE_SEARCH_STYLESHEET = PROJECT_ROOT / "templates" / "base2026-evidence-search.css"
DEFAULT_EVIDENCE_SEARCH_SCRIPT = PROJECT_ROOT / "templates" / "base2026-evidence-search.js"

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
EXCLUDED_SOURCE_EXACT = {
    "manifest.json",
    # These are generated by this builder and must not be replayed as served
    # source records when a reviewed candidate is rebuilt.
    ASSETSIGNORE_FILENAME,
    RECEIPT_FILENAME,
}
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
    html_urls_to_extensionless: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "old_base2026_origin_to_root": self.old_base2026_origin_to_root,
            "old_search_prefix_to_api": self.old_search_prefix_to_api,
            "internal_knowledge_paths_to_root": self.internal_knowledge_paths_to_root,
            "wordpress_routes_absolutized": self.wordpress_routes_absolutized,
            "redirect_documentation_preserved": self.redirect_documentation_preserved,
            "html_urls_to_extensionless": self.html_urls_to_extensionless,
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


def _extensionless_html_path(path: str) -> str:
    """Return the URL Cloudflare Static Assets treats as canonical."""

    lowered = path.casefold()
    if lowered == "/index.html":
        return "/"
    if lowered.endswith("/index.html"):
        return path[: -len("index.html")]
    if lowered.endswith(".html"):
        return path[: -len(".html")]
    return path


BASE2026_ABSOLUTE_URL_RE = re.compile(
    r"(?P<url>https://base2026\.dev(?P<path>/[^\s\"'<>]*))",
    re.IGNORECASE,
)
ROOT_HTML_ROUTE_RE = re.compile(
    r"(?<![A-Za-z0-9_:/.-])(?P<path>/(?:[A-Za-z0-9._~!$&()*+,;=:@%/-]+\.html))(?P<suffix>[?#][^\s\"'<>]*)?",
    re.IGNORECASE,
)


def _normalize_base2026_static_urls(text: str, counts: ReplacementCounts | None = None) -> str:
    """Align public URLs with Static Assets' extensionless HTML routing."""

    def replace_absolute(match: re.Match[str]) -> str:
        parsed = urlsplit(match.group("url"))
        mapped_path = _extensionless_html_path(parsed.path)
        if mapped_path == parsed.path:
            return match.group("url")
        if counts is not None:
            counts.html_urls_to_extensionless += 1
        return urlunsplit((parsed.scheme, parsed.netloc, mapped_path, parsed.query, parsed.fragment))

    normalized = BASE2026_ABSOLUTE_URL_RE.sub(replace_absolute, text)

    def replace_root(match: re.Match[str]) -> str:
        path = match.group("path")
        mapped_path = _extensionless_html_path(path)
        if mapped_path == path:
            return match.group(0)
        if counts is not None:
            counts.html_urls_to_extensionless += 1
        return mapped_path + (match.group("suffix") or "")

    return ROOT_HTML_ROUTE_RE.sub(replace_root, normalized)


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
        "integrations.html",
        "llms.txt",
        "mcp.html",
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
    if standalone_startup:
        transformed = _normalize_base2026_static_urls(transformed, counts)
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
REDIRECTING_CANONICAL_RE = re.compile(
    r'<link\s+rel=["\']canonical["\'][^>]*href=["\']https://base2026\.dev/[^"\']+\.html(?:[?#][^"\']*)?["\']',
    re.IGNORECASE,
)
REDIRECTING_SITEMAP_LOC_RE = re.compile(
    r'<loc>https://base2026\.dev/[^<]+\.html(?:[?#][^<]*)?</loc>',
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


ROBOTS_PAYLOAD = (
    "User-agent: *\n"
    "Allow: /\n\n"
    "Sitemap: https://base2026.dev/sitemap.xml\n"
    "Sitemap: https://base2026.dev/sitemap-dynamic.xml\n"
    "Sitemap: https://base2026.dev/sitemap-blog.xml\n"
    "Sitemap: https://base2026.dev/sitemap-guides.xml\n"
)
HEADERS_PAYLOAD = """/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  X-Frame-Options: SAMEORIGIN
  Permissions-Policy: accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()

/*.html
  Cache-Control: no-cache

/*/
  Cache-Control: no-cache

/static/*.jsonl
  Content-Type: application/x-ndjson; charset=utf-8
  Cache-Control: public, max-age=300, s-maxage=3600
"""

SOCIAL_IMAGE_URL = "https://base2026.dev/static/assets/base2026-ai-visibility-card.png"
HUB_SITEMAP_FILENAME = "sitemaps/base2026-hubs.xml"
HUB_SITEMAP_URL = f"{BASE2026_ORIGIN}/{HUB_SITEMAP_FILENAME}"
HUB_SITEMAP_ROUTES = (
    "/",
    "/creators/",
    "/compare/",
    "/analytics",
    "/methodology",
    "/roadmap",
    "/api",
    "/dataset",
    "/mcp",
    "/integrations",
    "/about",
    "/founder",
    "/privacy",
    "/partner",
    "/apply-research",
    "/opt-out",
    "/solutions/",
    "/ai-visibility-resources",
    "/site-structure",
    "/blog",
    "/journal/source-backed-video-search-cloudflare/",
    "/journal/source-diversity-check/",
    "/tools/evidence-search/",
)

# These are generated at the publication boundary rather than inherited from
# the former shared personal-site artifact.  They deliberately describe only
# Base2026's public product, routes and limits.
BASE2026_ROOT_LLMS_PAYLOAD = """# Base2026

Base2026 is an independent open-source public source-intelligence project. It
makes attributed short-form expert-video evidence
searchable for research into SEO, GEO, AEO, AI search, local visibility,
schema, content structure and entity trust.

## Public entry points

- Home: https://base2026.dev/
- Search workspace: https://base2026.dev/workspace/
- Topics: https://base2026.dev/topics/
- Creators: https://base2026.dev/creators/
- Methodology: https://base2026.dev/methodology
- Roadmap: https://base2026.dev/roadmap
- API and AI access: https://base2026.dev/api
- Public dataset: https://base2026.dev/dataset
- Build journal: https://base2026.dev/journal/source-backed-video-search-cloudflare/
- Blog: https://base2026.dev/blog
- Blog RSS: https://base2026.dev/blog/feed.xml
- Founder and selected work: https://base2026.dev/founder
- MCP for AI agents: https://base2026.dev/mcp
- Plugins and integrations: https://base2026.dev/integrations
- Source policy: https://base2026.dev/source-policy
- Creator correction or removal: https://base2026.dev/opt-out
- Current D1 projection sitemap: https://base2026.dev/sitemap-dynamic.xml

The public search API is https://base2026.dev/api/search/multi-search and the
stateless JSON MCP endpoint is https://base2026.dev/api/mcp. Both are no-key,
read-only surfaces over public D1. The MCP tools are search_sources, get_source,
get_creator, get_topic, get_topic_signal and get_public_manifest.

## Public boundary

Base2026 publishes reviewed public source records and attribution. It does not
publish private notes, client data, credentials, raw source vaults, raw ASR,
media files, local databases or unreviewed pipeline artifacts. Cite canonical
source, topic or creator pages when using Base2026 evidence.
"""

BASE2026_LLMS_PAYLOAD = """# Base2026 Knowledge Library

Base2026 is a public searchable library of attributed source records, reviewed
passages, insight cards, topic pages and creator profiles drawn from
short-form expert video. It is a research product, not a marketing-services
site or a private client workspace.

## Primary public entry points

- Search workspace: https://base2026.dev/workspace/
- Topic index: https://base2026.dev/topics/
- Creator index: https://base2026.dev/creators/
- Source index: https://base2026.dev/sources/
- Methodology: https://base2026.dev/methodology
- Founder and selected work: https://base2026.dev/founder
- Apply research: https://base2026.dev/apply-research
- API and AI access: https://base2026.dev/api
- Public dataset and quickstart: https://base2026.dev/dataset
- Build journal: https://base2026.dev/journal/source-backed-video-search-cloudflare/
- Blog: https://base2026.dev/blog
- Blog RSS: https://base2026.dev/blog/feed.xml

## Public data and use

- Release manifest: https://base2026.dev/static/manifest.json
- Public source documents: https://base2026.dev/static/documents.jsonl
- Public passages: https://base2026.dev/static/passages.jsonl
- Insight cards: https://base2026.dev/static/insight_cards.jsonl
- Topic signal briefs: https://base2026.dev/static/topic_signal_briefs.jsonl
- Data dictionary: https://base2026.dev/data-dictionary.json
- Read-only search API: https://base2026.dev/api/search/multi-search
- MCP endpoint: https://base2026.dev/api/mcp
- MCP guide: https://base2026.dev/mcp
- Plugins and integrations: https://base2026.dev/integrations
- Current D1 projection sitemap: https://base2026.dev/sitemap-dynamic.xml

Use the workspace to explore public evidence and cite a canonical Base2026
source, topic or creator page. The search API and MCP endpoint are read-only
and backed by public D1; no browser key is required. MCP has six bounded tools:
search_sources, get_source, get_creator, get_topic, get_topic_signal and
get_public_manifest. Do not use Base2026 for raw transcript harvesting,
creator impersonation, private lead data or administrative writes.
"""


def _rewrite_public_api_docs(relative_path: Path, text: str) -> str:
    """Make the small public API docs match the Cloudflare search contract."""

    path = relative_path.as_posix()
    if path == "root-llms.txt":
        return BASE2026_ROOT_LLMS_PAYLOAD

    if path == "llms.txt":
        return BASE2026_LLMS_PAYLOAD

    if path == "static/insight_cards.jsonl":
        public_rows: list[str] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ReleaseBuildError(
                    f"static/insight_cards.jsonl contains invalid JSON at line {line_number}"
                ) from exc
            if not isinstance(row, dict):
                raise ReleaseBuildError(
                    f"static/insight_cards.jsonl line {line_number} must be an object"
                )
            if row.get("public") is not True:
                continue
            if row.get("needs_review") is True or row.get("public_policy") != "reviewed_insight":
                raise ReleaseBuildError(
                    "static/insight_cards.jsonl contains a contradictory public row "
                    f"at line {line_number}"
                )
            public_rows.append(json.dumps(row, ensure_ascii=False, sort_keys=True))
        if not public_rows:
            raise ReleaseBuildError("static/insight_cards.jsonl has no publishable rows")
        return "\n".join(public_rows) + "\n"

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
        public_insight_cards = payload.get("public_insight_cards")
        if isinstance(public_insight_cards, int) and not isinstance(public_insight_cards, bool):
            payload["insight_cards"] = public_insight_cards
        return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    if path == "search/index.html":
        # This is a legacy no-index alias.  Its relative links must work at
        # /search/ and /search/index.html on a root-mounted static host.
        return text.replace('href="./', 'href="/').replace('src="../static/', 'src="/static/')

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
        text = text.replace(old, new)
        old_ai_handoff = re.compile(
            r"<p>For business-specific implementation, use <code>/apply-research(?:\.html)?</code> as the public bridge from Base2026 source intelligence to Alex Yarosh&#x27;s AI Visibility Snapshot, Diagnostic Audit, and service workflow\.</p>"
        )
        new_ai_handoff = (
            "<p>Use <code>/apply-research.html</code> to understand the public research boundary and how to turn source evidence into an independent review question. Base2026 does not accept private client material or provide a private audit workflow.</p>"
        )
        text = old_ai_handoff.sub(new_ai_handoff, text)
        if old_ai_handoff.search(text) or "service workflow.</p>" in text:
            raise ReleaseBuildError("api.html retains an unhandled personal-commercial handoff")
        return text

    if path == "api-index.json":
        # The source API index historically pointed the human workspace at
        # the old root route.  Keep this route-specific correction at the
        # release boundary so legacy source artifacts cannot reintroduce `/`
        # after the generic old-origin mapping runs.
        workspace_entry_re = re.compile(
            r'("id"\s*:\s*"human_search_workspace"\s*,\s*'
            r'"url"\s*:\s*")[^"]*(")',
            re.IGNORECASE | re.DOTALL,
        )
        text = workspace_entry_re.sub(
            rf'\g<1>{BASE2026_ORIGIN}/workspace/\g<2>', text, count=1
        )
        old_description = (
            '"description": "Server-side Meilisearch multi-search proxy used by the public UI. Prefer static JSONL for bulk/offline analysis; use this endpoint when live search ranking is needed."'
        )
        new_description = (
            '"description": "Read-only Meilisearch-compatible Cloudflare Worker API backed by D1 FTS5. No browser key is required; prefer static JSONL for bulk/offline analysis and use this endpoint when live search ranking is needed.",\n'
            '      "backend": "cloudflare_worker_d1_fts5",\n'
            '      "browser_key_required": false'
        )
        text = text.replace(
            "Human-readable bridge from Base2026 public source intelligence to Alex Yarosh's business-specific AI visibility audit and service workflow.",
            "Human-readable guide to Base2026 public source intelligence, its attribution rules and its public/private boundary.",
        )
        if "business-specific AI visibility audit" in text or "service workflow" in text:
            raise ReleaseBuildError("api-index.json contains an unhandled personal-commercial handoff")
        if old_description not in text:
            if "Server-side Meilisearch multi-search proxy" in text:
                raise ReleaseBuildError("api-index.json contains an unhandled legacy search-proxy contract")
            return text
        text = text.replace(old_description, new_description)
        return text

    return text


def _rewrite_legacy_base_styles(relative_path: Path, text: str) -> str:
    """Retain generated layout coverage while removing legacy visual authority.

    The public corpus is generated and links the broad legacy stylesheet on
    thousands of documents. Replacing it page-by-page would be error-prone;
    instead, normalize its direct palette and retired WordPress-avatar
    dependency as part of the deterministic release build. The independent
    core stylesheet is still loaded afterwards for the shared component
    contract.
    """

    path = relative_path.as_posix()
    legacy_base_styles = {
        "static/styles.css",
        "ai-recommends-solutions.css",
        "static/ai-recommends-solutions.css",
        "roadmap-dataviz-test.css",
        "static/roadmap-dataviz-test.css",
    }
    if path in legacy_base_styles:
        replacements = {
            "#f7f4ee": "#F7F9FC",
            "#fffaf0": "#FFFFFF",
            "#c84f07": "#315EEA",
            "#ef6b13": "#315EEA",
            "#d9730d": "#315EEA",
            "#ff6b18": "#315EEA",
            "#f4f1e9": "#F7F9FC",
            "#e5e2da": "#EEF2F7",
            "#eef2f0": "#EEF2F7",
            "#101820": "#0B1736",
            "#0f172a": "#0B1736",
            "#5f5e58": "#526177",
            "#fff0e3": "#EEF2F7",
        }
        for old, new in replacements.items():
            text = re.sub(re.escape(old), new, text, flags=re.IGNORECASE)
        if path == "static/styles.css":
            text = re.sub(
                r'background:\s*url\(["\']?/wp-content/themes/alex-yarosh/assets/alex-yarosh-avatar\.png["\']?\)\s*center\s*/\s*cover\s*no-repeat\s*;',
                "background: #EEF2F7;",
                text,
                flags=re.IGNORECASE,
            )
        if path.endswith("ai-recommends-solutions.css"):
            text = re.sub(r'\.solution-step__number\s*\{[^}]*\}', "", text)
        if "alex-yarosh-avatar" in text or "/wp-content/themes/alex-yarosh" in text:
            raise ReleaseBuildError("legacy stylesheet retains a personal WordPress asset")
        return text

    return text


STARTUP_HEADER_RE = re.compile(
    r'<header\b[^>]*class=["\'][^"\']*(?:site-header|ay-v2-header|b26-site-header)[^"\']*["\'][^>]*>.*?</header>',
    re.IGNORECASE | re.DOTALL,
)
STARTUP_FOOTER_RE = re.compile(
    r'<footer\b[^>]*class=["\'][^"\']*(?:site-footer|b26-site-footer)[^"\']*["\'][^>]*>.*?</footer>',
    re.IGNORECASE | re.DOTALL,
)
BODY_OPEN_RE = re.compile(r"<body\b[^>]*>", re.IGNORECASE)
BODY_CLOSE_RE = re.compile(r"</body\s*>", re.IGNORECASE)
HEAD_CLOSE_RE = re.compile(r"</head\s*>", re.IGNORECASE)
DOCTYPE_RE = re.compile(r"<!doctype\s+html\s*>", re.IGNORECASE)
STARTUP_SHELL_LINK = '<link rel="stylesheet" href="/static/base2026-startup-shell.css?v=20260820-b26v1">'
STARTUP_CORE_LINK = '<link rel="stylesheet" href="/static/base2026-core.css?v=20260820-b26v1">'
STARTUP_FAVICON_LINK = '<link rel="icon" href="/static/base2026-mark.svg" type="image/svg+xml">'
PERSONAL_ASSET_TAG_RE = re.compile(
    r'\s*<(?:link|script)\b[^>]*(?:wordpress-v4|alex-v4-static-shell|base2026-personal-v4-presentation|data-shell-authority|data-presentation-authority)[^>]*>(?:\s*</script>)?',
    re.IGNORECASE,
)
PERSONAL_IMAGE_TAG_RE = re.compile(
    r'\s*<(?:meta|link|img)\b[^>]*alex-yarosh[^>]*>', re.IGNORECASE
)
PERSONAL_ROUTE_ATTRIBUTE_RE = re.compile(
    r'(?P<prefix>\b(?:href|action|formaction)\s*=\s*["\'])'
    r'/(?:services|pricing|about|research|results|insights|ai-visibility-audit|ai-visibility-diagnostic-audit|ai-visibility-source-footprint|answer-ready-service-pages|entity-trust-source-intelligence|technical-seo-geo-foundation|wp-admin)(?:/[^"\']*)?'
    r'(?P<suffix>["\'])',
    re.IGNORECASE,
)
REMAINING_PERSONAL_ROUTE_ATTRIBUTE_RE = re.compile(
    r'(?P<prefix>\b(?:href|action|formaction)\s*=\s*["\'])'
    r'/(?:services|pricing|research|results|insights|ai-visibility-audit|ai-visibility-diagnostic-audit|ai-visibility-source-footprint|answer-ready-service-pages|entity-trust-source-intelligence|technical-seo-geo-foundation|wp-admin)(?:/[^"\']*)?'
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
LEGACY_COMMERCIAL_BRIDGE_RE = re.compile(
    r'\s*<section\b[^>]*(?:\bid|aria-labelledby)=["\'][^"\']*source-footprint-bridge[^"\']*["\'][^>]*>.*?</section>',
    re.IGNORECASE | re.DOTALL,
)
LEGACY_ROADMAP_CONTACT_RE = re.compile(
    r'\s*<section\b[^>]*class=["\'][^"\']*base-contact-section[^"\']*["\'][^>]*>.*?Base2026%20roadmap%20feedback.*?</section>',
    re.IGNORECASE | re.DOTALL,
)
ROADMAP_CONTACT_MARKUP = """
<section class="b26-roadmap-contact" aria-labelledby="b26-roadmap-contact-title">
  <div>
    <p class="b26-eyebrow">Roadmap feedback</p>
    <h2 id="b26-roadmap-contact-title">Send corrections and proposals through the project inbox.</h2>
    <p>Use the Support form for roadmap corrections, source suggestions, infrastructure offers or a proposal for the next public build step.</p>
  </div>
  <a class="b26-button--primary" href="/support">Open the Support form</a>
</section>
""".strip()
SOLUTION_STEP_NUMBER_RE = re.compile(
    r'\s*<span\b[^>]*class=["\'][^"\']*solution-step__number[^"\']*["\'][^>]*>.*?</span>',
    re.IGNORECASE | re.DOTALL,
)
PERSONAL_COMMERCIAL_MARKERS = (
    "get free snapshot",
    "free ai visibility snapshot",
    "ai visibility diagnostic audit",
    "check my ai visibility",
    "alex yarosh workflow",
    "alex yarosh's audit",
    "alex yarosh audit",
    "alex yarosh source library hero",
    "/static/assets/alex-yarosh-",
)


def _apply_startup_shell(text: str, header_html: str, footer_html: str) -> str:
    """Replace the inherited personal-site chrome on a public HTML page."""

    if STARTUP_SHELL_LINK not in text:
        if "</head>" in text:
            text = text.replace("</head>", f"  {STARTUP_SHELL_LINK}\n</head>", 1)
        else:
            text = STARTUP_SHELL_LINK + "\n" + text
    if STARTUP_CORE_LINK not in text:
        if "</head>" in text:
            text = text.replace("</head>", f"  {STARTUP_CORE_LINK}\n</head>", 1)
        else:
            text = STARTUP_CORE_LINK + "\n" + text
    text = PERSONAL_ASSET_TAG_RE.sub("", text)
    text = PERSONAL_IMAGE_TAG_RE.sub("", text)
    text = LEGACY_RESEARCH_NAV_RE.sub("", text)
    text = LEGACY_COOKIE_UI_RE.sub("", text)
    text = LEGACY_COOKIE_SCRIPT_RE.sub("", text)
    text = LEGACY_COMMERCIAL_BRIDGE_RE.sub("", text)
    text = LEGACY_ROADMAP_CONTACT_RE.sub("\n" + ROADMAP_CONTACT_MARKUP, text)
    text = SOLUTION_STEP_NUMBER_RE.sub("", text)
    if STARTUP_FAVICON_LINK not in text and "</head>" in text:
        text = text.replace("</head>", f"  {STARTUP_FAVICON_LINK}\n</head>", 1)
    text = re.sub(
        r'(<a\b[^>]*href=["\'])/ai-visibility-audit/(?:[^"\']*)?(["\'][^>]*>)\s*Get free snapshot\s*</a>',
        r'\1/methodology.html\2Read the methodology</a>',
        text,
        flags=re.IGNORECASE,
    )
    text = PERSONAL_ROUTE_ATTRIBUTE_RE.sub(r'\g<prefix>/workspace/\g<suffix>', text)
    for old_class in ("ay-alex-v4-static", "ay-stitch-home-v3", "ay-stitch-home-v4"):
        text = text.replace(old_class, "")
    text, header_count = STARTUP_HEADER_RE.subn(header_html, text, count=1)
    text, footer_count = STARTUP_FOOTER_RE.subn(footer_html, text, count=1)
    # A few retained static visual/legacy documents have a conventional footer
    # but no classed site header. They remain public routes, so normalize their
    # shell at this single release boundary instead of leaving a mixed page or
    # editing generated output one file at a time.
    if header_count == 0:
        if "b26-site-header" in text:
            header_count = 1
        else:
            text, header_count = BODY_OPEN_RE.subn(
                lambda match: match.group(0) + header_html, text, count=1
            )
            if header_count == 0:
                text, header_count = HEAD_CLOSE_RE.subn(
                    lambda match: match.group(0) + header_html, text, count=1
                )
            if header_count == 0:
                text, header_count = DOCTYPE_RE.subn(
                    lambda match: match.group(0) + header_html, text, count=1
                )
            if header_count == 0:
                text = header_html + text
                header_count = 1
    if footer_count == 0:
        if "b26-site-footer" in text:
            footer_count = 1
        else:
            text, footer_count = BODY_CLOSE_RE.subn(
                lambda match: footer_html + match.group(0), text, count=1
            )
            if footer_count == 0:
                text += footer_html
                footer_count = 1
    if "Alex Yarosh primary header" in text or "Get Free Snapshot" in text:
        raise ReleaseBuildError("HTML contains an unhandled personal-site header")
    if header_count != 1 or footer_count != 1:
        raise ReleaseBuildError("HTML shell replacement was incomplete")
    return _ensure_social_image_meta(
        text.replace("Alex Yarosh profile photo", "Base2026 project preview")
    )


def _ensure_social_image_meta(text: str) -> str:
    """Add the one approved Base2026 social preview when a page has none."""

    tags: list[str] = []
    if not re.search(r'<meta\s+property=["\']og:image["\']', text, re.IGNORECASE):
        tags.extend(
            [
                f'<meta property="og:image" content="{SOCIAL_IMAGE_URL}">',
                '<meta property="og:image:width" content="1200">',
                '<meta property="og:image:height" content="630">',
                '<meta property="og:image:alt" content="Base2026 public-source intelligence">',
            ]
        )
    if not re.search(r'<meta\s+name=["\']twitter:image["\']', text, re.IGNORECASE):
        tags.extend(
            [
                f'<meta name="twitter:image" content="{SOCIAL_IMAGE_URL}">',
                '<meta name="twitter:image:alt" content="Base2026 public-source intelligence">',
            ]
        )
    if not tags:
        return text
    payload = "\n".join(tags)
    if "</head>" in text:
        return text.replace("</head>", payload + "\n</head>", 1)
    return payload + "\n" + text


def _render_startup_page(template: str, header_html: str, footer_html: str) -> bytes:
    if template.count("{{STARTUP_HEADER}}") != 1 or template.count("{{STARTUP_FOOTER}}") != 1:
        raise ReleaseBuildError("startup page template must contain one header and footer placeholder")
    if STARTUP_FAVICON_LINK not in template and "</head>" in template:
        template = template.replace("</head>", f"{STARTUP_FAVICON_LINK}</head>", 1)
    if STARTUP_CORE_LINK not in template:
        if "</head>" in template:
            template = template.replace("</head>", f"{STARTUP_CORE_LINK}</head>", 1)
        elif DOCTYPE_RE.search(template):
            template = DOCTYPE_RE.sub(
                lambda match: match.group(0) + "\n" + STARTUP_CORE_LINK,
                template,
                count=1,
            )
        else:
            template = STARTUP_CORE_LINK + "\n" + template
    rendered = template.replace("{{STARTUP_HEADER}}", header_html).replace(
        "{{STARTUP_FOOTER}}", footer_html
    )
    return _ensure_social_image_meta(rendered).encode("utf-8")


def _hub_sitemap_payload() -> bytes:
    urls = "".join(
        f"<url><loc>{BASE2026_ORIGIN}{route}</loc></url>" for route in HUB_SITEMAP_ROUTES
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{urls}</urlset>\n"
    ).encode("utf-8")


def _editorial_catalog(path: Path = DEFAULT_EDITORIAL_CATALOG) -> list[dict]:
    """The two existing journal articles remain one reviewed metadata source.

    New articles live in receipted D1 rows, never in this fallback catalog.
    This rejects unsafe catalog URLs before either HTML or JSON-LD insertion.
    """
    records = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(records, list) or not 1 <= len(records) <= 25:
        raise ReleaseBuildError("editorial catalog must contain 1-25 records")
    seen: set[str] = set()
    required = {"id", "path", "title", "description", "category", "published_at", "updated_at", "author"}
    allowed_paths = {
        "/journal/source-diversity-check/",
        "/journal/source-backed-video-search-cloudflare/",
    }
    for record in records:
        if not isinstance(record, dict) or not required <= record.keys() or record.keys() - required - {"hero"}:
            raise ReleaseBuildError("invalid editorial catalog fields")
        if any(not isinstance(record[key], str) or not record[key].strip() for key in required):
            raise ReleaseBuildError("invalid editorial catalog text")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", record["id"]):
            raise ReleaseBuildError("invalid editorial catalog id")
        if record["path"] not in allowed_paths or record["path"] in seen:
            raise ReleaseBuildError("invalid or duplicate editorial catalog route")
        seen.add(record["path"])
        for key in ("published_at", "updated_at"):
            try:
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", record[key]):
                    raise ValueError
                datetime.strptime(record[key], "%Y-%m-%d")
            except ValueError as exc:
                raise ReleaseBuildError("invalid editorial catalog date") from exc
        if record["updated_at"] < record["published_at"]:
            raise ReleaseBuildError("invalid editorial catalog date order")
        if record["author"] != "Alex Yarosh":
            raise ReleaseBuildError("editorial catalog byline is not approved")
        hero = record.get("hero")
        if hero is not None:
            if not isinstance(hero, dict) or set(hero) != {"path", "alt", "credit", "ai_generated"}:
                raise ReleaseBuildError("invalid editorial image fields")
            if hero["path"] != "/static/assets/base2026-source-diversity.png":
                raise ReleaseBuildError("editorial image is not in the reviewed catalog")
            if any(not isinstance(hero[key], str) or not hero[key].strip() for key in ("alt", "credit")):
                raise ReleaseBuildError("invalid editorial image text")
            if hero["ai_generated"] is not True or "AI-generated" not in hero["credit"]:
                raise ReleaseBuildError("editorial image disclosure is missing")
    return sorted(records, key=lambda item: (-datetime.strptime(item["published_at"], "%Y-%m-%d").toordinal(), item["id"]))


def _editorial_card(record: dict, *, featured: bool) -> str:
    esc = html.escape
    heading_id = "blog-" + ("feature-" if featured else "card-") + "journal-" + record["id"]
    tag = "h2" if featured else "h3"
    date = datetime.strptime(record["published_at"], "%Y-%m-%d")
    label = date.strftime("%B") + f" {date.day}, {date.year}"
    copy = (
        '<p class="b26-blog-card__meta"><span class="b26-blog-card__category">'
        + esc(record["category"]) + '</span><time datetime="' + esc(record["published_at"])
        + '">' + label + "</time></p>"
        + f'<{tag} class="b26-blog-card__title" id="{esc(heading_id)}">'
        + esc(record["title"]) + f"</{tag}>"
        + '<p class="b26-blog-card__excerpt">' + esc(record["description"]) + "</p>"
        + '<div class="b26-blog-card__footer"><span class="b26-blog-card__byline">'
        + esc(record["author"]) + '</span><span class="b26-blog-card__read">'
        + 'Read article <span aria-hidden="true">→</span></span></div>'
    )
    hero = record.get("hero") if featured else None
    class_name = "b26-blog-feature" if featured else "b26-blog-card"
    if featured and not hero:
        class_name += " b26-blog-feature--text-only"
    media = (
        '<figure class="b26-blog-feature__media"><img src="' + esc(hero["path"])
        + '" alt="' + esc(hero["alt"]) + '" width="1254" height="1254" loading="eager" fetchpriority="high">'
        + "<figcaption>" + esc(hero["credit"]) + "</figcaption></figure>"
    ) if hero else ""
    return (
        '<article class="' + class_name + '"><a class="b26-blog-card__link" href="'
        + esc(record["path"]) + '" aria-labelledby="' + esc(heading_id) + '">'
        + ('<div class="b26-blog-feature__body">' + copy + "</div>" if featured else copy)
        + media + "</a></article>"
    )


def _render_editorial_index(header_html: str, footer_html: str) -> bytes:
    records = _editorial_catalog()
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage", "@id": BASE2026_ORIGIN + "/blog#page",
                "url": BASE2026_ORIGIN + "/blog", "name": "Base2026 Blog",
                "mainEntity": {"@id": BASE2026_ORIGIN + "/blog#blog"},
            },
            {
                "@type": "Blog", "@id": BASE2026_ORIGIN + "/blog#blog",
                "name": "Base2026 Blog", "url": BASE2026_ORIGIN + "/blog",
                "blogPost": [
                    {
                        "@type": "BlogPosting", "headline": item["title"],
                        "url": BASE2026_ORIGIN + item["path"],
                        "datePublished": item["published_at"], "dateModified": item["updated_at"],
                        "author": {"@type": "Person", "name": item["author"], "url": BASE2026_ORIGIN + "/founder"},
                    }
                    for item in records
                ],
            },
        ],
    }
    template = DEFAULT_BLOG_TEMPLATE.read_text(encoding="utf-8")
    values = {
        "BLOG_FEATURED": _editorial_card(records[0], featured=True),
        "BLOG_CARDS": "".join(_editorial_card(item, featured=False) for item in records[1:]),
        "BLOG_TOPIC_LINKS": '<a href="/topics/">Browse source topics</a><a href="/methodology">Research methodology</a>',
        "BLOG_SCHEMA": json.dumps(graph, ensure_ascii=True).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"),
    }
    for key, value in values.items():
        slot = "{{" + key + "}}"
        if template.count(slot) != 1:
            raise ReleaseBuildError("editorial template slot mismatch")
        template = template.replace(slot, value)
    return _render_startup_page(template, header_html, footer_html)


def _add_hub_sitemap_to_index(text: str) -> str:
    if HUB_SITEMAP_URL in text:
        return text
    entry = f"<sitemap><loc>{HUB_SITEMAP_URL}</loc></sitemap>"
    if "</sitemapindex>" not in text:
        raise ReleaseBuildError("sitemap.xml is not a sitemap index")
    return text.replace("</sitemapindex>", entry + "</sitemapindex>", 1)


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


def _workspace_manifest_counts(path: Path) -> dict[str, int]:
    """Read safe fallback counters from the reviewed static release manifest."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    candidates = {
        "documents": payload.get("documents", payload.get("source_records")),
        "chunks": payload.get("chunks", payload.get("passages")),
        "creators": payload.get("creators"),
    }
    return {
        key: value
        for key, value in candidates.items()
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0
    }


def _workspace_manifest_snapshot_date(path: Path) -> str:
    """Return the YYYY-MM-DD date for a reviewed static release manifest."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return ""
    if not isinstance(payload, dict):
        return ""
    created_at = payload.get("created_at")
    if not isinstance(created_at, str):
        return ""
    match = re.fullmatch(r"(\d{4}-\d{2}-\d{2})(?:T.*)?", created_at.strip())
    return match.group(1) if match else ""


def _rewrite_workspace_html(
    text: str,
    manifest_counts: Mapping[str, int] | None = None,
    manifest_snapshot_date: str = "",
) -> str:
    """Move the former root search UI to /workspace/ without breaking assets or SEO."""

    # A dated public artifact contains one malformed self-closing metadata
    # line (``<meta ... /`` without the final ``>``). Browsers then consume
    # following stylesheet links as attribute text, leaving the real search
    # application unstyled. Repair only that bounded malformed form while
    # keeping the document and its search runtime otherwise intact.
    text = re.sub(r"(<meta\b[^>\r\n]*?)\s+/\s*(?:\r?\n)", r"\1 />\n", text)
    # The historical workspace source contained an explicit handoff into the
    # founder's commercial audit. Base2026 remains a public research product;
    # the commercial bridge has no role in its independent navigation or
    # workspace. Keep the explanation of the public boundary, but remove the
    # sales block and normalize the surrounding copy to Base2026-only language.
    text = re.sub(
        r'\s*<section class="research-bridge" aria-labelledby="research-bridge-title">.*?</section>',
        "",
        text,
        count=1,
        flags=re.DOTALL,
    )
    text = re.sub(
        r'Base2026 is an independent research product by <a href="/(?:solutions|workspace)/">Alex Yarosh</a>\.',
        "Base2026 is an independent public research pilot.",
        text,
    )
    text = text.replace(
        "Do not use the public search workspace for private client data, credentials, analytics exports or confidential strategy. Route business-specific diagnosis into the Alex Yarosh workflow.",
        "Do not use the public search workspace for private client data, credentials, analytics exports or confidential strategy.",
    )
    text = re.sub(
        r'\s*<a class="ay-button-secondary" href="/solutions/">AI Visibility Diagnostic Audit</a>',
        "",
        text,
        count=1,
    )
    text = text.replace(
        ">AI Visibility Diagnostic Audit</a>", ">Explore the research workspace</a>"
    )
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
    # "Project Story" belongs to the public Base2026 project page.  Older
    # workspace artifacts may already carry the workspace route because the
    # startup-shell pass treated ``/about`` as a personal-site route; restore
    # this exact product link at the workspace boundary without changing the
    # genuine workspace links around it.
    text = re.sub(
        r'(<a\b[^>]*href=["\'])(?:/workspace/|/about(?:\.html)?)(["\'][^>]*>\s*Project Story\s*</a>)',
        r"\g<1>/about\g<2>",
        text,
        flags=re.IGNORECASE,
    )
    for key, value in (manifest_counts or {}).items():
        text = re.sub(
            rf'(data-manifest-count="{re.escape(key)}">)[^<]*',
            rf'\g<1>{value:,}',
            text,
        )
    if manifest_snapshot_date and "workspace-stat-snapshot" not in text:
        snapshot_markup = (
            '<p class="workspace-stat-snapshot">Static snapshot · '
            + manifest_snapshot_date
            + "</p>"
        )
        analytics_link = '<a class="workspace-stat-link" href="./analytics.html">Analytics</a>'
        if analytics_link in text:
            text = text.replace(analytics_link, snapshot_markup + analytics_link, 1)
        else:
            text = re.sub(
                r'(<strong data-manifest-count="creators">[^<]*</strong>)',
                r"\1" + snapshot_markup,
                text,
                count=1,
            )
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


def _with_member_workspace_assets(text: str) -> str:
    """Add opt-in account controls without replacing the served search renderer."""
    stylesheet = '<link rel="stylesheet" href="/static/base2026-members.css?v=20260831-members-v1">'
    script = '<script src="/static/base2026-members.js?v=20260831-members-v1" defer></script>'
    if text.count("</head>") != 1 or text.count("</body>") != 1:
        raise ReleaseBuildError("member workspace requires one complete HTML document")
    if "base2026-members.css" not in text:
        text = text.replace("</head>", stylesheet + "\n</head>", 1)
    if "base2026-members.js" not in text:
        text = text.replace("</body>", script + "\n</body>", 1)
    return text


def _with_member_privacy_notice(text: str, notice: str) -> str:
    if text.count("</article>") != 1 or 'id="b26-members-privacy"' not in notice:
        raise ReleaseBuildError("member privacy notice requires the current legal template")
    if 'id="b26-members-privacy"' in text:
        raise ReleaseBuildError("member privacy notice must be rendered from its source template")
    text = text.replace("</article>", notice.strip() + "</article>", 1)
    text = text.replace(
        "How Base2026 handles support and partnership proposal data.",
        "How Base2026 handles Google sign-in, private research and project proposals.",
        1,
    ).replace(
        "Project forms, kept separate from public research.",
        "Your private research and project information.",
        1,
    ).replace("Last updated: 20 August 2026.", "Last updated: 31 August 2026.", 1)
    return text


def build_release(
    source_web: Path | str,
    out: Path | str,
    homepage_template: Path | str | None = None,
    homepage_stylesheet: Path | str | None = None,
    members_workspace: bool = False,
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
    if members_workspace and not standalone_startup:
        raise ReleaseBuildError("member workspace requires the current startup shell")
    if not members_workspace and (source / "my-research" / "index.html").exists():
        raise ReleaseBuildError("member-enabled input requires explicit --members-workspace")
    startup_header = DEFAULT_STARTUP_HEADER.read_text(encoding="utf-8").strip() if standalone_startup else ""
    startup_footer = DEFAULT_STARTUP_FOOTER.read_text(encoding="utf-8").strip() if standalone_startup else ""
    startup_shell_css = DEFAULT_STARTUP_SHELL_STYLESHEET.read_bytes() if standalone_startup else b""
    core_css = DEFAULT_CORE_STYLESHEET.read_bytes() if standalone_startup else b""
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
                artifact_text = _rewrite_legacy_base_styles(relative_path, artifact_text)
                if standalone_startup:
                    artifact_text = _remove_excluded_startup_route_references(
                        artifact_text, startup_excluded_routes
                    )
                if standalone_startup and relative_path.suffix.casefold() in {".html", ".htm", ".xhtml"}:
                    artifact_text = _apply_startup_shell(
                        artifact_text, startup_header, startup_footer
                    )
                if standalone_startup:
                    artifact_text = _normalize_base2026_static_urls(artifact_text, replacements)
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
            if Path(relative_name).suffix.casefold() in {".html", ".json", ".js", ".txt", ".xml"}:
                try:
                    payload = _normalize_base2026_static_urls(
                        payload.decode("utf-8"), replacements
                    ).encode("utf-8")
                except UnicodeDecodeError:
                    pass
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
                        # A generated page can receive another reviewed overlay
                        # in the same build without existing in the input tree.
                        changed=not existing.source_sha256 or _sha256(payload) != existing.source_sha256,
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

        def write_tracked_public_overlay(relative_name: str, source_path: Path) -> None:
            """Publish a reviewed repository page through the normal release transforms."""

            source_text = source_path.read_text(encoding="utf-8")
            transformed = transform_text(
                source_text,
                public_root_names=public_root_names,
                intentional_redirect_documentation=False,
                standalone_startup=standalone_startup,
            )
            replacements.add(transformed.replacements)
            relative_path = Path(relative_name)
            artifact_text = _rewrite_public_api_docs(relative_path, transformed.text)
            artifact_text = _rewrite_legacy_base_styles(relative_path, artifact_text)
            if standalone_startup:
                artifact_text = _remove_excluded_startup_route_references(
                    artifact_text, startup_excluded_routes
                )
            if standalone_startup and relative_path.suffix.casefold() in {
                ".html",
                ".htm",
                ".xhtml",
            }:
                artifact_text = _apply_startup_shell(
                    artifact_text, startup_header, startup_footer
                )
            write_generated_public_file(relative_name, artifact_text.encode("utf-8"))

        write_generated_public_file(ROBOTS_FILENAME, ROBOTS_PAYLOAD.encode("utf-8"))
        write_generated_public_file(HEADERS_FILENAME, HEADERS_PAYLOAD.encode("utf-8"))
        if standalone_startup:
            sitemap_index_path = stage / "sitemap.xml"
            if not sitemap_index_path.is_file():
                raise ReleaseBuildError("startup release requires sitemap.xml")
            write_generated_public_file(
                "sitemap.xml",
                _add_hub_sitemap_to_index(
                    sitemap_index_path.read_text(encoding="utf-8")
                ).encode("utf-8"),
            )
            write_generated_public_file(HUB_SITEMAP_FILENAME, _hub_sitemap_payload())

        if homepage_template_path and homepage_stylesheet_path:
            # The retained source artifact has two root-family documents:
            # ``index.html`` is the former marketing/startup surface, while
            # ``search.html`` is the working search application.  Reusing the
            # former here created a visually plausible but non-functional
            # workspace at /workspace/.  Keep the product workspace sourced
            # from its actual application document and move only that document
            # to the canonical workspace route.
            workspace_source = stage / "search.html"
            if not workspace_source.is_file():
                raise ReleaseBuildError(
                    "startup overlay requires search.html as the workspace source"
                )
            workspace_manifest_path = stage / "static" / "manifest.json"
            workspace_manifest_counts = _workspace_manifest_counts(workspace_manifest_path)
            workspace_manifest_snapshot_date = _workspace_manifest_snapshot_date(
                workspace_manifest_path
            )
            workspace_html = _rewrite_workspace_html(
                workspace_source.read_text(encoding="utf-8"),
                workspace_manifest_counts,
                workspace_manifest_snapshot_date,
            ).encode("utf-8")
            homepage_html = _render_startup_page(
                homepage_template_path.read_text(encoding="utf-8"), startup_header, startup_footer
            )
            homepage_css = homepage_stylesheet_path.read_bytes()
            write_generated_public_file("workspace/index.html", workspace_html)
            # Retain legacy search aliases as public, independently usable
            # documents, but make their body and canonical vocabulary match
            # the Workspace.  Leaving their old founder-commercial bridge in
            # place would preserve a hidden second product contract even after
            # the visible route moved to /workspace/.
            for legacy_search_alias in ("search.html", "search/index.html", "meili.html"):
                legacy_alias_path = stage / legacy_search_alias
                if legacy_alias_path.is_file():
                    write_generated_public_file(
                        legacy_search_alias,
                        _rewrite_workspace_html(
                            legacy_alias_path.read_text(encoding="utf-8"),
                            workspace_manifest_counts,
                            workspace_manifest_snapshot_date,
                        ).encode("utf-8"),
                    )
            write_generated_public_file("index.html", homepage_html)
            write_generated_public_file("static/base2026-startup-homepage.css", homepage_css)
            write_generated_public_file("static/base2026-startup-shell.css", startup_shell_css)
            write_generated_public_file("static/base2026-core.css", core_css)
            write_generated_public_file("static/base2026-forms.js", DEFAULT_FORMS_SCRIPT.read_bytes())
            write_generated_public_file("static/base2026-evidence-brief.js", DEFAULT_EVIDENCE_BRIEF_SCRIPT.read_bytes())
            write_generated_public_file("static/roadmap.js", DEFAULT_ROADMAP_SCRIPT.read_bytes())
            write_tracked_public_overlay("roadmap.html", DEFAULT_ROADMAP_PAGE)
            write_tracked_public_overlay("analytics.html", DEFAULT_ANALYTICS_PAGE)
            write_tracked_public_overlay("api.html", DEFAULT_API_PAGE)
            write_tracked_public_overlay("api-index.json", DEFAULT_API_INDEX)
            write_tracked_public_overlay("mcp.html", DEFAULT_MCP_PAGE)
            write_tracked_public_overlay("integrations.html", DEFAULT_INTEGRATIONS_PAGE)
            write_tracked_public_overlay("data-dictionary.json", DEFAULT_DATA_DICTIONARY)
            write_tracked_public_overlay("llms.txt", DEFAULT_LLMS)
            write_tracked_public_overlay("root-llms.txt", DEFAULT_ROOT_LLMS)
            write_generated_public_file("static/brand/github.svg", DEFAULT_GITHUB_ICON.read_bytes())
            write_generated_public_file("static/brand/x.svg", DEFAULT_X_ICON.read_bytes())
            write_generated_public_file("static/base2026-mark.svg", DEFAULT_MARK_ICON.read_bytes())
            write_generated_public_file(
                "static/base2026-founder.css", DEFAULT_FOUNDER_STYLESHEET.read_bytes()
            )
            write_generated_public_file(
                "static/assets/alex-yarosh-founder-step-wall.webp",
                DEFAULT_FOUNDER_HERO_IMAGE.read_bytes(),
            )
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
            write_generated_public_file(
                "founder.html",
                _render_startup_page(
                    DEFAULT_FOUNDER_TEMPLATE.read_text(encoding="utf-8"),
                    startup_header,
                    startup_footer,
                ),
            )
            write_generated_public_file(
                "dataset.html",
                _render_startup_page(
                    DEFAULT_DATASET_TEMPLATE.read_text(encoding="utf-8"),
                    startup_header,
                    startup_footer,
                ),
            )
            write_generated_public_file(
                "journal/source-backed-video-search-cloudflare/index.html",
                _render_startup_page(
                    DEFAULT_JOURNAL_CLOUDFLARE_TEMPLATE.read_text(encoding="utf-8"),
                    startup_header,
                    startup_footer,
                ),
            )
            write_generated_public_file(
                "journal/source-diversity-check/index.html",
                _render_startup_page(
                    DEFAULT_JOURNAL_SOURCE_DIVERSITY_TEMPLATE.read_text(encoding="utf-8"),
                    startup_header,
                    startup_footer,
                ),
            )
            write_generated_public_file(
                "static/assets/base2026-source-diversity.png",
                DEFAULT_JOURNAL_SOURCE_DIVERSITY_IMAGE.read_bytes(),
            )
            write_generated_public_file("blog.html", _render_editorial_index(startup_header, startup_footer))
            write_generated_public_file("static/base2026-blog.css", DEFAULT_BLOG_STYLESHEET.read_bytes())
            write_generated_public_file("static/base2026-blog-article.css", DEFAULT_BLOG_ARTICLE_STYLESHEET.read_bytes())
            write_generated_public_file("static/base2026-evidence-guide.css", DEFAULT_EVIDENCE_GUIDE_STYLESHEET.read_bytes())
            write_generated_public_file("static/base2026-evidence-guide.js", DEFAULT_EVIDENCE_GUIDE_SCRIPT.read_bytes())
            write_generated_public_file(
                "static/base2026-evidence-search.css",
                DEFAULT_EVIDENCE_SEARCH_STYLESHEET.read_bytes(),
            )
            write_generated_public_file(
                "static/base2026-evidence-search.js",
                DEFAULT_EVIDENCE_SEARCH_SCRIPT.read_bytes(),
            )
            write_generated_public_file(
                "tools/evidence-search/index.html",
                _render_startup_page(
                    DEFAULT_EVIDENCE_SEARCH_TEMPLATE.read_text(encoding="utf-8"),
                    startup_header,
                    startup_footer,
                ),
            )
            write_generated_public_file(
                "static/assets/base2026-ai-visibility-measurement.png",
                DEFAULT_EDITORIAL_MEASUREMENT_IMAGE.read_bytes(),
            )
            write_generated_public_file(
                "apply-research.html",
                _render_startup_page(
                    DEFAULT_APPLY_RESEARCH_TEMPLATE.read_text(encoding="utf-8"),
                    startup_header,
                    startup_footer,
                ),
            )
            write_generated_public_file(
                "ai-visibility-resources.html",
                _render_startup_page(
                    DEFAULT_AI_VISIBILITY_RESOURCES_TEMPLATE.read_text(encoding="utf-8"),
                    startup_header,
                    startup_footer,
                ),
            )

            if members_workspace:
                write_generated_public_file(
                    "workspace/index.html",
                    _with_member_workspace_assets(
                        (stage / "workspace" / "index.html").read_text(encoding="utf-8")
                    ).encode("utf-8"),
                )
                write_generated_public_file(
                    "my-research/index.html",
                    _render_startup_page(
                        DEFAULT_MEMBERS_TEMPLATE.read_text(encoding="utf-8"),
                        startup_header,
                        startup_footer,
                    ),
                )
                write_generated_public_file("static/base2026-members.css", DEFAULT_MEMBERS_STYLESHEET.read_bytes())
                write_generated_public_file("static/base2026-members.js", DEFAULT_MEMBERS_SCRIPT.read_bytes())
                write_generated_public_file(
                    "privacy.html",
                    _render_startup_page(
                        _with_member_privacy_notice(
                            DEFAULT_PRIVACY_TEMPLATE.read_text(encoding="utf-8"),
                            DEFAULT_MEMBERS_PRIVACY.read_text(encoding="utf-8"),
                        ),
                        startup_header,
                        startup_footer,
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
        personal_commercial_markers = 0
        decorative_sequence_markers = 0
        redirecting_canonical_markers = 0
        redirecting_sitemap_markers = 0
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
                    personal_route_markers += len(REMAINING_PERSONAL_ROUTE_ATTRIBUTE_RE.findall(text))
                    personal_commercial_markers += sum(
                        text.casefold().count(marker) for marker in PERSONAL_COMMERCIAL_MARKERS
                    )
                    decorative_sequence_markers += text.casefold().count("solution-step__number")
            findings = scan_for_broken_paths(
                text, intentional_redirect_documentation=intentional
            )
            remaining_old_origin += findings["old_base2026_canonical_origin"]
            remaining_knowledge += findings["broken_knowledge_product_path"]
            redirecting_canonical_markers += len(REDIRECTING_CANONICAL_RE.findall(text))
            redirecting_sitemap_markers += len(REDIRECTING_SITEMAP_LOC_RE.findall(text))
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
        if redirecting_canonical_markers or redirecting_sitemap_markers:
            raise ReleaseBuildError(
                "final artifact points canonical/sitemap URLs at redirecting .html routes: "
                f"canonicals={redirecting_canonical_markers}, sitemaps={redirecting_sitemap_markers}"
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
        if personal_commercial_markers or decorative_sequence_markers:
            raise ReleaseBuildError(
                "standalone startup artifact contains retired personal-commercial or decorative sequence markers: "
                f"commercial={personal_commercial_markers}, sequence={decorative_sequence_markers}"
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
            "personal_commercial_markers_remaining": personal_commercial_markers,
            "decorative_sequence_markers_remaining": decorative_sequence_markers,
            "redirecting_html_canonical_markers_remaining": redirecting_canonical_markers,
            "redirecting_html_sitemap_markers_remaining": redirecting_sitemap_markers,
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
    parser.add_argument(
        "--members-workspace",
        action="store_true",
        help="include the optional private My Research UI (requires separately configured auth)",
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
            members_workspace=args.members_workspace,
        )
    except (OSError, ReleaseBuildError, UnicodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
