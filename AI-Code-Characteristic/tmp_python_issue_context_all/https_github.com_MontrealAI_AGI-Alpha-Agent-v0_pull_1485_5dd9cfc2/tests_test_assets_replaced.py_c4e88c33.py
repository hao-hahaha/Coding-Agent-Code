import pathlib


def test_workbox_replaced():
    path = pathlib.Path("alpha_factory_v1/demos/alpha_agi_insight_v1/insight_browser_v1/lib/workbox-sw.js")
    data = path.read_text(errors="ignore")
    assert "Placeholder" not in data
