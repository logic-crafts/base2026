from __future__ import annotations

import sys
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from alex_v4_static_shell import footer_html  # noqa: E402


def test_every_public_base_page_uses_the_global_personal_footer() -> None:
    expected = footer_html().strip()
    pages = sorted((ROOT / "web" / "static").rglob("*.html"))
    assert len(pages) >= 90

    for page in pages:
        markup = page.read_text(encoding="utf-8")
        soup = BeautifulSoup(markup, "html.parser")
        footers = soup.select('footer.ay-site-footer[data-footer-contract="personal-v1"]')
        assert len(footers) == 1, page.relative_to(ROOT)
        assert "b26-product-footer" not in markup, page.relative_to(ROOT)
        assert "Public evidence, with attribution." not in footers[0].get_text(" ", strip=True), page.relative_to(ROOT)
        assert str(footers[0]).strip() == str(BeautifulSoup(expected, "html.parser").footer).strip(), page.relative_to(ROOT)
