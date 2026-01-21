from pathlib import Path

def test_no_innerhtml_usage() -> None:
    files = [
        Path('alpha_factory_v1/demos/alpha_agi_insight_v1/insight_browser_v1/src/ui/EvolutionPanel.ts'),
        Path('alpha_factory_v1/demos/alpha_agi_insight_v1/insight_browser_v1/src/ui/ControlsPanel.ts'),
    ]
    for f in files:
        text = f.read_text()
        assert '.innerHTML' not in text

