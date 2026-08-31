from pathlib import Path

from scripts.generate_previews import DETAIL_FILES, VIEW_FILES, generate_previews
from scripts.generate_wing import generate as generate_wing


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "aircraft.yaml"


def test_preview_generation_is_disposable_and_contains_current_drawings(tmp_path: Path):
    generated = tmp_path / "generated"
    generate_wing(CONFIG, generated)
    previews = generated / "previews"
    paths = generate_previews(generated, previews)

    assert set(VIEW_FILES).issubset(paths)
    assert paths["index"].name == "index.html"
    assert all(path.is_file() and path.stat().st_size > 0 for path in paths.values())
    index = paths["index"].read_text(encoding="utf-8")
    for filename in [*VIEW_FILES.values(), *DETAIL_FILES.values()]:
        assert filename in index
    for filename in DETAIL_FILES.values():
        assert (previews / filename).read_bytes() == (generated / filename).read_bytes()


def test_preview_code_has_no_aircraft_parameter_or_snapshot_input():
    source = (ROOT / "scripts" / "generate_previews.py").read_text(encoding="utf-8")
    assert "load_aircraft_config" not in source
    assert "parameters.json" not in source
