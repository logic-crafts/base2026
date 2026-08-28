from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "generate-info-pages.py"
SPEC = importlib.util.spec_from_file_location("generate_info_pages", MODULE_PATH)
assert SPEC and SPEC.loader
generator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = generator
SPEC.loader.exec_module(generator)


def test_render_markdown_keeps_wrapped_list_items_in_order() -> None:
    markdown = """# Page

## Features

- First item wraps onto
  its second line.
- Second item.

After the list.
"""

    _h1, rendered = generator.render_markdown(markdown, "doc-page")

    assert "<li>First item wraps onto its second line.</li>" in rendered
    assert rendered.index("<ul>") < rendered.index("After the list.")


def test_render_markdown_preserves_ordered_lists_and_fenced_code() -> None:
    markdown = """# Page

## Workflow

1. Discover.
2. Verify.

```json
{"ok": true}
```
"""

    _h1, rendered = generator.render_markdown(markdown, "doc-page")

    assert "<ol><li>Discover.</li><li>Verify.</li></ol>" in rendered
    assert '<pre><code class="language-json">{&quot;ok&quot;: true}</code></pre>' in rendered
