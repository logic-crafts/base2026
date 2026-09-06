from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "base2026_topic_discovery.py"
SPEC = importlib.util.spec_from_file_location("base2026_topic_discovery", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _card(title: str, insights: str, sources: str, slug: str, description: str | None = None) -> str:
    body = description or f"Public evidence about {title}."
    return f"""
      <article class="intelligence-card">
        <h3>{title}</h3>
        <p class="meta">{insights} public insights · {sources} sources</p>
        <p>{body}</p>
        <a class="button-link" href="{slug}">Open</a>
      </article>
    """


def _index(*cards: str) -> str:
    return """<!doctype html>
<html><head><title>Topics</title><link rel="canonical" href="https://base2026.dev/topics/">
<script type="application/ld+json">{"@type":"CollectionPage","url":"https://base2026.dev/topics/"}</script>
</head><body>
<header class="b26-site-header">Header stays.</header>
<main id="content" class="app-shell content-page"><section class="page-hero"><h1>Old topic heading</h1></section>
<section class="content-section"><div class="card-grid">""" + "".join(cards) + """</div></section></main>
<footer class="b26-site-footer">Footer stays.</footer>
</body></html>"""


def test_extracts_exact_counts_and_canonical_routes_from_existing_card_shape() -> None:
    source = _index(
        _card("Large topic", "163", "163", "large-topic"),
        _card("Two-source topic", "7", "2", "two-source-topic"),
        _card("Single topic", "1", "1", "single-topic"),
    )

    records = MODULE.extract_topic_records(source)
    assert records is not None
    assert [(record.title, record.route, record.insight_count, record.source_count) for record in records] == [
        ("Large topic", "/topics/large-topic", 163, 163),
        ("Two-source topic", "/topics/two-source-topic", 7, 2),
        ("Single topic", "/topics/single-topic", 1, 1),
    ]

    rendered = MODULE.render_topic_discovery(source)
    assert rendered.count('class="b26-site-header"') == 1
    assert rendered.count('class="b26-site-footer"') == 1
    assert 'href="https://base2026.dev/topics/"' in rendered
    assert 'type="application/ld+json"' in rendered
    assert rendered.count('class="b26-topic-card"') == 3
    assert rendered.count('class="b26-topic-collection"') == 3
    assert 'href="/topics/large-topic"' in rendered
    assert '163 public insights · 163 sources' in rendered
    assert '7 public insights · 2 sources' in rendered
    assert "Start with more sources" in rendered
    assert "Explore the topics with the widest source coverage." in rendered
    assert "Find a working area or narrow your research by source coverage." in rendered
    assert "The broadest existing topic records" not in rendered
    assert 'id="b26-topic-directory-title" tabindex="-1"' in rendered
    assert 'data-topic-search type="search" maxlength="160"' in rendered
    assert rendered.count('data-topic-controls') == 1
    assert rendered.index('data-topic-controls') < rendered.index('b26-topic-collections-title')
    assert 'Search topics' in rendered
    assert 'Multiple sources' in rendered and 'Single source' in rendered


def test_titles_and_descriptions_are_escaped_without_losing_search_text() -> None:
    source = _index(
        _card(
            "Signals &amp; &lt;script&gt;alert(1)&lt;/script&gt;",
            "2",
            "2",
            "safe-topic",
            "A description with &amp; and &lt;em&gt;markup&lt;/em&gt;.",
        )
    )
    rendered = MODULE.render_topic_discovery(source)

    assert "<script>alert(1)</script>" not in rendered
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in rendered
    assert 'data-topic-title="Signals &amp; &lt;script&gt;alert(1)&lt;/script&gt;"' in rendered
    assert 'data-topic-description="A description with &amp; and &lt;em&gt;markup&lt;/em&gt;."' in rendered
    assert "innerHTML" not in (ROOT / "templates" / "base2026-topic-discovery.js").read_text(encoding="utf-8")


def test_transformation_is_idempotent_and_preserves_only_the_shell() -> None:
    source = _index(_card("A topic", "2", "2", "a-topic"))
    once = MODULE.render_topic_discovery(source)
    twice = MODULE.render_topic_discovery(once)
    assert once == twice
    assert once.count("data-b26-topic-discovery") == 1
    assert once.count("<main") == 1
    assert once.count("</main>") == 1
    assert "Old topic heading" not in once
    assert "Header stays." in once and "Footer stays." in once


def test_malformed_or_unsafe_expected_source_fails_closed_without_partial_rewrite() -> None:
    missing_count = _index(
        """
        <article class="intelligence-card"><h3>Broken</h3><p class="meta">No count</p>
        <p>Cannot safely index.</p><a class="button-link" href="broken">Open</a></article>
        """
    )
    external_route = _index(_card("External", "2", "2", "https://evil.example/topic"))
    duplicate_routes = _index(_card("One", "2", "2", "same-topic"), _card("Two", "1", "1", "same-topic"))
    no_main = "<html><head><title>Topics</title></head><body><article class='intelligence-card'>x</article></body></html>"

    for malformed in (missing_count, external_route, duplicate_routes, no_main, ""):
        assert MODULE.render_topic_discovery(malformed) == malformed
        assert MODULE.extract_topic_records(malformed) is None


def test_real_source_lab_artifact_keeps_every_indexed_route_and_exact_leading_counts() -> None:
    # The generated artifact is optional local evidence and is intentionally
    # not a committed fixture.  When a release preview is present under this
    # checkout, validate the real public index as well.
    artifact = ROOT / "output" / "source-lab-20260906-v4" / "topics" / "index.html"
    if not artifact.exists():
        return
    source = artifact.read_text(encoding="utf-8")
    records = MODULE.extract_topic_records(source)
    assert records is not None and len(records) >= 80
    assert records[0].route == "/topics/ai-visibility-and-answer-readiness"
    assert (records[0].insight_count, records[0].source_count) == (163, 163)
    assert records[1].route == "/topics/seo-research-and-tooling-workflow"
    assert (records[1].insight_count, records[1].source_count) == (98, 98)
    assert len({record.route for record in records}) == len(records)
    rendered = MODULE.render_topic_discovery(source)
    assert rendered.count('class="b26-topic-card"') == len(records)
    assert MODULE.render_topic_discovery(rendered) == rendered
