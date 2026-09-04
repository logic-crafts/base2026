#!/usr/bin/env python3
"""Build a deterministic evidence note from the public Base2026 MCP.

The workflow is intentionally small: it performs one MCP discovery request,
then one bounded read-only ``get_source`` request per supplied public ID.  It
does not authenticate, upload data, call a write tool, or retain anything
other than the output files the operator explicitly requests.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


DEFAULT_ENDPOINT = "https://base2026.dev/api/mcp"
MCP_PROTOCOL_VERSION = "2026-07-28"
MAX_IDS = 8
MAX_ID_LENGTH = 200
MAX_BODY_BYTES = 64 * 1024
DEFAULT_TIMEOUT_SECONDS = 30.0
PUBLIC_BOUNDARY = {
    "access": "public_read_only",
    "raw_captions": False,
    "raw_asr": False,
    "media_files": False,
    "private_data": False,
    "writes": False,
}
FORBIDDEN_KEYS = {
    "audio",
    "caption",
    "media_file",
    "raw_transcript",
    "raw_caption",
    "raw_asr",
    "media",
    "media_url",
    "private_payload",
    "private_notes",
    "credential",
    "credentials",
    "password",
    "secret",
    "transcript",
    "token",
    "cookie",
}
LIMITATIONS = [
    "This is a bounded point-in-time read of the public MCP, not a complete dataset snapshot.",
    "The public get_source response caps passages and applied cards; a missing field is recorded as an unknown, not treated as proof of absence.",
    "Attribution and excerpts are source-linked evidence, not a determination of truth, consensus, ranking, causality, or real-time coverage.",
    "The public boundary excludes raw captions, raw ASR, media, private records, credentials, and write operations.",
]


class EvidencePackError(RuntimeError):
    """An expected, user-actionable failure in the bounded workflow."""


def canonical_json(value: Any) -> str:
    """Serialize JSON in a stable form for reproducible output and tests."""

    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _validate_id(value: str) -> str:
    value = value.strip()
    if not value:
        raise EvidencePackError("source IDs must not be empty")
    if len(value) > MAX_ID_LENGTH:
        raise EvidencePackError(f"source ID exceeds {MAX_ID_LENGTH} characters: {value[:32]!r}")
    if any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in value):
        raise EvidencePackError(f"source ID contains whitespace/control characters: {value[:32]!r}")
    return value


def normalize_ids(values: Iterable[str]) -> list[str]:
    """Normalize, deduplicate, and sort a bounded set of public IDs."""

    unique: set[str] = set()
    for raw_value in values:
        value = _validate_id(raw_value)
        unique.add(value)
    if not unique:
        raise EvidencePackError("provide at least one public source ID")
    if len(unique) > MAX_IDS:
        raise EvidencePackError(f"at most {MAX_IDS} unique source IDs are allowed per run")
    return sorted(unique)


def read_ids_file(path: str | Path) -> list[str]:
    """Read one public source ID per line; blank lines and # comments are ignored."""

    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise EvidencePackError(f"could not read IDs file {path!s}: {exc}") from exc
    values: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            values.append(_validate_id(stripped))
        except EvidencePackError as exc:
            raise EvidencePackError(f"IDs file line {line_number}: {exc}") from exc
    return values


def validate_endpoint(endpoint: str) -> str:
    """Allow the Base2026 endpoint and loopback stubs used for local testing."""

    normalized = endpoint.rstrip("/")
    parsed = urlparse(normalized)
    is_public = (
        parsed.scheme == "https"
        and parsed.hostname == "base2026.dev"
        and parsed.path == "/api/mcp"
        and not parsed.query
        and not parsed.fragment
    )
    is_loopback = (
        parsed.scheme == "http"
        and parsed.hostname in {"localhost", "127.0.0.1"}
        and parsed.path
        and not parsed.query
        and not parsed.fragment
    )
    if not (is_public or is_loopback):
        raise EvidencePackError(
            "endpoint must be https://base2026.dev/api/mcp "
            "(or an http://localhost/127.0.0.1 stub for tests)"
        )
    return normalized


def _bounded_response_body(response: Any) -> bytes:
    body = response.read(MAX_BODY_BYTES + 1)
    if len(body) > MAX_BODY_BYTES:
        raise EvidencePackError(f"MCP response exceeds the {MAX_BODY_BYTES}-byte safety bound")
    return body


def _post_json(endpoint: str, message: dict[str, Any], timeout: float) -> dict[str, Any]:
    request_body = json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(request_body) > MAX_BODY_BYTES:
        raise EvidencePackError(f"MCP request exceeds the {MAX_BODY_BYTES}-byte safety bound")
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
        "Mcp-Method": str(message["method"]),
        "User-Agent": "Base2026-Public-Evidence-Pack/1.0 (+https://base2026.dev/dataset)",
    }
    params = message.get("params")
    if isinstance(params, dict) and isinstance(params.get("name"), str):
        headers["Mcp-Name"] = params["name"]
    request = Request(endpoint, data=request_body, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            body = _bounded_response_body(response)
    except HTTPError as exc:
        detail = exc.read(512).decode("utf-8", errors="replace").replace("\n", " ")
        suffix = f": {detail[:180]}" if detail else ""
        if exc.code == 429:
            raise EvidencePackError("public MCP rate limit returned HTTP 429; retry after the server's Retry-After window") from exc
        raise EvidencePackError(f"public MCP returned HTTP {exc.code}{suffix}") from exc
    except URLError as exc:
        raise EvidencePackError(f"could not reach public MCP: {exc.reason}") from exc
    except TimeoutError as exc:
        raise EvidencePackError("public MCP request timed out") from exc
    if status < 200 or status >= 300:
        raise EvidencePackError(f"public MCP returned HTTP {status}")
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidencePackError("public MCP returned a non-JSON response") from exc
    if not isinstance(payload, dict):
        raise EvidencePackError("public MCP response is not a JSON object")
    return payload


def _mcp_request(
    endpoint: str,
    method: str,
    request_id: str,
    params: dict[str, Any] | None = None,
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    request_params = dict(params or {})
    request_params["_meta"] = {
        "io.modelcontextprotocol/protocolVersion": MCP_PROTOCOL_VERSION,
    }
    payload = _post_json(
        endpoint,
        {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": request_params,
        },
        timeout,
    )
    if payload.get("jsonrpc") != "2.0":
        raise EvidencePackError("public MCP response is not JSON-RPC 2.0")
    if payload.get("id") != request_id:
        raise EvidencePackError("public MCP response ID does not match the request")
    if isinstance(payload.get("error"), dict):
        error = payload["error"]
        code = error.get("code", "unknown")
        message = error.get("message", "request failed")
        raise EvidencePackError(f"public MCP JSON-RPC error {code}: {message}")
    result = payload.get("result")
    if not isinstance(result, dict):
        raise EvidencePackError("public MCP response has no result object")
    return result


def discover(endpoint: str, *, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> dict[str, str]:
    """Verify the modern stateless public MCP contract before fetching records."""

    result = _mcp_request(endpoint, "server/discover", "discover", timeout=timeout)
    if result.get("resultType") != "complete":
        raise EvidencePackError("public MCP discovery did not complete")
    capabilities = result.get("capabilities")
    if not isinstance(capabilities, dict) or not isinstance(capabilities.get("tools"), dict):
        raise EvidencePackError("public MCP discovery did not advertise tools")
    supported = result.get("supportedVersions")
    if not isinstance(supported, list) or MCP_PROTOCOL_VERSION not in supported:
        raise EvidencePackError(f"public MCP does not advertise protocol {MCP_PROTOCOL_VERSION}")
    server_info: dict[str, Any] = {}
    metadata = result.get("_meta")
    if isinstance(metadata, dict) and isinstance(metadata.get("io.modelcontextprotocol/serverInfo"), dict):
        server_info = metadata["io.modelcontextprotocol/serverInfo"]
    return {
        "protocol": MCP_PROTOCOL_VERSION,
        "server": str(server_info.get("name") or "base2026-public-mcp"),
        "server_version": str(server_info.get("version") or "unknown"),
    }


def _structured_content(result: dict[str, Any]) -> dict[str, Any]:
    if result.get("resultType") != "complete":
        raise EvidencePackError("public MCP get_source result did not complete")
    if result.get("isError") is True:
        raise EvidencePackError("public MCP get_source returned a tool error")
    structured = result.get("structuredContent")
    if isinstance(structured, dict):
        return structured
    content = result.get("content")
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
                try:
                    fallback = json.loads(item["text"])
                except json.JSONDecodeError:
                    continue
                if isinstance(fallback, dict):
                    return fallback
    raise EvidencePackError("public MCP get_source returned no structured public record")


def _walk_forbidden_keys(value: Any, path: str = "payload") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            key_lower = str(key).lower()
            if key_lower == "public_boundary":
                if child != PUBLIC_BOUNDARY:
                    raise EvidencePackError(f"public MCP payload has a drifted public boundary at {path}.{key}")
                continue
            if key_lower in FORBIDDEN_KEYS:
                raise EvidencePackError(f"public MCP payload contains forbidden field {path}.{key}")
            if key_lower.startswith("private_") or key_lower.endswith("_token"):
                raise EvidencePackError(f"public MCP payload contains forbidden field {path}.{key}")
            _walk_forbidden_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_forbidden_keys(child, f"{path}[{index}]")


def validate_public_record(payload: dict[str, Any]) -> dict[str, Any]:
    """Fail closed if a response is outside the documented public boundary."""

    boundary = payload.get("public_boundary")
    if not isinstance(boundary, dict) or boundary != PUBLIC_BOUNDARY:
        raise EvidencePackError("public MCP payload did not prove the public read-only boundary")
    _walk_forbidden_keys(payload)
    if payload.get("schema") != "base2026.mcp.get_source.v1":
        raise EvidencePackError("public MCP payload is not a get_source v1 record")
    if not isinstance(payload.get("found"), bool):
        raise EvidencePackError("public MCP get_source payload has no boolean found field")
    return payload


def fetch_source(
    endpoint: str,
    source_id: str,
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    result = _mcp_request(
        endpoint,
        "tools/call",
        f"source-{source_id}",
        {
            "name": "get_source",
            "arguments": {"source_id": source_id},
        },
        timeout=timeout,
    )
    return validate_public_record(_structured_content(result))


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def record_unknowns(payload: dict[str, Any]) -> list[str]:
    """Name fields not returned by the bounded public response.

    These labels deliberately describe the response shape.  They do not claim
    that the underlying source has no such data.
    """

    if payload.get("found") is False:
        return ["record_not_found"]
    unknowns: list[str] = []
    if not _nonempty_string(payload.get("source_url")):
        unknowns.append("original_source_url_not_returned")
    if not _nonempty_string(payload.get("source_page_url")):
        unknowns.append("base2026_source_page_not_returned")
    creator = payload.get("creator")
    if not isinstance(creator, dict) or not _nonempty_string(creator.get("handle")):
        unknowns.append("creator_handle_not_returned")
    if not _nonempty_string(payload.get("published_date")):
        unknowns.append("published_date_not_returned")
    if not isinstance(payload.get("topics"), list) or not payload["topics"]:
        unknowns.append("topics_not_returned")
    if not isinstance(payload.get("passages"), list) or not payload["passages"]:
        unknowns.append("public_passages_not_returned")
    if not isinstance(payload.get("applied_projection_cards"), list) or not payload["applied_projection_cards"]:
        unknowns.append("applied_evidence_cards_not_returned")
    return unknowns


def build_record(requested_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "requested_id": requested_id,
        "found": bool(payload.get("found")),
        "public_record": payload,
        "unknowns": record_unknowns(payload),
    }


def build_note(
    source_ids: Iterable[str],
    records: Iterable[dict[str, Any]],
    discovery: dict[str, str],
    *,
    endpoint: str = DEFAULT_ENDPOINT,
) -> dict[str, Any]:
    ids = normalize_ids(source_ids)
    sorted_records = sorted(records, key=lambda item: str(item.get("requested_id", "")))
    if [item.get("requested_id") for item in sorted_records] != ids:
        raise EvidencePackError("every normalized source ID must have exactly one fetched record")
    found_count = sum(1 for item in sorted_records if item.get("found") is True)
    missing_ids = [item["requested_id"] for item in sorted_records if item.get("found") is not True]
    field_gaps = [
        {
            "requested_id": item["requested_id"],
            "unknowns": item.get("unknowns", []),
        }
        for item in sorted_records
        if item.get("unknowns")
    ]
    return {
        "schema": "base2026.public-evidence-pack.v1",
        "endpoint": endpoint,
        "transport": discovery,
        "request": {
            "source_ids": ids,
            "unique_id_count": len(ids),
            "max_ids_per_run": MAX_IDS,
        },
        "summary": {
            "requested_count": len(ids),
            "found_count": found_count,
            "not_found_count": len(missing_ids),
            "records_with_unknowns": len(field_gaps),
        },
        "records": sorted_records,
        "unknowns": {
            "not_found_ids": missing_ids,
            "field_gaps": field_gaps,
        },
        "public_boundary": PUBLIC_BOUNDARY,
        "limitations": LIMITATIONS,
    }


def collect_note(
    endpoint: str,
    source_ids: Iterable[str],
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    endpoint = validate_endpoint(endpoint)
    ids = normalize_ids(source_ids)
    discovery = discover(endpoint, timeout=timeout)
    records = [build_record(source_id, fetch_source(endpoint, source_id, timeout=timeout)) for source_id in ids]
    return build_note(ids, records, discovery, endpoint=endpoint)


def _md_text(value: Any, fallback: str = "not returned") -> str:
    if not isinstance(value, str) or not value:
        return fallback
    text = value.replace("\n", " ").strip()
    for character in ("\\", "`", "*", "_", "[", "]", "<", ">"):
        text = text.replace(character, f"\\{character}")
    return text


def _md_link(label: Any, url: Any) -> str:
    if not isinstance(url, str) or not re.match(r"^https://[^\s<>]+$", url):
        return "not returned"
    safe_label = _md_text(label, "source")
    safe_url = url.replace(">", "%3E")
    return f"[{safe_label}](<{safe_url}>)"


def _md_quote(value: Any) -> list[str]:
    text = value if isinstance(value, str) and value else "(empty excerpt)"
    return [f"> {line}" for line in text.splitlines()]


def render_markdown(note: dict[str, Any]) -> str:
    """Render the stable human-readable companion to the canonical JSON note."""

    request = note["request"]
    summary = note["summary"]
    lines = [
        "# Base2026 public evidence note",
        "",
        "This note is a bounded, read-only retrieval from the public Base2026 MCP.",
        "It preserves returned source links and labels fields that the response did not return.",
        "",
        f"- Schema: `{note['schema']}`",
        f"- Endpoint: `{note['endpoint']}`",
        f"- Protocol: `{note['transport']['protocol']}` ({note['transport']['server']})",
        f"- Requested IDs: {request['unique_id_count']} of the per-run maximum {request['max_ids_per_run']}",
        f"- Results: {summary['found_count']} found; {summary['not_found_count']} not found",
        "",
        "## Public boundary",
        "",
        "The MCP response proves `public_read_only`; no login, key, upload, or write operation is used.",
        "Raw captions, raw ASR, media, private records, credentials, and publication controls are outside this note.",
        "",
        "## Records",
        "",
    ]
    for index, item in enumerate(note["records"], start=1):
        requested_id = item["requested_id"]
        payload = item["public_record"]
        lines.extend([f"### {index}. `{requested_id}`", ""])
        if payload.get("found") is not True:
            lines.extend([
                "- Status: not found by the public `get_source` lookup.",
                "- Unknowns: `record_not_found`.",
                "",
            ])
            continue
        creator = payload.get("creator") if isinstance(payload.get("creator"), dict) else {}
        lines.extend([
            "- Status: found",
            f"- Source ID: `{_md_text(payload.get('source_id'))}`",
            f"- Platform: `{_md_text(payload.get('platform'))}`",
            f"- Title: {_md_text(payload.get('title'))}",
            f"- Creator: {_md_text(creator.get('handle'))}",
            f"- Published: {_md_text(payload.get('published_date'))}",
            f"- Original source: {_md_link('open original source', payload.get('source_url'))}",
            f"- Base2026 source page: {_md_link('open Base2026 record', payload.get('source_page_url'))}",
            "",
            "#### Topics returned",
            "",
        ])
        topics = payload.get("topics") if isinstance(payload.get("topics"), list) else []
        if topics:
            for topic in topics:
                if isinstance(topic, dict):
                    lines.append(f"- `{_md_text(topic.get('id'))}` — {_md_text(topic.get('label'))}")
        else:
            lines.append("- None returned by this bounded response.")
        lines.extend(["", "#### Public passage excerpts", ""])
        passages = payload.get("passages") if isinstance(payload.get("passages"), list) else []
        if passages:
            for passage in passages:
                if not isinstance(passage, dict):
                    continue
                passage_id = _md_text(passage.get("id"), "unknown passage")
                lines.extend([f"- `{passage_id}` (chunk {passage.get('chunk_index', 'unknown')}):", *_md_quote(passage.get("excerpt")), ""])
        else:
            lines.append("- None returned by this bounded response.")
            lines.append("")
        lines.extend(["#### Applied public evidence cards", ""])
        cards = payload.get("applied_projection_cards") if isinstance(payload.get("applied_projection_cards"), list) else []
        if cards:
            for card in cards:
                if not isinstance(card, dict):
                    continue
                lines.extend([
                    f"- Card {card.get('ordinal', 'unknown')} — **{_md_text(card.get('claim'))}**",
                    f"  - Topic: {_md_text(card.get('topic'))}",
                    f"  - Suggested action: {_md_text(card.get('suggested_action'))}",
                    "  - Evidence excerpt:",
                    *_md_quote(card.get("evidence_excerpt")),
                ])
        else:
            lines.append("- None returned by this bounded response.")
        lines.extend(["", "#### Unknowns", ""])
        unknowns = item.get("unknowns") or []
        if unknowns:
            lines.extend([f"- `{unknown}`" for unknown in unknowns])
        else:
            lines.append("- No field gaps recorded in this response.")
        lines.append("")
    lines.extend(["## Limitations", "", *[f"- {limitation}" for limitation in note["limitations"]], ""])
    return "\n".join(lines)


def write_outputs(note: dict[str, Any], output_stem: str | Path) -> tuple[Path, Path]:
    stem = Path(output_stem)
    if stem.suffix.lower() in {".json", ".md"}:
        stem = stem.with_suffix("")
    stem.parent.mkdir(parents=True, exist_ok=True)
    json_path = stem.parent / f"{stem.name}.json"
    markdown_path = stem.parent / f"{stem.name}.md"
    json_path.write_text(canonical_json(note), encoding="utf-8")
    markdown_path.write_text(render_markdown(note), encoding="utf-8")
    return json_path, markdown_path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch up to eight public Base2026 source IDs and emit deterministic Markdown and JSON evidence notes."
    )
    parser.add_argument("source_ids", nargs="*", help="public source_id, item_id, video_id, or post_id")
    parser.add_argument("--ids-file", help="text file with one public ID per line; # comments are ignored")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help=argparse.SUPPRESS)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS, help="per-request timeout in seconds (1-60; default: 30)")
    parser.add_argument("--output", default="base2026-evidence-note", metavar="PATH", help="output filename stem (default: base2026-evidence-note)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if not 1 <= args.timeout <= 60:
        parser.error("--timeout must be between 1 and 60 seconds")
    values = list(args.source_ids)
    if args.ids_file:
        try:
            values.extend(read_ids_file(args.ids_file))
        except EvidencePackError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    try:
        ids = normalize_ids(values)
        note = collect_note(args.endpoint, ids, timeout=args.timeout)
        json_path, markdown_path = write_outputs(note, args.output)
    except (EvidencePackError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {json_path}")
    print(f"Wrote {markdown_path}")
    print(
        f"Fetched {note['summary']['found_count']}/{note['summary']['requested_count']} records; "
        f"{note['summary']['not_found_count']} not found; output is bounded and read-only."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
