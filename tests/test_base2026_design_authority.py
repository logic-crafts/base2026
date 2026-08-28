from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = spec_from_file_location(
    "base2026_design_authority",
    ROOT / "scripts" / "check-base2026-design-authority.py",
)
assert SPEC and SPEC.loader
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_canonical_design_authority_has_no_active_regression() -> None:
    assert MODULE.check() == []
