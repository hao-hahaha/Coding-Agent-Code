import pathlib


BASE = pathlib.Path("alpha_factory_v1/demos/alpha_agi_insight_v1/insight_browser_v1")


def _assert_no_placeholder(path: pathlib.Path) -> None:
    data = path.read_text(errors="ignore")
    assert "placeholder" not in data.lower()


def test_assets_replaced() -> None:
    _assert_no_placeholder(BASE / "lib" / "workbox-sw.js")
    _assert_no_placeholder(BASE / "lib" / "bundle.esm.min.js")
    _assert_no_placeholder(BASE / "dist" / "workbox-sw.js")
    _assert_no_placeholder(BASE / "dist" / "bundle.esm.min.js")
