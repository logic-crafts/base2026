from __future__ import annotations

import sys
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from template_migration.source_detail import adapt_source_detail, render_source_detail  # noqa: E402


def test_adapter_removes_legacy_owned_runtime_before_strict_render(tmp_path: Path) -> None:
    source = tmp_path / "sources/tiktok-video-fixture.html"
    source.parent.mkdir(parents=True)
    source.write_text(
        """<!doctype html><html lang="en"><head>
        <meta name="robots" content="index,follow"><title>Fixture</title>
        <script defer src="../static/alex-v4-static-shell.js?v=legacy"></script>
        </head><body><main>
        <section class="source-page-hero">
          <div class="source-identity"><h1>@fixture</h1><span class="source-identity__date">2026-07-18</span></div>
          <p class="lead">Reviewed fixture thesis.</p>
          <div class="hero-actions">
            <a href="../?source=tiktok-video-fixture">Open in Search</a>
            <a href="https://www.tiktok.com/@fixture/video/1">Open original TikTok</a>
            <a href="../creators/fixture.html">Creator</a>
          </div>
          <span title="Public policy">excerpt only</span>
          <span title="Language">en</span>
          <span title="Public insight cards"><strong>1</strong></span>
        </section>
        <div class="source-full-text"><p>Reviewed public source text.</p></div>
        <section class="content-section"><h2>Source Intelligence</h2>
          <article class="intelligence-card source-detail-insight">
            <h3>Bounded reviewed claim.</h3><p class="meta">Fixture topic</p>
            <ul><li>Use the bounded action.</li></ul>
            <div class="source-detail-topic-links"><a href="../topics/fixture.html">Fixture</a></div>
          </article>
        </section>
        <article class="evidence-qa-card"><h3>What is supported?</h3><p>The reviewed fixture.</p></article>
        </main></body></html>""",
        encoding="utf-8",
    )

    view = adapt_source_detail(
        source,
        "sources/tiktok-video-fixture.html",
        "normal_public_card",
    )
    rendered = BeautifulSoup(render_source_detail(view, "fixture-renderer"), "html.parser")

    shell_scripts = rendered.select('script[src*="alex-v4-static-shell.js"]')
    assert len(shell_scripts) == 1
    assert shell_scripts[0].get("src") == "../static/alex-v4-static-shell.js?v=fixture-renderer"
