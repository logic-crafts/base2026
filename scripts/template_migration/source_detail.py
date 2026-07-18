"""Typed Source Detail V2 adapter and Jinja renderer.

The adapter is intentionally strict: an isolated full-family candidate is allowed
only when the legacy page agrees with the admission state frozen in the route
manifest.  Missing or structurally unexpected evidence must fail the build,
never turn into plausible fallback copy.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag
from pydantic import BaseModel, ConfigDict, Field

from alex_v4_static_shell import footer_html, header_html
from base2026_ui_system import SYSTEM_VERSION as B26_SYSTEM_VERSION
from base2026_ui_system import stylesheet_tags as b26_stylesheet_tags
from .jinja_env import environment

AdmissionState = Literal[
    "normal_public_card",
    "provenance_archive_noindex",
    "future_private_backlog",
]


class SourceQuestion(BaseModel):
    model_config = ConfigDict(frozen=True)
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)


class SourceTopic(BaseModel):
    model_config = ConfigDict(frozen=True)
    label: str = Field(min_length=1)
    href: str = Field(min_length=1)


class SourceInsight(BaseModel):
    model_config = ConfigDict(frozen=True)
    claim: str = Field(min_length=1)
    meta: str = Field(min_length=1)
    actions: tuple[str, ...] = Field(min_length=1)
    topics: tuple[SourceTopic, ...] = Field(min_length=1)


class SourceSolution(BaseModel):
    model_config = ConfigDict(frozen=True)
    solution_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str = Field(min_length=1)
    href: str = Field(pattern=r"^/knowledge/solutions/[a-z0-9-]+\.html$")
    why_relevant: str = Field(min_length=1)


class SourceDetailView(BaseModel):
    """Normalized typed view-model. Templates never read raw legacy DOM."""

    model_config = ConfigDict(frozen=True)
    route: str
    item_id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)+$")
    admission_state: AdmissionState
    language_code: str = Field(min_length=1)
    head_html: str
    header_html: str
    footer_html: str
    handle: str = Field(min_length=1)
    date: str = Field(min_length=1)
    avatar_src: str
    avatar_alt: str
    thesis: str = Field(min_length=1)
    original_link: str = Field(min_length=1)
    creator_link: str
    search_link: str
    platform_key: str = Field(min_length=1)
    platform_label: str = Field(min_length=1)
    policy: str = Field(min_length=1)
    language: str = Field(min_length=1)
    insight_count: str
    topics: tuple[SourceTopic, ...]
    source_html: str = Field(min_length=1)
    insights: tuple[SourceInsight, ...]
    questions: tuple[SourceQuestion, ...]
    solutions: tuple[SourceSolution, ...]
    archive: bool
    schema_html: str


def _text(node: object | None) -> str:
    return node.get_text(" ", strip=True) if isinstance(node, Tag) else ""


def _inner(node: object | None) -> str:
    return "".join(str(child) for child in node.contents) if isinstance(node, Tag) else ""


def _platform(url: str) -> tuple[str, str]:
    host = urlparse(url).netloc.lower()
    if "tiktok" in host:
        return "tiktok", "TikTok"
    if "instagram" in host:
        return "instagram", "Instagram"
    if "youtube" in host or "youtu.be" in host:
        return "youtube", "YouTube"
    return "external", "Original source"


def _required(node: Any, field: str) -> Tag:
    if not isinstance(node, Tag):
        raise ValueError(f"Source Detail adapter requires {field}")
    return node


def _required_text(node: object | None, field: str) -> str:
    text = _text(_required(node, field))
    if not text:
        raise ValueError(f"Source Detail adapter requires non-empty {field}")
    return text


def _action_href(actions: list[Tag], label: str, *, contains: bool = False) -> str:
    for action in actions:
        text = _text(action).lower()
        if (label in text) if contains else (text == label):
            href = str(action.get("href") or "")
            if href:
                return href
    return ""


def _admission_from_robots(soup: BeautifulSoup) -> AdmissionState:
    robots = _required(soup.select_one('meta[name="robots"]'), 'meta[name="robots"]')
    content = str(robots.get("content") or "").lower().replace(" ", "")
    if "noindex" in content:
        return "provenance_archive_noindex"
    if "index" in content:
        return "normal_public_card"
    raise ValueError(f"Source Detail adapter cannot classify robots={content!r}")


def _source_intelligence(soup: BeautifulSoup) -> Tag | None:
    return next(
        (
            section
            for section in soup.select("main > section.content-section")
            if _text(section.select_one("h2")) == "Source Intelligence"
        ),
        None,
    )


def _extract_topics(nodes: list[Tag], field: str) -> tuple[SourceTopic, ...]:
    topics: list[SourceTopic] = []
    for node in nodes:
        label = _required_text(node, f"{field} label")
        href = str(node.get("href") or "")
        if not href:
            raise ValueError(f"Source Detail adapter requires {field} href")
        topics.append(SourceTopic(label=label, href=href))
    return tuple(topics)


def adapt_source_detail(
    source: Path,
    route: str,
    expected_admission_state: AdmissionState | None = None,
    solutions: tuple[SourceSolution, ...] = (),
) -> SourceDetailView:
    """Parse one frozen legacy source route into the strict V2 view-model.

    Full-family callers must pass ``expected_admission_state`` from the frozen
    manifest.  The optional inference keeps the existing two-page local canary
    backwards-compatible; it is not used by the full candidate renderer.
    """
    soup = BeautifulSoup(source.read_text(encoding="utf-8"), "html.parser")
    observed_admission = _admission_from_robots(soup)
    item_id = Path(route).stem
    admission = expected_admission_state or observed_admission
    if admission == "future_private_backlog":
        raise ValueError(f"Future route {route} must never be adapted or rendered")
    if observed_admission != admission:
        raise ValueError(
            f"Admission mismatch for {route}: manifest={admission}, robots={observed_admission}"
        )

    # The V2 renderer owns the complete visual surface.  Preserve metadata and
    # scripts from the frozen route, but never carry a previous visual cascade
    # into the new template.
    for visual_css in soup.select('link[rel~="stylesheet"]'):
        visual_css.decompose()
    for external_font in soup.select(
        'link[href*="fonts.googleapis.com"], link[href*="fonts.gstatic.com"]'
    ):
        external_font.decompose()

    hero = _required(soup.select_one(".source-page-hero"), ".source-page-hero")
    identity = _required(hero.select_one(".source-identity"), ".source-identity")
    handle = _required_text(identity.select_one("h1"), ".source-identity h1")
    avatar = identity.select_one("img")
    actions = list(hero.select(".hero-actions a"))
    original_link = _action_href(actions, "original", contains=True)
    if not original_link.startswith(("https://", "http://")):
        raise ValueError("Source Detail adapter requires a public original-source URL")
    creator_link = _action_href(actions, "creator")
    search_link = _action_href(actions, "search", contains=True)
    platform_key, platform_label = _platform(original_link)
    topics = _extract_topics(list(hero.select(".source-hero-topic-tags a")), "hero topic")
    intelligence = _source_intelligence(soup)
    questions = tuple(
        SourceQuestion(
            question=_required_text(card.select_one("h3"), "question title"),
            answer=_required_text(card.select_one("p"), "question answer"),
        )
        for card in soup.select(".evidence-qa-card")
    )
    source_text = _required(soup.select_one(".source-full-text"), ".source-full-text")
    language_code = str((soup.html or {}).get("lang") or "").strip()
    if not language_code:
        raise ValueError("Source Detail adapter requires <html lang>")

    insights: tuple[SourceInsight, ...] = ()
    if intelligence:
        collected: list[SourceInsight] = []
        for card in intelligence.select(".intelligence-card.source-detail-insight"):
            claim = _required_text(card.select_one("h3"), "Source Intelligence claim")
            meta = _required_text(card.select_one(".meta"), "Source Intelligence meta")
            action_items = tuple(_required_text(item, "Source Intelligence action") for item in card.select("li"))
            if not action_items:
                raise ValueError("Source Detail adapter requires Source Intelligence actions")
            insight_topics = _extract_topics(list(card.select(".source-detail-topic-links a")), "Source Intelligence topic")
            if not insight_topics:
                raise ValueError("Source Detail adapter requires Source Intelligence topics")
            collected.append(
                SourceInsight(claim=claim, meta=meta, actions=action_items, topics=insight_topics)
            )
        if not collected:
            raise ValueError("Source Detail adapter found an empty Source Intelligence section")
        insights = tuple(collected)

    date = _required_text(identity.select_one(".source-identity__date"), "source publication date")
    policy = _required_text(hero.select_one('[title="Public policy"]'), "public policy")
    language = _required_text(hero.select_one('[title="Language"]'), "language")
    insight_node = hero.select_one('[title="Public insight cards"] strong')
    insight_count = _text(insight_node)

    if admission == "normal_public_card":
        if not creator_link or not search_link:
            raise ValueError("Normal Source Detail requires creator and Search Workspace actions")
        if not insights or not questions:
            raise ValueError("Normal Source Detail requires intelligence and questions")
        if not insight_count:
            raise ValueError("Normal Source Detail requires public insight count")
    else:
        if creator_link or search_link:
            raise ValueError("Archive Source Detail must not expose creator or Search Workspace actions")
        if insights or questions or insight_count:
            raise ValueError("Archive Source Detail must not expose public intelligence surfaces")

    return SourceDetailView(
        route=route,
        item_id=item_id,
        admission_state=admission,
        language_code=language_code,
        head_html=_inner(_required(soup.head, "<head>")),
        header_html=header_html(),
        footer_html=footer_html(),
        handle=handle,
        date=date,
        avatar_src=str(avatar.get("src") or "") if isinstance(avatar, Tag) else "",
        avatar_alt=str(avatar.get("alt") or "") if isinstance(avatar, Tag) else "",
        thesis=_required_text(hero.select_one(".lead"), "source thesis"),
        original_link=original_link,
        creator_link=creator_link,
        search_link=search_link,
        platform_key=platform_key,
        platform_label=platform_label,
        policy=policy,
        language=language,
        insight_count=insight_count,
        topics=topics,
        source_html=_inner(source_text),
        insights=insights,
        questions=questions,
        solutions=solutions if admission == "normal_public_card" else (),
        archive=admission == "provenance_archive_noindex",
        schema_html="".join(str(script) for script in soup.select('main script[type="application/ld+json"]')),
    )


def render_source_detail(view: SourceDetailView, renderer_version: str) -> str:
    return environment().get_template("families/source_detail.html.j2").render(
        view=view,
        renderer_version=renderer_version,
        b26_system_version=B26_SYSTEM_VERSION,
        b26_stylesheet_tags=b26_stylesheet_tags(".."),
    )
